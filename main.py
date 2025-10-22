# main.py
import os
from agents.support_agent import agent_support_fnac, analyze_and_store_llm, init_db
import time

def main():
    print("🧠 Agent de support Fnac — conversation interactive\n")
    print("Tape 'exit' pour quitter.\n")
    
    # 🔹 Initialisation base
    init_db()
    
    # 🔹 Création de ton agent
    agent, memory = agent_support_fnac()

    # 🔹 Historique et timing
    conversation_start = time.time()
    all_user_messages = []
    all_agent_responses = []
    
    while True:
        question = input("👤 Client : ")
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 À bientôt !")
            break

        # 🔹 Appel de l'agent pour chaque message
        answer = agent(question)
        print(f"🤖 Support : {answer}\n")

        # 🔹 Sauvegarde locale pour analyse finale
        all_user_messages.append(question)
        all_agent_responses.append(answer)

    # 🔹 Analyse finale avec LLM
    conversation_end = time.time()
    total_duration = round(conversation_end - conversation_start, 2)

    # Historique complet en texte
    chat_history_text = "\n".join(
        [f"Client: {u}\nAgent: {a}" for u, a in zip(all_user_messages, all_agent_responses)]
    )

    # Dernier message + dernière réponse pour le LLM analytique
    final_user_message = all_user_messages[-1] if all_user_messages else ""
    final_agent_response = all_agent_responses[-1] if all_agent_responses else ""

    analyze_and_store_llm(final_user_message, final_agent_response, chat_history_text, total_duration)

if __name__ == "__main__":
    main()