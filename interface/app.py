import gradio as gr
import time
from agents.support_agent import agent_support_fnac
from agents.analytics_agent import init_analytics_db, analytics_agent

# --- Initialisation ---
init_analytics_db()
support_agent, memory = agent_support_fnac()
conversation_start_time = None

# --- Fonctions de l'interface ---

def add_user_message(user_message, chat_history):
    """Affiche immédiatement le message de l'utilisateur et un indicateur de frappe."""
    global conversation_start_time
    if not chat_history:
        conversation_start_time = time.time()
    
    if user_message:
        chat_history.append((user_message, None))
    return "", chat_history

def get_agent_response(chat_history):
    """Génère la réponse de l'agent et met à jour le chatbot."""
    if not chat_history or chat_history[-1][1] is not None:
        return chat_history

    user_message = chat_history[-1][0]
    response = support_agent(user_message)
    chat_history[-1] = (user_message, response)
    return chat_history

def handle_end_conversation(chat_history):
    """Gère la fin de la conversation et lance l'analyse."""
    if not chat_history:
        return "Aucune conversation à analyser.", None

    duration = time.time() - conversation_start_time if conversation_start_time else 0
    
    # Reconstituer l'historique et les derniers messages
    full_history_text = "\n".join([f"Client: {u}\nAgent: {a}" for u, a in chat_history])
    last_user_message = chat_history[-1][0] if chat_history else ""
    last_agent_response = chat_history[-1][1] if chat_history else ""

    # Lancer l'analyse
    analysis_result = analytics_agent(
        user_message=last_user_message,
        agent_response=last_agent_response,
        chat_history=full_history_text,
        duration=duration
    )
    
    # Formater le rapport pour l'affichage
    report = f"""
    ## Rapport d'Analyse de la Conversation
    - **Thème :** {analysis_result.get('theme', 'N/A')}
    - **Score de Satisfaction :** {analysis_result.get('satisfaction_score', 'N/A'):.2f}
    - **Durée :** {duration:.2f} secondes
    - **Suggestion d'amélioration :** {analysis_result.get('improvement_suggestion') or 'Aucune'}
    """
    return report, None # Retourne le rapport et efface l'historique pour une nouvelle conversation

# --- Construction de l'interface Gradio ---

with gr.Blocks(theme=gr.themes.Soft(), title="Agent de Support Fnac") as app:
    gr.Markdown("# 🧠 Agent de Support Client Fnac")
    gr.Markdown("Discutez avec l'agent ci-dessous. Quand vous avez terminé, cliquez sur 'Terminer & Analyser'.")

    chatbot = gr.Chatbot(label="Conversation", height=500)
    msg_input = gr.Textbox(label="Votre message", placeholder="Posez votre question ici...")
    
    with gr.Row():
        send_button = gr.Button("Envoyer", variant="primary")
        end_button = gr.Button("Terminer & Analyser", variant="stop")

    analysis_report = gr.Markdown(label="Rapport d'Analyse")

    # Logique des événements en deux temps pour une meilleure réactivité
    msg_input.submit(add_user_message, [msg_input, chatbot], [msg_input, chatbot], queue=False).then(
        get_agent_response, chatbot, chatbot
    )
    send_button.click(add_user_message, [msg_input, chatbot], [msg_input, chatbot], queue=False).then(
        get_agent_response, chatbot, chatbot
    )
    end_button.click(handle_end_conversation, [chatbot], [analysis_report, chatbot])

if __name__ == "__main__":
    app.launch()
