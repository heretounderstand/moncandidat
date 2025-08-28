from supabase import create_client, Client
from typing import List, Dict, Optional
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_KEY

class Database:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # ===== GESTION DES CONVERSATIONS =====
    
    def save_message(self, chat_id: int, user_message: str, bot_response: str, 
                     search_results: Optional[List[Dict]] = None):
        """Sauvegarde un échange dans la conversation"""
        try:
            data = {
                'chat_id': chat_id,
                'user_message': user_message,
                'bot_response': bot_response,
                'search_results': search_results,
                'timestamp': datetime.now().isoformat()
            }
            
            result = self.supabase.table('conversations').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erreur sauvegarde message: {e}")
            return None
    
    def get_conversation_history(self, chat_id: int, limit: int = 10) -> List[Dict]:
        """Récupère l'historique d'une conversation"""
        try:
            result = self.supabase.table('conversations')\
                .select('user_message, bot_response, timestamp')\
                .eq('chat_id', chat_id)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            return list(reversed(result.data)) if result.data else []
        except Exception as e:
            print(f"Erreur récupération historique: {e}")
            return []
    
    def clear_conversation(self, chat_id: int) -> bool:
        """Efface l'historique d'une conversation"""
        try:
            self.supabase.table('conversations')\
                .delete()\
                .eq('chat_id', chat_id)\
                .execute()
            return True
        except Exception as e:
            print(f"Erreur effacement conversation: {e}")
            return False
    
    # ===== RECHERCHE DANS LA BASE DE CONNAISSANCES =====
    
    def search_by_keywords(self, keywords: List[str], candidate: Optional[str] = None) -> List[Dict]:
        """Recherche par mots-clés dans la base de connaissances"""
        try:
            query = self.supabase.table('knowledge').select('*')
            
            # Filtrer par candidat si spécifié
            if candidate:
                query = query.eq('candidate', candidate)
            
            # Recherche par mots-clés (utilise l'opérateur overlap pour les arrays)
            query = query.overlaps('keywords', keywords)
            
            result = query.limit(20).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Erreur recherche mots-clés: {e}")
            return []
    
    def search_by_similarity(self, embedding: List[float], candidate: Optional[str] = None, 
                           limit: int = 5, threshold: float = 0.7) -> List[Dict]:
        """Recherche par similarité vectorielle (RAG)"""
        try:
            # Construction de la requête RPC pour la recherche vectorielle
            params = {
                'query_embedding': embedding,
                'match_threshold': threshold,
                'match_count': limit
            }
            
            if candidate:
                params['candidate_filter'] = candidate
            
            result = self.supabase.rpc('match_documents', params).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Erreur recherche vectorielle: {e}")
            return []
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Récupère un document par son ID"""
        try:
            result = self.supabase.table('knowledge')\
                .select('*')\
                .eq('id', doc_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            print(f"Erreur récupération document: {e}")
            return None