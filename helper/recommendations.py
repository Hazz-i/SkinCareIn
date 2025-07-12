import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import os
from typing import List, Dict, Tuple
import re

from helper.functions import find_harmful_ingredients_with_details


from utils.database import read_table

class SkinCareRecommendationSystem:
    def __init__(self, table_name: str = "products"):
        """
        Initialize the recommendation system using database table
        
        Args:
            table_name: Name of the database table containing skincare products
        """
        self.table_name = table_name
        self.df = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.scaler = StandardScaler()
        self.load_data_from_db()
        self.prepare_recommendation_system()

    def load_data_from_db(self):
        """
        Load product data from the database table into a DataFrame
        """
        try:
            self.df = read_table(self.table_name)
            if self.df is None or self.df.empty:
                raise ValueError(f"No data found in table '{self.table_name}'")
            print(f"Loaded {len(self.df)} products from database table '{self.table_name}'")
        except Exception as e:
            print(f"Error loading data from database: {e}")
            self.df = None
    
    def clean_ingredients_text(self, ingredients: str) -> str:
        """Clean and normalize ingredients text"""
        if pd.isna(ingredients) or ingredients == '' or ingredients == 'ingredients tidak ditemukan.':
            return ''
        
        # Convert to lowercase
        ingredients = ingredients.lower()
        
        # Remove special characters but keep important separators
        ingredients = re.sub(r'[^\w\s,.-]', ' ', ingredients)
        
        # Normalize whitespace
        ingredients = re.sub(r'\s+', ' ', ingredients)
        
        # Remove common non-ingredient words
        words = ingredients.split()
        
        return ' '.join(words)
    
    def prepare_recommendation_system(self):
        """Prepare TF-IDF vectorizer and similarity matrix"""
        try:
            # Clean ingredients text
            self.df['ingredients'] = self.df['ingredients'].apply(self.clean_ingredients_text)
            
            # Remove products with empty ingredients
            valid_ingredients = self.df['ingredients'] != ''
            print(f"Found {valid_ingredients.sum()} products with valid ingredients out of {len(self.df)} total")
            
            if valid_ingredients.sum() == 0:
                raise ValueError("No valid ingredients found in dataset")
            
            self.df = self.df[valid_ingredients].reset_index(drop=True)
            
            # Create TF-IDF matrix with adjusted parameters
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=3000,
                stop_words='english',
                lowercase=True,
                ngram_range=(1, 2),  # Include bigrams for better matching
                min_df=1,  # Lower threshold for small dataset
                max_df=0.95  # Ignore terms that appear in more than 95% of documents
            )
            
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.df['ingredients'])
            print(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
            
        except Exception as e:
            print(f"Error preparing recommendation system: {e}")
            raise
    
    def find_similar_products(self, input_ingredients: List[str], 
                                top_k: int = 10) -> List[Dict]:
        """
        Find products with similar ingredients
        
        Args:
            input_ingredients: List of ingredients from scanned product
            skin_type: User's skin type to filter recommendations
            top_k: Number of recommendations to return
            
        Returns:
            List of recommended products with similarity scores
        """
        try:
            # Convert input ingredients to text
            input_text = ' '.join([self.clean_ingredients_text(ing) for ing in input_ingredients])
            
            if not input_text.strip():
                return []
            
            # Transform input ingredients using fitted TF-IDF vectorizer
            input_vector = self.tfidf_vectorizer.transform([input_text])
            
            # Calculate cosine similarity
            similarity_scores = cosine_similarity(input_vector, self.tfidf_matrix).flatten()
            
            # Get top similar products
            similar_indices = similarity_scores.argsort()[::-1][:top_k * 3]  # Get more to filter for duplicates
            
            recommendations = []
            seen_products = set()  # Track unique products to avoid duplicates
            
            for idx in similar_indices:
                if len(recommendations) >= top_k:
                    break
                    
                product = self.df.iloc[idx]
                similarity_score = similarity_scores[idx]
                
                # Skip if similarity is too low (lowered threshold for small dataset)
                if similarity_score < 0.05:
                    continue
                
                # Extract product name for duplicate checking
                product_name = str(product['title']) if 'title' in product and pd.notna(product['title']) else 'Unknown'
                
                # Skip if we've already seen this product (avoid duplicates)
                if product_name in seen_products:
                    continue
                
                # Add to seen products set
                seen_products.add(product_name)
                
                # Extract product information - safely access pandas Series
                recommendation = {
                    'product_name': product_name,
                    'product_image': str(product['image_url']) if 'image_url' in product and pd.notna(product['image_url']) else 'Unknown',
                    'similarity_score': float(similarity_score),
                    'price': str(product['price']) if 'price' in product and pd.notna(product['price']) else 'Unknown',
                    'product_link': str(product['link']) if 'link' in product and pd.notna(product['link']) else 'Unknown',
                }
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            print(f"Error finding similar products: {e}")
            return []
    
    def filter_safe_products(self, recommendations: List[Dict], 
                            skin_type: str) -> List[Dict]:
        """
        Filter out products that contain harmful ingredients for the skin type
        
        Args:
            recommendations: List of product recommendations
            skin_type: User's skin type
            
        Returns:
            Filtered list of safe recommendations (no duplicates)
        """
        from helper.functions import get_ingredients_to_avoid
        
        safe_recommendations = []
        seen_products = set()  # Track unique products to avoid duplicates
        
        # Get ingredients to avoid based on skin type
        avoid_list = get_ingredients_to_avoid(skin_type)
        
        for product in recommendations:
            product_name = product.get('product_name', 'Unknown')
            
            # Skip if we've already seen this product (avoid duplicates)
            if product_name in seen_products:
                continue
            
            product_ingredients = str(product.get('ingredients', ''))
            
            # Find harmful ingredients in this product's ingredients
            harmful_ingredients = find_harmful_ingredients_with_details(product_ingredients, avoid_list, skin_type)
            
            # Check if product is safe (no harmful ingredients found)
            is_safe = len(harmful_ingredients) == 0
            
            if is_safe:
                seen_products.add(product_name)  # Add to seen products
                safe_recommendations.append(product)
            else:
                # Add information about why product was filtered out (but don't add to safe list)
                harmful_names = [item['ingredient'] for item in harmful_ingredients if isinstance(item, dict) and 'ingredient' in item]
                product['filtered_reason'] = f"Contains harmful ingredients: {', '.join(harmful_names)}"
        
        return safe_recommendations
    
    def get_ingredient_based_recommendations(self, 
                                            input_ingredients: List[str],
                                            skin_type: str,
                                            top_k: int = 5) -> Dict:
        """
        Get ingredient-based recommendations for safe products
        
        Args:
            input_ingredients: ingredients from scanned product
            skin_type: User's skin type
            harmful_ingredients: List of harmful ingredients to avoid (can be strings or dicts)
            top_k: Number of recommendations to return
            
        Returns:
            Dictionary containing recommendations and metadata
        """
        try:
            # Find similar products
            similar_products = self.find_similar_products(
                input_ingredients, 
                top_k * 3 
            )
            
            # Filter out unsafe products if harmful ingredients provided
            safe_products = self.filter_safe_products(
                similar_products, 
                skin_type
            )
            
            # Take top K safe products (use filtered safe products, not original similar_products)
            final_recommendations = safe_products[:top_k]
            
            return {
                'recommendations': final_recommendations,
                'total_found': len(similar_products),
                'total_safe': len(safe_products),
                'skin_type': skin_type,
                'recommendation_count': len(final_recommendations)
            }
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return {
                'recommendations': [],
                'recommendation_count': 0,
                'error': str(e)
            }
    
    def get_skin_type_recommendations(self, skin_type: str, top_k: int = 5) -> Dict:
        """
        Get product recommendations based on skin type by searching descriptions
        
        Args:
            skin_type: User's skin type (oily, dry, normal, acne, sensitive)
            top_k: Number of recommendations to return
            
        Returns:
            Dictionary containing recommendations
        """
        try:
            import re
            
            # Create regex patterns for skin type matching
            skin_type_patterns = [
                # Universal patterns - products for all skin types
                r'\b(semua\s+jenis\s+kulit|all\s+skin\s+types?|segala\s+jenis\s+kulit|untuk\s+semua\s+kulit)\b',
                # Specific skin type patterns
                rf'\b(untuk\s+kulit\s+{skin_type}|{skin_type}\s+skin|kulit\s+{skin_type})\b'
            ]
            
            # Additional specific patterns based on skin type
            if skin_type == "oily":
                skin_type_patterns.extend([
                    r'\b(berminyak|oily|excess\s+oil|kontrol\s+minyak|oil\s+control)\b'
                ])
            elif skin_type == "dry":
                skin_type_patterns.extend([
                    r'\b(kering|dry|dehidrasi|dehydrat|moisturiz|pelembab)\b'
                ])
            elif skin_type == "sensitive":
                skin_type_patterns.extend([
                    r'\b(sensitif|sensitive|gentle|lembut|hypoallergenic)\b'
                ])
            elif skin_type == "acne":
                skin_type_patterns.extend([
                    r'\b(jerawat|acne|breakout|blemish|anti\s+acne)\b'
                ])
            elif skin_type == "normal":
                skin_type_patterns.extend([
                    r'\b(normal|seimbang|balanced)\b'
                ])
            
            # Combine all patterns
            combined_pattern = '|'.join(skin_type_patterns)
            
            # Check if description column exists
            if 'description' not in self.df.columns:
                return {
                    'recommendations': [],
                    'total_found': 0,
                    'skin_type': skin_type,
                    'recommendation_count': 0,
                    'error': 'Description column not found in database'
                }
            
            # Filter products based on description matching
            matching_products = []
            seen_products = set()
            
            for idx, row in self.df.iterrows():
                description = str(row.get('description', '')).lower()
                
                # Skip if no description
                if not description or description == 'nan':
                    continue
                
                # Check if description matches any pattern
                if re.search(combined_pattern, description, re.IGNORECASE):
                    product_name = str(row.get('title', 'Unknown'))
                    
                    # Skip duplicates
                    if product_name in seen_products:
                        continue
                    
                    seen_products.add(product_name)
                    
                    # Create product recommendation
                    product_rec = {
                        'product_name': product_name,
                        'product_image': str(row.get('image_url', 'Unknown')),
                        'product_link': str(row.get('link', 'Unknown')),
                        'price': str(row.get('price', 'Unknown')),
                        'match_reason': f'Suitable for {skin_type} skin type'
                    }
                    
                    matching_products.append(product_rec)
                    
                    # Stop if we have enough products
                    if len(matching_products) >= top_k:
                        break
            
            return {
                'recommendations': matching_products,
                'total_found': len(matching_products),
                'skin_type': skin_type,
                'recommendation_count': len(matching_products)
            }
            
        except Exception as e:
            print(f"Error getting skin type recommendations: {e}")
            return {
                'recommendations': [],
                'total_found': 0,
                'skin_type': skin_type,
                'recommendation_count': 0,
                'error': str(e)
            }

# Initialize global recommendation system with better error handling
recommendation_system = None

def initialize_recommendation_system():
    """Initialize recommendation system with error handling"""
    global recommendation_system
    
    try:
        recommendation_system = SkinCareRecommendationSystem()
        print("Recommendation system initialized successfully")
        return True
    except Exception as e:
        print(f"Failed to initialize recommendation system: {e}")
        recommendation_system = None
        return False

# Try to initialize
initialize_recommendation_system()

def get_skincare_recommendations(input_ingredients: List[str], 
                                skin_type: str,
                                top_k: int = 5) -> Dict:
    """
    Wrapper function to get skincare recommendations
    
    Args:
        input_ingredients: List of ingredients from scanned product
        skin_type: User's skin type
        harmful_ingredients: List of harmful ingredients to avoid (can be strings or dicts)
        top_k: Number of recommendations to return
        
    Returns:
        Dictionary containing recommendations
    """
    global recommendation_system
    
    # Try to initialize if not already done
    if recommendation_system is None:
        if not initialize_recommendation_system():
            return {
                'recommendations': [],
                'total_found': 0,
                'total_safe': 0,
                'skin_type': skin_type,
                'recommendation_count': 0,
                'error': 'Recommendation system could not be initialized'
            }
    
    try:
        return recommendation_system.get_ingredient_based_recommendations(
            input_ingredients,
            skin_type,
            top_k
        )
        
    except Exception as e:
        print(f"Error in get_skincare_recommendations: {e}")
        return {
            'recommendations': [],
            'total_found': 0,
            'total_safe': 0,
            'skin_type': skin_type,
            'recommendation_count': 0,
            'error': str(e)
        }

def get_skin_type_recommendations(skin_type: str, top_k: int = 5) -> Dict:
    """
    Wrapper function to get skincare recommendations based on skin type
    
    Args:
        skin_type: User's skin type
        top_k: Number of recommendations to return
        
    Returns:
        Dictionary containing recommendations
    """
    global recommendation_system
    
    # Try to initialize if not already done
    if recommendation_system is None:
        if not initialize_recommendation_system():
            return {
                'recommendations': [],
                'total_found': 0,
                'skin_type': skin_type,
                'recommendation_count': 0,
                'error': 'Recommendation system could not be initialized'
            }
    
    try:
        return recommendation_system.get_skin_type_recommendations(
            skin_type,
            top_k
        )
        
    except Exception as e:
        print(f"Error in get_skin_type_recommendations: {e}")
        return {
            'recommendations': [],
            'total_found': 0,
            'skin_type': skin_type,
            'recommendation_count': 0,
            'error': str(e)
        }