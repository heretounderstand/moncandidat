import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, WELCOME_MESSAGE, HELP_MESSAGE, ERROR_MESSAGE
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

def main():
    """Fonction principale"""
    print("🤖 Démarrage du bot d'élections...")
    
    # Créer l'instance du bot
    bot = ElectionBot()
    
    # Créer l'application Telegram
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Ajouter les gestionnaires
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("clear", bot.clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Gestionnaire d'erreurs
    application.add_error_handler(bot.error_handler)
    
    print("✅ Bot configuré avec succès !")
    print("🚀 Démarrage du polling...")
    
    # Démarrer le bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du bot demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        logger.error(f"Erreur fatale: {e}")