import os
from dotenv import load_dotenv

load_dotenv()

# Configuration Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configuration Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configuration de recherche
KEYWORD_THRESHOLD = 0.3  # Seuil de pertinence pour la recherche par mots-clés
RAG_THRESHOLD = 0.7      # Seuil de similarité pour le RAG
MAX_CONTEXT_TOKENS = 3000  # Limite de tokens pour le contexte envoyé à Gemini
MAX_SEARCH_RESULTS = 5   # Nombre max de résultats de recherche

# Messages système
WELCOME_MESSAGE = """
🗳️ **Bot d'Information Électorale**

Salut ! Je suis là pour répondre à tes questions sur les élections présidentielles.

Tu peux me demander :
• Les programmes des candidats
• Les positions sur différents sujets
• Les informations générales sur les élections
• Les procédures de vote

Pose-moi ta question !
"""

HELP_MESSAGE = """
📋 **Commandes disponibles :**

/start - Commencer la conversation
/help - Afficher cette aide
/clear - Effacer l'historique de conversation

💡 **Comment bien poser tes questions :**
• Sois spécifique (ex: "Position de Macron sur l'écologie")
• Tu peux mentionner un candidat précis
• Ou poser des questions générales sur les élections

N'hésite pas à me poser tes questions !
"""


ERROR_MESSAGE = "Désolé, j'ai rencontré un problème. Peux-tu reformuler ta question ?"

WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

PORT = int(os.environ.get('PORT', 5000))

