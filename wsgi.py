"""
Point d'entrée WSGI pour Gunicorn
"""
import os
from main import app, initialize_bot

# Initialiser le bot au démarrage
if not initialize_bot():
    raise RuntimeError("Impossible d'initialiser le bot")

# Point d'entrée pour Gunicorn
application = app

if __name__ == "__main__":
    # Mode développement
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)