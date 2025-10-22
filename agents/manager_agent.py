# agents/manager_agent.py
import sqlite3
import json
import os
from datetime import datetime


# ==========================
# Récupération des suggestions d'amélioration
# ==========================
def fetch_low_satisfaction_suggestions(threshold: float = 0.6) -> list:
    """
    Récupère toutes les suggestions d'amélioration pour les conversations
    avec satisfaction < threshold.
    
    Args:
        threshold: Seuil de satisfaction (défaut 0.6)
        
    Returns:
        list: Liste des suggestions avec contexte (theme, satisfaction, suggestion)
    """
    try:
        conn = sqlite3.connect("data/analytics/analytics.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT intent, satisfaction_score, improvement_suggestion, timestamp
            FROM chat_analytics
            WHERE satisfaction_score < ? AND improvement_suggestion IS NOT NULL
            ORDER BY timestamp DESC
        """, (threshold,))
        
        rows = cursor.fetchall()
        conn.close()
        
        suggestions = []
        for row in rows:
            suggestions.append({
                "theme": row[0],
                "satisfaction_score": row[1],
                "suggestion": row[2],
                "timestamp": row[3]
            })
        
        return suggestions
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des suggestions: {e}")
        return []


# ==========================
# Génération des guidelines
# ==========================
def generate_improvement_guidelines(threshold: float = 0.6) -> dict:
    """
    Génère les guidelines d'amélioration basées sur les suggestions.
    Les regroupe par thème pour faciliter la consultation.
    
    Args:
        threshold: Seuil de satisfaction
        
    Returns:
        dict: Guidelines organisées par thème
    """
    suggestions = fetch_low_satisfaction_suggestions(threshold)
    
    # Organiser par thème
    guidelines_by_theme = {}
    for item in suggestions:
        theme = item["theme"]
        if theme not in guidelines_by_theme:
            guidelines_by_theme[theme] = []
        guidelines_by_theme[theme].append({
            "suggestion": item["suggestion"],
            "satisfaction_score": item["satisfaction_score"],
            "date": item["timestamp"]
        })
    
    # Créer un résumé
    guidelines = {
        "last_updated": datetime.now().isoformat(),
        "threshold": threshold,
        "total_suggestions": len(suggestions),
        "by_theme": guidelines_by_theme,
        "summary": _generate_summary(guidelines_by_theme)
    }
    
    return guidelines


def _generate_summary(guidelines_by_theme: dict) -> str:
    """Génère un résumé texte des guidelines principales."""
    if not guidelines_by_theme:
        return "Aucune suggestion d'amélioration disponible."
    
    summary_lines = ["Points clés d'amélioration:"]
    for theme, items in guidelines_by_theme.items():
        summary_lines.append(f"\n🔹 {theme.upper()}:")
        # Garder les suggestions les plus récentes et pertinentes
        for item in items[:2]:  # Top 2 par thème
            summary_lines.append(f"  • {item['suggestion']}")
    
    return "\n".join(summary_lines)


def store_guidelines(guidelines: dict) -> bool:
    """
    Stocke les guidelines dans un fichier JSON.
    
    Args:
        guidelines: Dict des guidelines à stocker
        
    Returns:
        bool: True si succès
    """
    try:
        os.makedirs("data", exist_ok=True)
        filepath = "data/improvement_guidelines.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(guidelines, f, indent=2, ensure_ascii=False)
        print(f"✅ Guidelines mises à jour - {filepath}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du stockage des guidelines: {e}")
        return False


def load_guidelines() -> dict:
    """
    Charge les guidelines depuis le fichier JSON.
    
    Returns:
        dict: Guidelines ou dict vide si fichier inexistant
    """
    filepath = "data/improvement_guidelines.json"
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Impossible de charger les guidelines: {e}")
    
    return {"by_theme": {}, "summary": "Aucune guideline disponible"}


def manager_update() -> dict:
    """
    Fonction principale du manager : récupère suggestions et met à jour guidelines.
    
    Returns:
        dict: Guidelines mises à jour
    """
    print("🔄 Manager: Mise à jour des guidelines d'amélioration...")
    
    guidelines = generate_improvement_guidelines(threshold=0.6)
    store_guidelines(guidelines)
    
    print(f"📊 {guidelines['total_suggestions']} suggestions analysées")
    print(guidelines.get("summary", ""))
    
    return guidelines
