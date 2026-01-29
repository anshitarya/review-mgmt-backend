import os
import re
from typing import List, Dict, Tuple
import cohere
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from ..models.review import Review

class AIService:
    def __init__(self):
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.use_local_models = self.cohere_api_key is None
        
        if self.use_local_models:
            # Load local models for fallback
            try:
                self.sentiment_pipeline = pipeline("sentiment-analysis", 
                                                 model="cardiffnlp/twitter-roberta-base-sentiment-latest")
                self.summarization_pipeline = pipeline("summarization", 
                                                      model="facebook/bart-large-cnn")
            except Exception as e:
                print(f"Warning: Could not load local models: {e}")
                self.sentiment_pipeline = None
                self.summarization_pipeline = None
        else:
            self.cohere_client = cohere.Client(self.cohere_api_key)
            
        # Initialize TF-IDF vectorizer for similarity search
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.review_texts = []
        self.review_ids = []

    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of review text"""
        if self.use_local_models and self.sentiment_pipeline:
            try:
                result = self.sentiment_pipeline(text)[0]
                label = result['label'].lower()
                # Map different model outputs to our standardized labels
                if 'pos' in label or label == 'label_2':
                    return 'positive'
                elif 'neg' in label or label == 'label_0':
                    return 'negative'
                else:
                    return 'neutral'
            except Exception:
                pass
        
        # Fallback to simple rule-based sentiment
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'horrible', 'disgusting', 'poor']
        
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
        
        if not self.use_local_models:
            try:
                return self._generate_reply_cohere(clean_text, rating, sentiment, topic)
            except Exception as e:
                print(f"Cohere API error: {e}")
        
        # Fallback to template-based reply
        return self._generate_reply_template(rating, sentiment, topic)

    def _generate_reply_cohere(self, text: str, rating: int, sentiment: str, topic: str) -> Dict:
        """Generate reply using Cohere API"""
        prompt = f"""
        You are a customer service manager responding to a customer review. Generate a professional, empathetic response.
        
        Review: "{text}"
        Rating: {rating}/5
        Sentiment: {sentiment}
        Topic: {topic}
        
        Guidelines:
        - Be professional and empathetic
        - Address specific concerns mentioned
        - Thank the customer for their feedback
        - Offer concrete next steps when appropriate
        - Keep response under 150 words
        
        Response:
        """
        
        response = self.cohere_client.generate(
            model='command',
            prompt=prompt,
            max_tokens=150,
            temperature=0.7,
            stop_sequences=["Response:", "Review:"]
        )
        
        reply_text = response.generations[0].text.strip()
        
        return {
            'reply': reply_text,
            'tags': {'sentiment': sentiment, 'topic': topic},
            'reasoning_log': f'Generated using Cohere API based on {sentiment} sentiment and {topic} topic.'
        }

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
        """Build TF-IDF index for similarity search"""
        self.review_texts = [review.text for review in reviews]
        self.review_ids = [review.id for review in reviews]
        
        if self.review_texts:
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.review_texts)

    def find_similar_reviews(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """Find similar reviews using cosine similarity"""
        if self.tfidf_matrix is None or not query.strip():
            return []
        
        try:
            # Transform query to TF-IDF vector
            query_vector = self.tfidf_vectorizer.transform([query])
            
            # Calculate cosine similarities
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top k similar reviews (excluding exact matches)
            similar_indices = np.argsort(similarities)[::-1]
            
            results = []
            for idx in similar_indices:
                if similarities[idx] > 0.1 and len(results) < k:  # Threshold to avoid very low similarities
                    results.append((self.review_ids[idx], similarities[idx]))
            
            return results
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []