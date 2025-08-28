from typing import List, Optional
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter

# Télécharger les ressources NLTK si nécessaire
try:
    nltk.data.find('tokenizers/punkt_tab')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt_tab')
    nltk.download('stopwords')

# Mots vides français
french_stopwords = set(stopwords.words('french'))

# Liste des candidats principaux (à adapter selon tes élections)
CANDIDATES = [
    "seta", "caxton", "ateki", "bello", "bouba", "maigari", "paul", "biya", "jacques", "bouhga", "hagbe", 
    "issa", "tchiroma", "bakary", "hiram", "samuel", "iyodi", "pierre", "kwemo", "cabral", "libii",
    "serge", "espoir", "matomba", "akere", "muna", "joshua", "osih", "hermine", "patricia", "tomaino", "ndam", "njoya"
]

def extract_keywords(text: str, max_keywords: int = 8) -> List[str]:
    """
    Extrait les mots-clés d'un texte en français
    """
    if not text:
        return []
    
    # Nettoyer et tokeniser
    text = text.lower()
    tokens = word_tokenize(text, language='french')
    
    # Filtrer les mots (alphabétiques, >2 caractères, pas de mots vides)
    filtered_words = [
        word for word in tokens 
        if word.isalpha() and len(word) > 2 and word not in french_stopwords
    ]
    
    # Compter et garder les plus fréquents
    word_freq = Counter(filtered_words)
    keywords = [word for word, _ in word_freq.most_common(max_keywords)]
    
    return keywords

def extract_candidate_mentions(text: str) -> Optional[str]:
    """
    Détecte si un candidat est mentionné dans le texte
    Retourne le nom normalisé du candidat ou None
    """
    text_lower = text.lower()
    
    # Rechercher des mentions de candidats
    for candidate in CANDIDATES:
        if candidate in text_lower:
            # Retourner une version normalisée
            if "seta" in candidate:
                return "Seta Caxton Ateki"
            elif "caxton" in candidate:
                return "Seta Caxton Ateki"
            elif "ateki" in candidate:
                return "Seta Caxton Ateki"
            elif "bello" in candidate:
                return "Bello Bouba Maigari"
            elif "bouba" in candidate:
                return "Bello Bouba Maigari"
            elif "maigari" in candidate:
                return "Bello Bouba Maigari"
            elif "paul" in candidate:
                return "Paul Biya"
            elif "biya" in candidate:
                return "Paul Biya"
            elif "jacques" in candidate:
                return "Jacques Bouhga-Hagbe"
            elif "bouhga" in candidate:
                return "Jacques Bouhga-Hagbe"
            elif "hagbe" in candidate:
                return "Jacques Bouhga-Hagbe"
            elif "issa" in candidate:
                return "Issa Tchiroma Bakary"
            elif "tchiroma" in candidate:
                return "Issa Tchiroma Bakary"
            elif "bakary" in candidate:
                return "Issa Tchiroma Bakary"
            elif "hiram" in candidate:
                return "Hiram Samuel Iyodi"
            elif "samuel" in candidate:
                return "Hiram Samuel Iyodi"
            elif "iyodi" in candidate:
                return "Hiram Samuel Iyodi"
            elif "pierre" in candidate:
                return "Pierre Kwemo"
            elif "kwemo" in candidate:
                return "Pierre Kwemo"
            elif "cabral" in candidate:
                return "Cabral Libii"
            elif "libii" in candidate:
                return "Cabral Libii"
            elif "serge" in candidate:
                return "Serge Espoir Matomba"
            elif "espoir" in candidate:
                return "Serge Espoir Matomba"
            elif "matomba" in candidate:
                return "Serge Espoir Matomba"
            elif "akere" in candidate:
                return "Akere Muna"
            elif "muna" in candidate:
                return "Akere Muna"
            elif "joshua" in candidate:
                return "Joshua Osih"
            elif "osih" in candidate:
                return "Joshua Osih"
            elif "hermine" in candidate:
                return "Hermine Patricia Tomaïno Ndam Njoya"
            elif "patricia" in candidate:
                return "Hermine Patricia Tomaïno Ndam Njoya"
            elif "tomaino" in candidate:
                return "Hermine Patricia Tomaïno Ndam Njoya"
            elif "ndam" in candidate:
                return "Hermine Patricia Tomaïno Ndam Njoya"
            elif "njoya" in candidate:
                return "Hermine Patricia Tomaïno Ndam Njoya"
    
    return None

def is_greeting(text: str) -> bool:
    """
    Détecte si le message est une salutation
    """
    greetings = ["salut", "bonjour", "hello", "bonsoir", "coucou", "hey"]
    text_lower = text.lower().strip()
    
    return any(greeting in text_lower for greeting in greetings) and len(text.split()) <= 3