import os
import re
import cohere
from typing import List, Dict, Tuple
from ..models.review import Review

class AIService:
    def __init__(self):
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.use_cohere = self.cohere_api_key is not None
        
        if self.use_cohere:
            try:
                import httpx
                # Create client with SSL verification disabled for corporate networks
                transport = httpx.HTTPTransport(verify=False)
                self.cohere_client = cohere.Client(self.cohere_api_key, httpx_client=httpx.Client(transport=transport))
                print("🤖 Cohere AI service initialized successfully!")
            except Exception as e:
                print(f"⚠️ Cohere initialization failed: {e}")
                self.use_cohere = False
        else:
            print("📝 Using simplified rule-based AI service")
        
        # Fallback for simple models
        self.review_texts = []
        self.review_ids = []

    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment using Cohere or fallback to rule-based"""
        if self.use_cohere:
            return self._analyze_sentiment_cohere(text)
        return self._analyze_sentiment_simple(text)
    
    def _analyze_sentiment_cohere(self, text: str) -> str:
        """Use Cohere Chat API for sentiment analysis"""
        try:
            response = self.cohere_client.chat(
                model='command-r-08-2024',
                message=f'Analyze the sentiment of this customer review. Respond with only one word: positive, negative, or neutral.\n\nReview: "{text}"',
                max_tokens=5,
                temperature=0.1
            )
            
            result = response.text.strip().lower()
            
            # Ensure we return a valid sentiment
            if result in ['positive', 'negative', 'neutral']:
                return result
            elif 'positive' in result or 'good' in result:
                return 'positive'
            elif 'negative' in result or 'bad' in result:
                return 'negative'
            else:
                return 'neutral'
                
        except Exception as e:
            print(f"Cohere sentiment analysis failed: {e}")
            return self._analyze_sentiment_simple(text)

    def _analyze_sentiment_simple(self, text: str) -> str:
        """Fallback rule-based sentiment analysis"""
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
        """Extract topic using Cohere or fallback to rule-based"""
        if self.use_cohere:
            return self._extract_topic_cohere(text)
        return self._extract_topic_simple(text)
    
    def _extract_topic_cohere(self, text: str) -> str:
        """Use Cohere Chat API for topic extraction"""
        try:
            response = self.cohere_client.chat(
                model='command-r-08-2024',
                message=f'Analyze this customer review and identify the main topic. Choose the most relevant category from: service, food, cleanliness, price, atmosphere, location, technology, other.\n\nReview: "{text}"\n\nRespond with just the topic word:',
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.text.strip().lower()
            
            # Valid topics
            valid_topics = ['service', 'food', 'cleanliness', 'price', 'atmosphere', 'location', 'technology', 'other']
            
            for topic in valid_topics:
                if topic in result:
                    return topic
            
            return 'other'
            
        except Exception as e:
            print(f"Cohere topic extraction failed: {e}")
            return self._extract_topic_simple(text)

    def _extract_topic_simple(self, text: str) -> str:
        """Fallback rule-based topic extraction"""
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
        """Generate suggested reply using Cohere or fallback to templates"""
        if self.use_cohere:
            return self._generate_reply_cohere(review_text, rating, sentiment, topic)
        return self._generate_reply_template(rating, sentiment, topic)

    def _generate_reply_cohere(self, review_text: str, rating: int, sentiment: str, topic: str) -> Dict:
        """Use Cohere Chat API to generate personalized replies"""
        try:
            clean_text = self._apply_safeguards(review_text)
            
            message = f"""You are a professional customer service representative. Write a personalized, empathetic response to this customer review. 

Review: "{clean_text}"
Rating: {rating}/5 stars
Sentiment: {sentiment}
Main Topic: {topic}

Guidelines:
- Be professional and empathetic
- Keep it concise (2-3 sentences)
- If negative, acknowledge concerns and offer to make things right
- If positive, thank them genuinely
- Don't make specific promises you can't keep
- Use a warm, human tone

Write the response:"""
            
            response = self.cohere_client.chat(
                model='command-r-08-2024',
                message=message,
                max_tokens=150,
                temperature=0.7
            )
            
            reply = response.text.strip()
            
            return {
                'reply': reply,
                'tags': {'sentiment': sentiment, 'topic': topic, 'ai_generated': True},
                'reasoning_log': f'Generated using Cohere Chat API for {sentiment} sentiment and {topic} topic.'
            }
            
        except Exception as e:
            print(f"Cohere reply generation failed: {e}")
            return self._generate_reply_template(rating, sentiment, topic)

    def _generate_reply_template(self, rating: int, sentiment: str, topic: str) -> Dict:
        """Fallback template-based reply generation"""
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
            'tags': {'sentiment': sentiment, 'topic': topic, 'ai_generated': False},
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
        """Build similarity index using Cohere embeddings or simple approach"""
        if self.use_cohere:
            self._build_similarity_index_cohere(reviews)
        else:
            self._build_similarity_index_simple(reviews)

    def _build_similarity_index_cohere(self, reviews: List[Review]):
        """Build similarity index using Cohere embeddings"""
        try:
            self.review_texts = [review.text for review in reviews]
            self.review_ids = [review.id for review in reviews]
            
            # Get embeddings for all review texts
            response = self.cohere_client.embed(
                texts=self.review_texts,
                model='embed-english-v3.0'
            )
            self.review_embeddings = response.embeddings
            
        except Exception as e:
            print(f"Cohere embedding failed: {e}")
            self._build_similarity_index_simple(reviews)

    def _build_similarity_index_simple(self, reviews: List[Review]):
        """Simple similarity index for demo"""
        self.review_texts = [review.text for review in reviews]
        self.review_ids = [review.id for review in reviews]
        self.review_embeddings = None

    def find_similar_reviews(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """Find similar reviews using Cohere embeddings or simple matching"""
        if self.use_cohere and hasattr(self, 'review_embeddings') and self.review_embeddings:
            return self._find_similar_reviews_cohere(query, k)
        return self._find_similar_reviews_simple(query, k)

    def _find_similar_reviews_cohere(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """Find similar reviews using Cohere embeddings"""
        try:
            # Get embedding for query
            query_response = self.cohere_client.embed(
                texts=[query],
                model='embed-english-v3.0'
            )
            query_embedding = query_response.embeddings[0]
            
            # Calculate cosine similarity
            import numpy as np
            similarities = []
            
            for i, review_embedding in enumerate(self.review_embeddings):
                # Cosine similarity
                dot_product = np.dot(query_embedding, review_embedding)
                norm_a = np.linalg.norm(query_embedding)
                norm_b = np.linalg.norm(review_embedding)
                
                if norm_a > 0 and norm_b > 0:
                    similarity = dot_product / (norm_a * norm_b)
                    similarities.append((i, similarity))
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for i, similarity in similarities[:k]:
                if similarity > 0.3:  # Threshold
                    results.append((self.review_ids[i], similarity))
            
            return results
            
        except Exception as e:
            print(f"Cohere similarity search failed: {e}")
            return self._find_similar_reviews_simple(query, k)

    def _find_similar_reviews_simple(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """Simple word matching similarity"""
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