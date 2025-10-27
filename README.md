# 🧠 Projet d'Agent Conversationnel Auto-Améliorant

Ce projet est une démonstration d'un système d'agent conversationnel (chatbot) avancé conçu pour le support client. Sa particularité est sa capacité à s'auto-améliorer en analysant ses propres conversations pour identifier des points faibles et générer des directives pour ses futures interactions.

## ✨ Fonctionnalités Clés

- **Interface de Chat Interactive** : Une interface web simple et réactive construite avec Gradio.
- **Analyse Post-Conversation** : Après chaque conversation, un agent spécialisé analyse l'échange pour en déterminer le thème et le score de satisfaction client.
- **Boucle d'Auto-Amélioration** : Si le score de satisfaction est bas, le système génère une suggestion d'amélioration concrète.
- **Gestion des Connaissances** : Les suggestions sont consolidées par un "agent manager" dans une base de connaissances (`improvement_guidelines.json`) que l'agent de support consulte pour améliorer ses réponses futures.
- **Tests Automatisés** : Une suite de tests pilotée par les données (via un fichier CSV) permet de valider le comportement du système de manière robuste et reproductible.

## ⚙️ Architecture : Le Système à Trois Agents

Le cœur de ce projet réside dans l'interaction entre trois agents spécialisés :

1.  **Agent de Support** (`agents/support_agent.py`)
    - **Rôle** : C'est l'agent principal qui interagit en temps réel avec l'utilisateur.
    - **Fonctionnement** : Il utilise une technique de RAG (Retrieval-Augmented Generation) pour répondre aux questions en se basant sur une base de connaissances vectorielle (ChromaDB). Il prend également en compte les directives d'amélioration fournies par l'Agent Manager.

2.  **Agent d'Analyse** (`agents/analytics_agent.py`)
    - **Rôle** : Intervient à la fin de chaque conversation pour l'analyser.
    - **Fonctionnement** : Il évalue l'historique de la conversation pour déterminer un score de satisfaction (de 0 à 1). Si le score est inférieur à 0.6, il génère une suggestion concrète pour améliorer la performance de l'agent de support. Les résultats sont stockés dans une base de données SQLite (`data/analytics/analytics.db`).

3.  **Agent Manager** (`agents/manager_agent.py`)
    - **Rôle** : L'architecte de l'amélioration continue.
    - **Fonctionnement** : Lorsque l'Agent d'Analyse détecte une conversation peu satisfaisante, il appelle l'Agent Manager. Ce dernier récupère toutes les suggestions d'amélioration de la base de données, les synthétise en utilisant un LLM, et met à jour un fichier central de directives (`data/improvement_guidelines.json`).

Ce cycle permet au système d'apprendre de ses erreurs et de s'adapter pour devenir de plus en plus performant.

## 🚀 Installation

Suivez ces étapes pour lancer le projet sur votre machine locale.

1.  **Cloner le dépôt** (si ce n'est pas déjà fait) :
    ```bash
    git clone <URL_DU_REPO>
    cd <NOM_DU_DOSSIER>
    ```

2.  **Créer un environnement virtuel** :
    ```bash
    python -m venv .venv
    ```

3.  **Activer l'environnement virtuel** :
    - Sur Windows :
      ```powershell
      .\.venv\Scripts\Activate.ps1
      ```
    - Sur macOS/Linux :
      ```bash
      source .venv/bin/activate
      ```

4.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configurer la clé API** :
    - Créez un fichier nommé `.env` à la racine du projet.
    - Ajoutez votre clé API Google Gemini dans ce fichier :
      ```
      GEMINI_API_KEY="VOTRE_CLE_API_ICI"
      ```

## 🛠️ Utilisation

Pour discuter avec le chatbot, lancez l'application Gradio :

```bash
python app.py
```

Ouvrez votre navigateur et allez à l'adresse locale qui s'affiche (généralement `http://127.0.0.1:7860`).

