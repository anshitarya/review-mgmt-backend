import os
import re
from typing import List, Dict, Tuple
from ..models.review import Review

class AIService:
    def __init__(self):
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.use_local_models = self.cohere_api_key is None
        
        # Simplified approach for demo - using rule-based methods
        self.review_texts = []
        self.review_ids = []

    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of review text using simple rule-based approach"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'best', 'awesome', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'horrible', 'disgusting', 'poor', 'slow', 'rude']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'

    def extract_topic(self, text: str) -> str:
        """Extract main topic from review text"""
        text_lower = text.lower()
        
        topic_keywords = {
            'service': ['service', 'staff', 'employee', 'server', 'cashier', 'manager', 'customer service'],
            'food': ['food', 'meal', 'dish', 'taste', 'flavor', 'menu', 'cooking', 'recipe', 'ingredients'],
            'cleanliness': ['clean', 'dirty', 'bathroom', 'table', 'floor', 'hygiene', 'sanitize'],
            'price': ['price', 'cost', 'expensive', 'cheap', 'money', 'value', 'affordable', 'budget'],
            'atmosphere': ['atmosphere', 'ambiance', 'music', 'noise', 'comfortable', 'seating', 'environment'],
            'location': ['location', 'parking', 'convenient', 'accessibility', 'neighborhood'],
            'technology': ['app', 'website', 'wifi', 'online', 'technology', 'system', 'crash']
        }
        
        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        return 'other'

    def generate_reply(self, review_text: str, rating: int, sentiment: str, topic: str) -> Dict:
        """Generate suggested reply to review"""
        
        # Basic safeguards - redact emails and phones
        clean_text = self._apply_safeguards(review_text)
        
        # Use template-based reply generation
        return self._generate_reply_template(rating, sentiment, topic)

    def _generate_reply_template(self, rating: int, sentiment: str, topic: str) -> Dict:
        """Generate reply using templates"""
        templates = {
            'positive': {
                'service': "Thank you for your wonderful review! We're thrilled you had such a positive experience with our team. Your feedback means the world to us!",
                'food': "We're so happy you enjoyed your meal! Our team works hard to provide quality food, and it's great to hear we succeeded.",
                'default': "Thank you so much for your positive feedback! We truly appreciate your support and look forward to serving you again."
            },
            'negative': {
                'service': "We sincerely apologize for the poor service you experienced. This doesn't reflect our standards. We'd like to make this right - please contact our manager.",
                'food': "We're sorry your meal didn't meet expectations. We take food quality seriously and will review this with our kitchen team.",
                'cleanliness': "Thank you for bringing this to our attention. We've addressed the cleanliness issue immediately and are reviewing our maintenance procedures.",
                'default': "We apologize for your disappointing experience. Your feedback is valuable and we're taking steps to improve. Please give us another chance."
            },
            'neutral': {
                'default': "Thank you for your feedback. We appreciate you taking the time to share your experience and will use it to continue improving."
            }
        }
        
        reply = templates.get(sentiment, {}).get(topic) or templates.get(sentiment, {}).get('default') or templates['neutral']['default']
        
        return {
            'reply': reply,
            'tags': {'sentiment': sentiment, 'topic': topic},
            'reasoning_log': f'Generated using template for {sentiment} sentiment and {topic} topic.'
        }

    def _apply_safeguards(self, text: str) -> str:
        """Apply basic safeguards to text"""
        # Redact email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        # Redact phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        return text

    def build_similarity_index(self, reviews: List[Review]):
        """Build simple similarity index for demo"""
        self.review_texts = [review.text for review in reviews]
        self.review_ids = [review.id for review in reviews]

    def find_similar_reviews(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """Find similar reviews using simple word matching"""
        if not self.review_texts or not query.strip():
            return []
        
        try:
            query_words = set(query.lower().split())
            similarities = []
            
            for i, text in enumerate(self.review_texts):
                text_words = set(text.lower().split())
                # Simple Jaccard similarity
                intersection = len(query_words & text_words)
                union = len(query_words | text_words)
                similarity = intersection / union if union > 0 else 0
                
                if similarity > 0.1:  # Threshold
                    similarities.append((i, similarity))
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for i, similarity in similarities[:k]:
                results.append((self.review_ids[i], similarity))
            
            return results
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []