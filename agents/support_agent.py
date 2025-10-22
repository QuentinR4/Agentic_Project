from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.memory import ConversationSummaryMemory
import os
from agents.manager_agent import load_guidelines
    
        
def agent_support_fnac():
    embedding = HuggingFaceEmbeddings(model_name="embaas/sentence-transformers-multilingual-e5-base")
    vectordb = Chroma(persist_directory="./vectorstore/chroma", embedding_function=embedding)
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3, api_key=os.getenv("GEMINI_API_KEY"))
    
    llm_summary = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, api_key=os.getenv("GEMINI_API_KEY"))
    memory = ConversationSummaryMemory(llm=llm_summary, memory_key="chat_history", return_messages=True)

    # � Charger les guidelines d'amélioration
    guidelines = load_guidelines()
    guidelines_text = guidelines.get("summary", "Aucune guideline disponible")

    # 🔧 Ton prompt personnalisé
    template = """
    Tu es un agent de support client Fnac.

    - Ta mission : répondre uniquement à la QUESTION DU CLIENT en te basant uniquement sur le CONTEXTE fourni ci-dessous.
    - Réponds toujours poliment et de façon claire, avec les formules de courtoisie appropriées.
    - Si tu ne sais pas, dis-le explicitement ("Je ne dispose pas de cette information.").
    - Si la question sort du domaine Fnac, indique-le gentiment.
    - ⚠️ IMPORTANT : Si le client remercie, dit "ok", "d'accord", "merci", "au revoir" ou ferme la conversation, réponds UNIQUEMENT par une courte phrase de politesse (ex: "De rien ! N'hésitez pas si vous avez d'autres questions."). NE RÉPÈTE JAMAIS ta réponse précédente.
    - Ne redis pas "Bonjour" si tu l'as déjà fait dans l'HISTORIQUE.
    - Ne répète jamais exactement ce qui a déjà été dit dans l'historique.

    === CONTEXTE ===
    {context}

    === HISTORIQUE ===
    {chat_history}

    === QUESTION DU CLIENT ===
    {question}

    === RÉPONSE ===
    """
    prompt = PromptTemplate(
        input_variables=["context", "chat_history", "question"],
        template=template,
    )

    # 🔑 CRÉER LA CHAÎNE UNE SEULE FOIS (pas à chaque appel)
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        output_key="answer",
        verbose=False
    )
    
    # Fonction appelée pour chaque message
    def run_support(query: str):
        # Injecter les guidelines dans la question
        augmented_query = f"""Voici les directives d'amélioration à prendre en compte:
        {guidelines_text}

        Question originale du client:
        {query}
        """
        response = qa_chain.invoke({
            "question": augmented_query
        })
        # Essaye plusieurs clés possibles
        if isinstance(response, dict):
            answer = response.get("answer") or response.get("output_text") or str(response)
        else:
            answer = str(response)
        return answer

    return run_support, memory  # Retourne aussi la mémoire pour l'analyse finale