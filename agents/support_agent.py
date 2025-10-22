from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.memory import ConversationSummaryMemory
import sqlite3, os, time, json, uuid


# ==========================
# Création de la base de données pour les analytics
# ==========================
def init_db():
    db_path = "data/analytics/analytics.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)  # crée le dossier si inexistant
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        intent TEXT,
        satisfaction_score REAL,
        chat_duration REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

# ==========================
# Analyse LLM avec historique
# ==========================
def analyze_and_store_llm(user_message: str, agent_response: str, chat_history: str, duration: float):
    chat_id = str(uuid.uuid4())

    llm_analyse = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        api_key=os.getenv("GEMINI_API_KEY")
    )

    # Prompt prenant en compte l'historique complet
    analyse_prompt = PromptTemplate(
        input_variables=["chat_history", "user_message", "agent_response"],
        template="""
    Tu es un analyste conversationnel expert pour le support client Fnac.
    Analyse cette conversation complète client-agent.

    Historique complet :
    {chat_history}

    Dernier message client :
    {user_message}

    Dernière réponse agent :
    {agent_response}

    Pour chaque conversation, fournis un JSON avec :

    1️⃣ theme : le thème principal de la conversation (ex: commande, retour, produit, paiement, assistance technique)
    2️⃣ satisfaction_score : un nombre entre 0 et 1 représentant la satisfaction globale du client
    3️⃣ remarque : un court résumé des points importants ou frustrations éventuelles
    
    
    - Tous les guillemets doubles " dans le texte doivent être échappés avec un backslash \"
    - Répond strictement en JSON sous ce format :

    {{
    "theme": "retour",
    "satisfaction_score": 0.8,
    "remarque": "Le client voulait retourner un produit, agent a répondu clairement"
    }}
    
    Ne pas utiliser de balises Markdown, renvoie uniquement le JSON pur.
    """
    )
    prompt_text = analyse_prompt.format(
        chat_history=chat_history,
        user_message=user_message,
        agent_response=agent_response
    )

    try:
        result = llm_analyse.invoke(prompt_text).content
        data = json.loads(result)
        intent = data.get("theme", "autre")
        satisfaction = float(data.get("satisfaction_score", 0.5))
        remarque = data.get("remarque", "")

    except Exception as e:
        intent = "autre"
        satisfaction = 0.5

    # Stockage minimal dans la base
    conn = sqlite3.connect("data/analytics/analytics.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_analytics (chat_id, intent, satisfaction_score, chat_duration)
        VALUES (?, ?, ?, ?)
    """, (chat_id, intent, satisfaction, duration))
    conn.commit()
    conn.close()
    
        
def agent_support_fnac():
    embedding = HuggingFaceEmbeddings(model_name="embaas/sentence-transformers-multilingual-e5-base")
    vectordb = Chroma(persist_directory="./vectorstore/chroma", embedding_function=embedding)
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3, api_key=os.getenv("GEMINI_API_KEY"))
    
    llm_summary = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, api_key=os.getenv("GEMINI_API_KEY"))
    memory = ConversationSummaryMemory(llm=llm_summary, memory_key="chat_history", return_messages=True)

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
        response = qa_chain.invoke({"question": query})
        # Essaye plusieurs clés possibles
        if isinstance(response, dict):
            answer = response.get("answer") or response.get("output_text") or str(response)
        else:
            answer = str(response)
        return answer

    return run_support, memory  # Retourne aussi la mémoire pour l'analyse finale