# agents/analytics_agent.py
import sqlite3
import os
import json
import uuid
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


# ==========================
# Création de la base de données pour les analytics
# ==========================
def init_analytics_db():
    """Initialise la base de données SQLite pour l'analytics."""
    db_path = "data/analytics/analytics.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier si la table existe déjà
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='chat_analytics'
    """)
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("✅ Base de données analytics déjà initialisée.")
    else:
        print("🔨 Création de la table chat_analytics...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            intent TEXT,
            satisfaction_score REAL,
            chat_duration REAL,
            improvement_suggestion TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        print("✅ Table chat_analytics créée avec succès.")
    
    conn.close()


# ==========================
# Analyse LLM avec historique
# ==========================
def analyze_conversation(
    user_message: str,
    agent_response: str,
    chat_history: str,
    duration: float
) -> dict:
    """
    Analyse une conversation complète avec le LLM.
    
    Args:
        user_message: Dernier message du client
        agent_response: Dernière réponse de l'agent
        chat_history: Historique complet de la conversation
        duration: Durée totale de la conversation
        
    Returns:
        dict: Contient chat_id, theme, satisfaction_score, remarque
    """
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
    4️⃣ improvement_suggestion : (OPTIONNEL - seulement si satisfaction_score < 0.6) UNE suggestion concrète pour améliorer la réponse
    
    - Tous les guillemets doubles " dans le texte doivent être échappés avec un backslash \"
    - Répond strictement en JSON sous ce format :

    {{
    "theme": "retour",
    "satisfaction_score": 0.8,
    "remarque": "Le client voulait retourner un produit, agent a répondu clairement",
    "improvement_suggestion": null
    }}
    
    ou si satisfaction < 0.6 :

    {{
    "theme": "retour",
    "satisfaction_score": 0.45,
    "remarque": "Le client était frustré par le manque de clarté",
    "improvement_suggestion": "Proposer des délais spécifiques au lieu de réponses vagues"
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
        improvement_suggestion = data.get("improvement_suggestion")  # Peut être None

    except Exception as e:
        print(f"⚠️ Erreur lors de l'analyse LLM: {e}")
        intent = "autre"
        satisfaction = 0.5
        remarque = ""
        improvement_suggestion = None

    return {
        "chat_id": chat_id,
        "theme": intent,
        "satisfaction_score": satisfaction,
        "remarque": remarque,
        "improvement_suggestion": improvement_suggestion,
        "duration": duration
    }


def store_analytics(analysis_result: dict) -> bool:
    """
    Stocke les résultats d'analyse dans la base de données.
    
    Args:
        analysis_result: Dict contenant les résultats de analyze_conversation()
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        conn = sqlite3.connect("data/analytics/analytics.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_analytics (chat_id, intent, satisfaction_score, chat_duration, improvement_suggestion)
            VALUES (?, ?, ?, ?, ?)
        """, (
            analysis_result["chat_id"],
            analysis_result["theme"],
            analysis_result["satisfaction_score"],
            analysis_result["duration"],
            analysis_result.get("improvement_suggestion")
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur lors du stockage en base: {e}")
        return False


def analytics_agent(
    user_message: str,
    agent_response: str,
    chat_history: str,
    duration: float
) -> dict:
    """
    Combine analyse + stockage en une seule fonction.
    Appelle le manager si satisfaction < 0.6 pour générer les guidelines d'amélioration.
    
    Args:
        user_message: Dernier message du client
        agent_response: Dernière réponse de l'agent
        chat_history: Historique complet
        duration: Durée de la conversation
        
    Returns:
        dict: Résultats d'analyse
    """
    from agents.manager_agent import manager_update
    
    analysis = analyze_conversation(user_message, agent_response, chat_history, duration)
    store_analytics(analysis)
    
    # Affichage
    msg = f"✅ Analyse stockée - Thème: {analysis['theme']}, Satisfaction: {analysis['satisfaction_score']}"
    if analysis.get("improvement_suggestion"):
        msg += f"\n💡 Suggestion: {analysis['improvement_suggestion']}"
    
    print(msg)
    
    # 🔄 Si satisfaction faible, appeler le manager pour mettre à jour les guidelines
    if analysis['satisfaction_score'] < 0.6:
        print("📞 Appel du Manager pour mise à jour des guidelines...")
        manager_update()
    
    return analysis
