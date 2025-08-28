import google.generativeai as genai
from typing import List, Dict
from config import GEMINI_API_KEY

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def generate_response(self, user_question: str, context: str = "", 
                         conversation_history: List[Dict] = None) -> str:
        """
        Génère une réponse en utilisant Gemini 1.5 Flash
        """
        try:
            # Construire le prompt système
            system_prompt = self._build_system_prompt()
            
            # Construire le contexte de conversation
            conversation_context = self._build_conversation_context(conversation_history)
            
            # Construire le prompt complet
            full_prompt = f"""
{system_prompt}

{conversation_context}

CONTEXTE DOCUMENTAIRE:
{context if context else "Aucun document spécifique trouvé dans la base de connaissances."}

QUESTION DE L'UTILISATEUR: {user_question}

RÉPONSE:"""
            
            # Générer la réponse
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Réponses plus factuelles
                    max_output_tokens=1000,
                    top_p=0.9,
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Erreur Gemini: {e}")
            return "Désolé, je n'ai pas pu traiter ta demande. Peux-tu reformuler ta question ?"
    
    def _build_system_prompt(self) -> str:
        """Construit le prompt système pour Gemini"""
        return """Tu es un assistant spécialisé dans les élections présidentielles françaises. 

RÔLE:
- Tu fournis des informations factuelles et objectives sur les élections
- Tu présentes les positions des candidats de manière neutre
- Tu peux comparer les programmes sans prendre parti
- Tu expliques les procédures électorales

INSTRUCTIONS:
- Base-toi PRIORITAIREMENT sur le contexte documentaire fourni
- Si l'information n'est pas dans le contexte, dis-le clairement
- Reste neutre et objectif, ne prends pas position
- Cite les sources quand possible
- Réponse en français, style conversationnel mais informatif
- Évite les réponses trop longues (max 800 mots)

INTERDICTIONS:
- Ne pas inventer d'informations
- Ne pas donner de conseils de vote
- Ne pas exprimer d'opinions politiques personnelles
- Ne pas faire de propaganda pour un candidat"""
    
    def _build_conversation_context(self, history: List[Dict]) -> str:
        """Construit le contexte de conversation"""
        if not history:
            return ""
        
        context_parts = ["HISTORIQUE DE LA CONVERSATION:"]
        
        # Prendre les 3 derniers échanges pour garder le contexte récent
        for exchange in history[-3:]:
            context_parts.append(f"User: {exchange['user_message']}")
            context_parts.append(f"Assistant: {exchange['bot_response']}")
        
        context_parts.append("")  # Ligne vide
        return '\n'.join(context_parts)
    
    def generate_no_context_response(self, user_question: str) -> str:
        """
        Génère une réponse quand aucun contexte n'est trouvé
        """
        prompt = f"""
Tu es un assistant pour les élections présidentielles. L'utilisateur te pose cette question:

"{user_question}"

Malheureusement, tu n'as trouvé aucune information spécifique dans ta base de connaissances pour répondre à cette question.

Réponds poliment en:
1. Reconnaissant que tu n'as pas l'information spécifique
2. Suggérant de reformuler la question ou d'être plus spécifique
3. Proposant des sujets connexes que tu pourrais couvrir
4. Restant encourageant et utile

Garde un ton amical et professionnel.
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=300,
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Erreur Gemini (no context): {e}")
            return """Je n'ai pas trouvé d'information spécifique sur ta question dans ma base de connaissances.

Peux-tu essayer de:
• Reformuler ta question
• Être plus spécifique (mentionner un candidat ou un sujet précis)
• Poser une question sur les programmes, positions, ou procédures électorales

Je suis là pour t'aider ! 🗳️"""