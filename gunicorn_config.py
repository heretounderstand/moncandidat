# Configuration Gunicorn pour la production
import os

# Serveur
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = 1  # Important : 1 seul worker pour éviter les conflits avec le bot Telegram
threads = 2  # Plusieurs threads par worker pour gérer les requêtes concurrentes

# Timeouts
timeout = 60  # Timeout pour les requêtes
keepalive = 2

# Logging
loglevel = "info"
accesslog = "-"  # Logs d'accès sur stdout
errorlog = "-"   # Logs d'erreur sur stderr
capture_output = True

# Performance
preload_app = True  # Charger l'app avant de forker les workers
max_requests = 1000  # Redémarrer le worker après N requêtes
max_requests_jitter = 100

# Process naming
proc_name = "election-bot"

# Worker class
worker_class = "sync"  # Utiliser les workers synchrones avec threading

# Hooks
def on_starting(server):
    """Appelé au démarrage du serveur"""
    server.log.info("🤖 Démarrage du serveur Election Bot...")

def on_reload(server):
    """Appelé lors du rechargement"""
    server.log.info("🔄 Rechargement du serveur...")

def worker_int(worker):
    """Appelé quand un worker reçoit SIGINT"""
    worker.log.info("🛑 Arrêt du worker demandé...")

def on_exit(server):
    """Appelé à l'arrêt du serveur"""
    server.log.info("👋 Arrêt du serveur Election Bot")