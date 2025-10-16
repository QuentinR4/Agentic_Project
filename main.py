# main.py
import os
from agents.support_agent import agent_support_fnac


def main():
    print("🧠 Agent de support Fnac — conversation interactive\n")
    print("Tape 'exit' pour quitter.\n")
    # 🔹 Création de ton agent
    agent = agent_support_fnac()

    while True:
        question = input("👤 Client : ")
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 À bientôt !")
            break

        # 🔹 Envoi de la requête à l’agent
        response = agent.invoke({"question": question})

        # 🔹 Affiche la réponse
        print(f"🤖 Support : {response['answer']}\n")

if __name__ == "__main__":
    main()