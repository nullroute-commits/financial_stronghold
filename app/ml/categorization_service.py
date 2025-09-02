"""
Machine Learning service for transaction categorization.
Provides AI-powered transaction categorization with learning capabilities.

Created by Team Tau (Machine Learning & Analytics) - Sprint 8
"""

import logging
import re
import pickle
import os
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
import numpy as np

from ..models.import_models import TransactionCategory, MLModel
from ..django_models import Transaction

logger = logging.getLogger('ml.categorization')


class TransactionCategorizationService:
    """ML-powered transaction categorization service."""
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.categories = {}
        self.model_version = "1.0.0"
        self.confidence_threshold = 0.7
        
        # Load or create model
        self._load_or_create_model()
    
    def categorize_transaction(self, description, amount=None, merchant=None):
        """
        Categorize a single transaction.
        
        Args:
            description: Transaction description
            amount: Transaction amount (optional)
            merchant: Merchant name (optional)
            
        Returns:
            dict: Categorization result with category and confidence
        """
        
        if not self.model:
            return self._get_default_categorization(description, amount)
        
        try:
            # Prepare features
            features = self._extract_features(description, amount, merchant)
            
            # Predict category
            probabilities = self.model.predict_proba([features])[0]
            predicted_class = self.model.predict([features])[0]
            confidence = max(probabilities)
            
            # Get category name
            category_name = self.model.classes_[np.argmax(probabilities)]
            
            return {
                'category': category_name,
                'confidence': float(confidence),
                'is_confident': confidence >= self.confidence_threshold,
                'alternatives': self._get_alternative_categories(probabilities)
            }
            
        except Exception as e:
            logger.error(f"Categorization failed: {str(e)}")
            return self._get_default_categorization(description, amount)
    
    def categorize_batch(self, transactions):
        """
        Categorize multiple transactions efficiently.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            list: List of categorization results
        """
        
        if not self.model:
            return [self._get_default_categorization(t.get('description', ''), t.get('amount')) 
                   for t in transactions]
        
        try:
            # Extract features for all transactions
            features_list = []
            for transaction in transactions:
                features = self._extract_features(
                    transaction.get('description', ''),
                    transaction.get('amount'),
                    transaction.get('merchant')
                )
                features_list.append(features)
            
            # Batch prediction
            probabilities = self.model.predict_proba(features_list)
            predictions = self.model.predict(features_list)
            
            results = []
            for i, transaction in enumerate(transactions):
                confidence = max(probabilities[i])
                category_name = predictions[i]
                
                results.append({
                    'category': category_name,
                    'confidence': float(confidence),
                    'is_confident': confidence >= self.confidence_threshold,
                    'alternatives': self._get_alternative_categories(probabilities[i])
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Batch categorization failed: {str(e)}")
            return [self._get_default_categorization(t.get('description', ''), t.get('amount')) 
                   for t in transactions]
    
    def train_model(self, training_data=None):
        """
        Train or retrain the categorization model.
        
        Args:
            training_data: Optional custom training data
        """
        
        try:
            # Get training data
            if training_data is None:
                training_data = self._prepare_training_data()
            
            if len(training_data) < 50:  # Minimum training data
                logger.warning("Insufficient training data for ML model")
                return False
            
            # Prepare features and labels
            X = [self._extract_features(row['description'], row.get('amount'), row.get('merchant')) 
                 for row in training_data]
            y = [row['category'] for row in training_data]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Create and train model
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            self.model = Pipeline([
                ('tfidf', self.vectorizer),
                ('classifier', MultinomialNB(alpha=1.0))
            ])
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            self._save_model(accuracy, len(training_data))
            
            logger.info(f"Model trained successfully", extra={
                'accuracy': accuracy,
                'training_size': len(training_data),
                'test_size': len(X_test)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return False
    
    def _extract_features(self, description, amount=None, merchant=None):
        """Extract features for ML model."""
        
        features = []
        
        # Text features from description
        if description:
            # Clean and normalize description
            clean_desc = self._clean_description(description)
            features.append(clean_desc)
        else:
            features.append('')
        
        # Amount-based features
        if amount is not None:
            try:
                amount_value = float(amount)
                
                # Amount range features
                if amount_value < 0:
                    features.append('expense')
                else:
                    features.append('income')
                
                # Amount magnitude features
                abs_amount = abs(amount_value)
                if abs_amount < 10:
                    features.append('small_amount')
                elif abs_amount < 100:
                    features.append('medium_amount')
                elif abs_amount < 1000:
                    features.append('large_amount')
                else:
                    features.append('very_large_amount')
                    
            except (ValueError, TypeError):
                pass
        
        # Merchant features
        if merchant:
            clean_merchant = self._clean_description(merchant)
            features.append(f"merchant_{clean_merchant}")
        
        return ' '.join(features)
    
    def _clean_description(self, description):
        """Clean transaction description for feature extraction."""
        
        if not description:
            return ''
        
        # Convert to lowercase
        clean = description.lower()
        
        # Remove special characters and numbers
        clean = re.sub(r'[^a-zA-Z\s]', ' ', clean)
        
        # Remove extra whitespace
        clean = ' '.join(clean.split())
        
        return clean
    
    def _prepare_training_data(self):
        """Prepare training data from existing transactions."""
        
        # Get existing transactions with categories
        transactions = Transaction.objects.filter(
            category__isnull=False
        ).exclude(category='').values(
            'description', 'amount', 'category'
        )
        
        training_data = []
        for transaction in transactions:
            training_data.append({
                'description': transaction['description'],
                'amount': transaction['amount'],
                'category': transaction['category'],
                'merchant': self._extract_merchant_from_description(transaction['description'])
            })
        
        # Add default categories if no training data
        if not training_data:
            training_data = self._get_default_training_data()
        
        return training_data
    
    def _get_default_training_data(self):
        """Get default training data for initial model."""
        
        return [
            # Income categories
            {'description': 'salary payment', 'amount': 5000, 'category': 'salary', 'merchant': 'employer'},
            {'description': 'freelance payment', 'amount': 1500, 'category': 'freelance', 'merchant': 'client'},
            {'description': 'interest payment', 'amount': 25, 'category': 'interest', 'merchant': 'bank'},
            
            # Food categories
            {'description': 'grocery store purchase', 'amount': -85, 'category': 'groceries', 'merchant': 'supermarket'},
            {'description': 'restaurant dinner', 'amount': -45, 'category': 'dining', 'merchant': 'restaurant'},
            {'description': 'coffee shop', 'amount': -5, 'category': 'dining', 'merchant': 'cafe'},
            
            # Transportation
            {'description': 'gas station', 'amount': -60, 'category': 'transportation', 'merchant': 'gas_station'},
            {'description': 'uber ride', 'amount': -25, 'category': 'transportation', 'merchant': 'rideshare'},
            {'description': 'public transit', 'amount': -3, 'category': 'transportation', 'merchant': 'transit'},
            
            # Utilities
            {'description': 'electric bill', 'amount': -120, 'category': 'utilities', 'merchant': 'utility_company'},
            {'description': 'internet service', 'amount': -80, 'category': 'utilities', 'merchant': 'isp'},
            {'description': 'phone bill', 'amount': -50, 'category': 'utilities', 'merchant': 'telecom'},
            
            # Entertainment
            {'description': 'movie tickets', 'amount': -25, 'category': 'entertainment', 'merchant': 'cinema'},
            {'description': 'streaming service', 'amount': -15, 'category': 'entertainment', 'merchant': 'streaming'},
            {'description': 'concert tickets', 'amount': -100, 'category': 'entertainment', 'merchant': 'venue'},
            
            # Shopping
            {'description': 'online purchase', 'amount': -75, 'category': 'shopping', 'merchant': 'ecommerce'},
            {'description': 'clothing store', 'amount': -150, 'category': 'shopping', 'merchant': 'retail'},
            {'description': 'electronics store', 'amount': -300, 'category': 'shopping', 'merchant': 'electronics'},
            
            # Healthcare
            {'description': 'doctor visit', 'amount': -200, 'category': 'healthcare', 'merchant': 'medical'},
            {'description': 'pharmacy', 'amount': -30, 'category': 'healthcare', 'merchant': 'pharmacy'},
            {'description': 'dental checkup', 'amount': -150, 'category': 'healthcare', 'merchant': 'dental'},
        ]
    
    def _extract_merchant_from_description(self, description):
        """Extract merchant name from transaction description."""
        
        if not description:
            return None
        
        # Common merchant patterns
        merchant_patterns = [
            r'(\w+)\s+store',
            r'(\w+)\s+market',
            r'(\w+)\s+restaurant',
            r'(\w+)\s+cafe',
            r'(\w+)\s+gas',
            r'(\w+)\s+pharmacy',
        ]
        
        description_lower = description.lower()
        
        for pattern in merchant_patterns:
            match = re.search(pattern, description_lower)
            if match:
                return match.group(1)
        
        # Return first word as potential merchant
        words = description.split()
        return words[0] if words else None
    
    def _get_default_categorization(self, description, amount):
        """Get default categorization when ML model is not available."""
        
        # Simple rule-based categorization
        if amount is not None and float(amount) > 0:
            category = 'income'
        else:
            # Basic keyword matching for expenses
            description_lower = description.lower() if description else ''
            
            if any(word in description_lower for word in ['grocery', 'supermarket', 'food']):
                category = 'groceries'
            elif any(word in description_lower for word in ['gas', 'fuel', 'uber', 'taxi']):
                category = 'transportation'
            elif any(word in description_lower for word in ['restaurant', 'cafe', 'dining']):
                category = 'dining'
            elif any(word in description_lower for word in ['electric', 'utility', 'phone', 'internet']):
                category = 'utilities'
            elif any(word in description_lower for word in ['store', 'shop', 'purchase']):
                category = 'shopping'
            else:
                category = 'other'
        
        return {
            'category': category,
            'confidence': 0.5,  # Low confidence for rule-based
            'is_confident': False,
            'alternatives': []
        }
    
    def _get_alternative_categories(self, probabilities):
        """Get alternative category suggestions."""
        
        if not hasattr(self.model, 'classes_'):
            return []
        
        # Get top 3 alternatives
        top_indices = np.argsort(probabilities)[-3:][::-1]
        alternatives = []
        
        for idx in top_indices[1:]:  # Skip the top prediction
            if probabilities[idx] > 0.1:  # Only include reasonable alternatives
                alternatives.append({
                    'category': self.model.classes_[idx],
                    'confidence': float(probabilities[idx])
                })
        
        return alternatives
    
    def _load_or_create_model(self):
        """Load existing model or create new one."""
        
        try:
            # Try to load active model
            active_model = MLModel.objects.filter(
                model_type=MLModel.ModelType.CATEGORIZATION,
                is_active=True
            ).first()
            
            if active_model and os.path.exists(active_model.model_file_path):
                with open(active_model.model_file_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['model']
                    self.vectorizer = model_data.get('vectorizer')
                    self.confidence_threshold = active_model.performance_metrics.get('confidence_threshold', 0.7)
                
                logger.info(f"Loaded ML model: {active_model.name} v{active_model.version}")
                return
                
        except Exception as e:
            logger.warning(f"Failed to load existing model: {str(e)}")
        
        # Create and train new model
        logger.info("Creating new categorization model")
        self.train_model()
    
    def _save_model(self, accuracy, training_size):
        """Save trained model to database and file system."""
        
        try:
            # Create model file path
            model_dir = os.path.join(settings.MEDIA_ROOT, 'ml_models')
            os.makedirs(model_dir, exist_ok=True)
            
            model_filename = f"categorization_v{self.model_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            model_file_path = os.path.join(model_dir, model_filename)
            
            # Save model to file
            model_data = {
                'model': self.model,
                'vectorizer': self.vectorizer,
                'version': self.model_version,
                'training_date': datetime.now().isoformat()
            }
            
            with open(model_file_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            # Save model metadata to database
            ml_model = MLModel.objects.create(
                name=f"Transaction Categorization",
                model_type=MLModel.ModelType.CATEGORIZATION,
                version=self.model_version,
                accuracy_score=accuracy,
                training_data_size=training_size,
                features_used=['description', 'amount', 'merchant'],
                model_file_path=model_file_path,
                model_size_bytes=os.path.getsize(model_file_path),
                is_active=True,
                is_production_ready=accuracy > 0.7,
                performance_metrics={
                    'accuracy': accuracy,
                    'confidence_threshold': self.confidence_threshold,
                    'training_date': datetime.now().isoformat()
                },
                last_training_date=timezone.now()
            )
            
            # Deactivate old models
            MLModel.objects.filter(
                model_type=MLModel.ModelType.CATEGORIZATION,
                is_active=True
            ).exclude(id=ml_model.id).update(is_active=False)
            
            logger.info(f"Model saved successfully", extra={
                'model_id': str(ml_model.id),
                'accuracy': accuracy,
                'file_path': model_file_path
            })
            
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
    
    def get_model_performance(self):
        """Get current model performance metrics."""
        
        try:
            active_model = MLModel.objects.filter(
                model_type=MLModel.ModelType.CATEGORIZATION,
                is_active=True
            ).first()
            
            if active_model:
                return {
                    'model_name': active_model.name,
                    'version': active_model.version,
                    'accuracy': active_model.accuracy_score,
                    'training_size': active_model.training_data_size,
                    'last_training': active_model.last_training_date.isoformat() if active_model.last_training_date else None,
                    'usage_count': active_model.usage_count,
                    'is_production_ready': active_model.is_production_ready
                }
            
            return {
                'model_name': 'Default Rule-Based',
                'version': '1.0.0',
                'accuracy': 0.5,
                'training_size': 0,
                'is_production_ready': False
            }
            
        except Exception as e:
            logger.error(f"Failed to get model performance: {str(e)}")
            return {}
    
    def learn_from_correction(self, description, amount, correct_category, predicted_category):
        """Learn from user corrections to improve model."""
        
        try:
            # Log correction for future training
            logger.info("User correction received", extra={
                'description': description[:100],
                'predicted_category': predicted_category,
                'correct_category': correct_category,
                'amount': float(amount) if amount else None
            })
            
            # In a production system, this would:
            # 1. Store correction in training database
            # 2. Trigger incremental learning
            # 3. Update model confidence scores
            # 4. Schedule model retraining if enough corrections
            
            # For now, just log the correction
            return True
            
        except Exception as e:
            logger.error(f"Failed to process user correction: {str(e)}")
            return False


# Global categorization service instance
categorization_service = TransactionCategorizationService()


def get_categorization_service():
    """Get the global categorization service instance."""
    return categorization_service