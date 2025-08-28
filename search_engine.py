from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from text_processing import extract_keywords, extract_candidate_mentions
from database import Database
from config import KEYWORD_THRESHOLD, RAG_THRESHOLD, MAX_SEARCH_RESULTS

class SearchEngine:
    def __init__(self):
        self.db = Database()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def search(self, query: str) -> Tuple[List[Dict], str]:
        """
        Recherche hybride : mots-clés d'abord, puis RAG si nécessaire
        Retourne (résultats, méthode_utilisée)
        """
        # 1. Extraire les mots-clés et candidats mentionnés
        keywords = extract_keywords(query)
        candidate = extract_candidate_mentions(query)
        
        print(f"Recherche pour: '{query}'")
        print(f"Mots-clés extraits: {keywords}")
        print(f"Candidat détecté: {candidate}")
        
        # 2. Première étape : recherche par mots-clés
        keyword_results = self._search_by_keywords(keywords, candidate)
        
        if self._is_sufficient_results(keyword_results):
            print(f"Recherche par mots-clés suffisante: {len(keyword_results)} résultats")
            return self._rank_results(keyword_results, query), "keywords"
        
        # 3. Deuxième étape : recherche RAG
        print("Recherche par mots-clés insuffisante, passage au RAG")
        rag_results = self._search_by_rag(query, candidate)
        
        if rag_results:
            print(f"Recherche RAG: {len(rag_results)} résultats")
            return rag_results, "rag"
        
        # 4. Fallback : retourner les résultats des mots-clés même s'ils sont peu nombreux
        print("Aucun résultat RAG, retour aux mots-clés")
        return self._rank_results(keyword_results, query), "keywords_fallback"
    
    def _search_by_keywords(self, keywords: List[str], candidate: Optional[str] = None) -> List[Dict]:
        """Recherche par mots-clés"""
        if not keywords:
            return []
        
        results = self.db.search_by_keywords(keywords, candidate)
        
        # Calculer un score de pertinence basé sur le nombre de mots-clés matchés
        for result in results:
            matched_keywords = set(keywords) & set(result.get('keywords', []))
            result['keyword_score'] = len(matched_keywords) / len(keywords)
        
        return results
    
    def _search_by_rag(self, query: str, candidate: Optional[str] = None) -> List[Dict]:
        """Recherche par similarité vectorielle (RAG)"""
        # Générer l'embedding de la question
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Recherche vectorielle
        results = self.db.search_by_similarity(
            query_embedding, 
            candidate, 
            limit=MAX_SEARCH_RESULTS,
            threshold=RAG_THRESHOLD
        )
        
        return results
    
    def _is_sufficient_results(self, results: List[Dict], min_score: float = KEYWORD_THRESHOLD) -> bool:
        """Détermine si les résultats de mots-clés sont suffisants"""
        if not results:
            return False
        
        # Vérifier qu'au moins un résultat a un bon score
        good_results = [r for r in results if r.get('keyword_score', 0) >= min_score]
        return len(good_results) >= 1
    
    def _rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Classe les résultats par pertinence"""
        if not results:
            return []
        
        # Trier par score de mots-clés décroissant
        sorted_results = sorted(
            results, 
            key=lambda x: x.get('keyword_score', 0), 
            reverse=True
        )
        
        return sorted_results[:MAX_SEARCH_RESULTS]
    
    def get_context_for_llm(self, search_results: List[Dict], max_tokens: int = 3000) -> str:
        """
        Prépare le contexte pour envoyer au LLM
        Estime grossièrement les tokens (1 token ≈ 4 caractères)
        """
        if not search_results:
            return ""
        
        context_parts = []
        current_length = 0
        max_chars = max_tokens * 4
        
        for i, result in enumerate(search_results):
            # Formater le résultat
            part = f"""
Document {i+1}:
Source: {result.get('source_link', 'N/A')}
Candidat: {result.get('candidate', 'Information générale')}
Section: {result.get('section', 'N/A')}
Contenu: {result.get('text', '')}
---
"""
            
            # Vérifier si on dépasse la limite
            if current_length + len(part) > max_chars:
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        return '\n'.join(context_parts)
    
    def format_sources(self, search_results: List[Dict]) -> str:
        """Formate les sources pour l'affichage"""
        if not search_results:
            return ""
        
        sources = []
        seen_sources = set()
        
        for result in search_results:
            source_link = result.get('source_link')
            candidate = result.get('candidate', 'Information générale')
            
            if source_link and source_link not in seen_sources:
                sources.append(f"• [{candidate}] {source_link}")
                seen_sources.add(source_link)
        
        if sources:
            return "\n\n📚 **Sources:**\n" + '\n'.join(sources)
        return ""