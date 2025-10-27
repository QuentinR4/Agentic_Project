import os
import sqlite3
import pandas as pd
import operator
from datetime import datetime
import time

import sys

# Ajoute le dossier racine du projet au path Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.support_agent import agent_support_fnac
from agents.analytics_agent import analytics_agent, init_analytics_db


# --- Chargement du CSV ---
def load_test_scenarios():
    csv_path = os.path.join(os.path.dirname(__file__), "test_scenarios.csv")
    df = pd.read_csv(csv_path, sep=";")
    return df.to_records(index=False)


# --- Exécution d’un scénario ---
def run_conversation_test(test_name, conversation_steps, expected_satisfaction_operator, expected_satisfaction_value, should_generate_suggestion):
    print(f"\n🧪 TEST : {test_name}")
    print("────────────────────────────")

    # Initialisation
    init_analytics_db()
    support_agent, memory = agent_support_fnac()

    steps = conversation_steps.split(";")
    for step in steps:
        response = support_agent(step)
        print(f"👤 {step}")
        print(f"🤖 {response}\n")
        time.sleep(0.5)

    # Analyse post-conversation
    conversation_history = memory.load_memory_variables({})["chat_history"]
    last_user_message = steps[-1]
    analytics_agent(
        user_message=last_user_message,
        agent_response="",
        chat_history=conversation_history,
        duration=100.0
    )

    # Lecture du résultat depuis SQLite
    conn = sqlite3.connect("data/analytics/analytics.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT satisfaction_score, improvement_suggestion
        FROM chat_analytics
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    conn.close()

    if not result:
        print("⚠️ Aucune donnée d'analyse trouvée.")
        return False

    actual_score, actual_suggestion = result
    
    # Normalisation des opérateurs et types
    expected_satisfaction_operator = expected_satisfaction_operator.strip().lower()
    actual_score = float(actual_score)
    should_generate_suggestion = str(should_generate_suggestion).strip().lower() in ["yes", "true", "1"]

    # Vérifications
    op_map = {
        "ge": operator.ge, ">=": operator.ge,
        "gt": operator.gt, ">": operator.gt,
        "le": operator.le, "<=": operator.le,
        "lt": operator.lt, "<": operator.lt,
        "eq": operator.eq, "==": operator.eq,
        "ne": operator.ne, "!=": operator.ne,
    }

    satisfaction_check = op_map[expected_satisfaction_operator](actual_score, expected_satisfaction_value)
    has_suggestion = bool(actual_suggestion and str(actual_suggestion).strip())
    suggestion_check = has_suggestion == should_generate_suggestion

    print(f"🎯 Satisfaction attendue : {expected_satisfaction_operator} {expected_satisfaction_value}")
    print(f"📈 Satisfaction obtenue : {actual_score:.2f}")
    print(f"💡 Suggestion générée : {has_suggestion}")
    print(f"✅ Test {'RÉUSSI' if satisfaction_check and suggestion_check else 'ÉCHOUÉ'}")
    print("────────────────────────────\n")

    return satisfaction_check and suggestion_check


# --- Exécution globale ---print
if __name__ == "__main__":
    scenarios = load_test_scenarios()
    results = []
    for s in scenarios:
        success = run_conversation_test(*s)
        results.append((s.test_name, "PASSED" if success else "FAILED"))

    # Résumé final
    print("\n📊 RÉSUMÉ FINAL DES TESTS")
    print("────────────────────────────")
    for name, status in results:
        print(f"{name}: {status}")

    # Export CSV rapport
    report_df = pd.DataFrame(results, columns=["test_name", "status"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"tests/results/test_results_{timestamp}.csv"
    os.makedirs("tests/results", exist_ok=True)
    report_df.to_csv(report_path, index=False)
    print(f"\n🗂️ Rapport sauvegardé dans : {report_path}")
