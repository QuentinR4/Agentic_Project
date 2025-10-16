from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
import os
def agent_support_fnac():
    embedding = HuggingFaceEmbeddings(model_name="embaas/sentence-transformers-multilingual-e5-base")
    vectordb = Chroma(persist_directory="./vectorstore/chroma", embedding_function=embedding)
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3, api_key=os.getenv("GEMINI_API_KEY"))
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # 🔧 Ton prompt personnalisé
    template = """
    Tu es un agent de support client Fnac.
    Ta mission est d’aider les clients en te basant uniquement sur le CONTEXTE fourni ci-dessous.

    - Réponds toujours poliment et de façon claire.
    - Si tu ne sais pas, dis-le explicitement ("Je ne dispose pas de cette information.").
    - Si la question sort du domaine Fnac, indique-le gentiment.

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

    # 🧠 On injecte le prompt personnalisé
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        verbose=False
    )

    return qa_chain
