import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request, Response
import asyncio
import threading
import queue
import time
from config import TELEGRAM_BOT_TOKEN, WELCOME_MESSAGE, HELP_MESSAGE, ERROR_MESSAGE, WEBHOOK_URL
from database import Database
from search_engine import SearchEngine
from gemini_client import GeminiClient
from text_processing import is_greeting

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ElectionBot:
    def __init__(self):
        self.db = Database()
        self.search_engine = SearchEngine()
        self.gemini_client = GeminiClient()
        self.application = None
        self.update_queue = queue.Queue()
        self.loop = None
        self.loop_thread = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start"""
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        logger.info(f"Nouveau utilisateur: {user.first_name} (ID: {chat_id})")
        
        await update.message.reply_text(
            WELCOME_MESSAGE, 
            parse_mode='Markdown'
        )
        
        # Sauvegarder le démarrage de conversation
        self.db.save_message(
            chat_id=chat_id,
            user_message="/start",
            bot_response=WELCOME_MESSAGE
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /help"""
        await update.message.reply_text(
            HELP_MESSAGE, 
            parse_mode='Markdown'
        )
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /clear - Efface l'historique"""
        chat_id = update.effective_chat.id
        
        success = self.db.clear_conversation(chat_id)
        
        if success:
            message = "✅ Historique de conversation effacé !"
        else:
            message = "❌ Erreur lors de l'effacement de l'historique."
        
        await update.message.reply_text(message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Traite les messages des utilisateurs"""
        try:
            chat_id = update.effective_chat.id
            user_message = update.message.text
            user = update.effective_user
            
            logger.info(f"Message de {user.first_name} (ID: {chat_id}): {user_message}")
            
            # Envoyer un indicateur "en train d'écrire"
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            
            # Traiter le message
            bot_response = await self._process_user_message(chat_id, user_message)
            
            # Envoyer la réponse
            await update.message.reply_text(bot_response)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")
            await update.message.reply_text(ERROR_MESSAGE)
    
    async def _process_user_message(self, chat_id: int, user_message: str) -> str:
        """
        Traite un message utilisateur et retourne la réponse
        """
        try:
            # Cas spéciaux : salutations simples
            if is_greeting(user_message):
                response = "Salut ! 👋 Pose-moi tes questions sur les élections présidentielles !"
                self.db.save_message(chat_id, user_message, response)
                return response
            
            # 1. Récupérer l'historique de conversation
            conversation_history = self.db.get_conversation_history(chat_id, limit=5)
            
            # 2. Recherche dans la base de connaissances
            search_results, search_method = self.search_engine.search(user_message)
            
            # 3. Préparer le contexte pour Gemini
            context = self.search_engine.get_context_for_llm(search_results)
            
            # 4. Générer la réponse avec Gemini
            if context:
                bot_response = self.gemini_client.generate_response(
                    user_message, 
                    context, 
                    conversation_history
                )
                
                # Ajouter les sources
                sources = self.search_engine.format_sources(search_results)
                if sources:
                    bot_response += sources
                    
                logger.info(f"Réponse générée avec contexte ({search_method}): {len(search_results)} documents")
            else:
                bot_response = self.gemini_client.generate_no_context_response(user_message)
                logger.info("Réponse générée sans contexte")
            
            # 5. Sauvegarder l'échange
            self.db.save_message(
                chat_id=chat_id,
                user_message=user_message,
                bot_response=bot_response,
                search_results=search_results[:3] if search_results else None
            )
            
            return bot_response
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement: {e}")
            return ERROR_MESSAGE
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Gestionnaire d'erreurs global"""
        logger.error(f"Exception lors de la mise à jour {update}: {context.error}")
    
    def start_async_loop(self):
        """Démarre la boucle d'événements asynchrone dans un thread séparé"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
        # Attendre que la boucle soit prête
        while self.loop is None:
            time.sleep(0.1)
    
    def stop_async_loop(self):
        """Arrête la boucle d'événements"""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
    
    async def setup_application(self):
        """Configure l'application Telegram"""
        print("🤖 Configuration du bot d'élections...")
        
        # Créer l'application Telegram
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Ajouter les gestionnaires
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Gestionnaire d'erreurs
        self.application.add_error_handler(self.error_handler)
        
        # Initialiser l'application
        await self.application.initialize()
        await self.application.start()
        
        print("✅ Bot configuré avec succès !")
    
    async def set_webhook(self, webhook_url: str):
        """Configure le webhook sur Telegram"""
        try:
            success = await self.application.bot.set_webhook(
                url=webhook_url,
                allowed_updates=['message', 'edited_message', 'callback_query']
            )
            
            if success:
                print(f"✅ Webhook configuré: {webhook_url}")
                
                # Vérifier le webhook
                webhook_info = await self.application.bot.get_webhook_info()
                print(f"📡 Info webhook: {webhook_info.url}")
                if webhook_info.last_error_date:
                    print(f"⚠️  Dernière erreur: {webhook_info.last_error_message}")
            else:
                print("❌ Échec de la configuration du webhook")
                
        except Exception as e:
            print(f"❌ Erreur lors de la configuration du webhook: {e}")
            logger.error(f"Erreur webhook: {e}")
    
    def process_update_sync(self, update_data):
        """Traite une mise à jour de manière synchrone"""
        if not self.loop or not self.application:
            logger.error("Boucle ou application non initialisée")
            return
        
        try:
            # Créer l'objet Update
            update = Update.de_json(update_data, self.application.bot)
            
            # Planifier le traitement dans la boucle d'événements
            future = asyncio.run_coroutine_threadsafe(
                self.application.process_update(update), 
                self.loop
            )
            
            # Attendre le résultat (avec timeout)
            future.result(timeout=30)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'update: {e}")

# Instance globale du bot
bot_instance = ElectionBot()

# Configuration Flask
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint pour Render"""
    return {"status": "healthy", "service": "election-bot"}, 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint pour recevoir les webhooks de Telegram"""
    try:
        # Récupérer les données JSON
        json_data = request.get_json(force=True)
        
        if not json_data:
            logger.warning("Webhook reçu sans données JSON")
            return Response(status=200)
        
        logger.info(f"Webhook reçu")
        
        # Traiter l'update dans un thread séparé
        threading.Thread(
            target=bot_instance.process_update_sync,
            args=(json_data,),
            daemon=True
        ).start()
        
        return Response(status=200)
        
    except Exception as e:
        logger.error(f"Erreur dans le webhook: {e}")
        return Response(status=500)

def initialize_bot():
    """Initialise le bot"""
    webhook_url = WEBHOOK_URL
    
    if not webhook_url:
        print("⚠️  Variable WEBHOOK_URL non définie")
        print("💡 Pour tester en local avec ngrok:")
        print("   1. Installez ngrok: https://ngrok.com/")
        print("   2. Lancez: ngrok http 5000")
        print("   3. Définissez WEBHOOK_URL=https://your-id.ngrok.io/webhook")
        print("   4. Relancez le bot")
        return False
    
    try:
        # Démarrer la boucle d'événements
        bot_instance.start_async_loop()
        
        # Configurer le bot et le webhook
        setup_future = asyncio.run_coroutine_threadsafe(
            bot_instance.setup_application(), 
            bot_instance.loop
        )
        setup_future.result(timeout=30)
        
        webhook_future = asyncio.run_coroutine_threadsafe(
            bot_instance.set_webhook(webhook_url), 
            bot_instance.loop
        )
        webhook_future.result(timeout=30)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        logger.error(f"Erreur initialisation: {e}")
        return False

def main():
    """Fonction principale"""
    try:
        print("🤖 Démarrage du bot d'élections...")
        
        # Initialiser le bot
        if not initialize_bot():
            return
        
        # Lancer Flask
        port = int(os.environ.get('PORT', 5000))
        host = '0.0.0.0'
        
        print(f"🚀 Démarrage du serveur Flask sur {host}:{port}")
        app.run(host=host, port=port, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du bot demandé par l'utilisateur")
        bot_instance.stop_async_loop()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        logger.error(f"Erreur fatale: {e}")
        bot_instance.stop_async_loop()

if __name__ == '__main__':
    main()
