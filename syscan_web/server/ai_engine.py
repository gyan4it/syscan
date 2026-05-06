"""
AI Engine for SysCan Phase 5.
Uses TensorFlow to predict file deletion recommendations.
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
import json
from datetime import datetime

class AIDeletionEngine:
    """AI-powered file deletion recommendation system."""
    
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ai_model.keras')
    FEATURES = ['size_gb', 'file_age_days', 'access_frequency', 'file_type_score']
    
    def __init__(self):
        self.model = None
        self.load_or_create_model()
    
    def load_or_create_model(self):
        """Load existing model or create a new one."""
        if os.path.exists(self.MODEL_PATH):
            try:
                self.model = keras.models.load_model(self.MODEL_PATH)
                print("AI: Loaded existing model")
            except:
                self.create_model()
        else:
            self.create_model()
    
    def create_model(self):
        """Create a simple neural network for deletion prediction."""
        self.model = keras.Sequential([
            keras.layers.Dense(64, activation='relu', input_shape=(4,)),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')  # Output: 0-1 (delete probability)
        ])
        
        self.model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        print("AI: Created new model")
    
    def extract_features(self, file_path, file_size_bytes, access_time=None):
        """Extract features from a file for AI prediction."""
        # Feature 1: Size in GB
        size_gb = file_size_bytes / (1024**3)
        
        # Feature 2: File age in days
        if access_time:
            age_days = (datetime.now() - datetime.fromtimestamp(access_time)).days
        else:
            try:
                age_days = (datetime.now() - datetime.fromtimestamp(os.path.getatime(file_path))).days
            except:
                age_days = 365  # Default to 1 year
        
        # Feature 3: Access frequency (simulated)
        # In production: track actual access patterns
        access_freq = max(0, 100 - age_days) / 100  # Higher = more recent access
        
        # Feature 4: File type score (0-1)
        ext = os.path.splitext(file_path)[1].lower()
        type_scores = {
            '.tmp': 0.9, '.temp': 0.9, '.log': 0.7, '.cache': 0.8,
            '.mp4': 0.2, '.jpg': 0.3, '.doc': 0.1, '.pdf': 0.1
        }
        type_score = type_scores.get(ext, 0.5)
        
        return np.array([[size_gb, age_days, access_freq, type_score]])
    
    def predict_deletion(self, file_path, file_size_bytes, access_time=None):
        """Predict if a file should be deleted (returns probability 0-1)."""
        if not self.model:
            return 0.5  # Neutral if no model
        
        features = self.extract_features(file_path, file_size_bytes, access_time)
        
        try:
            prediction = self.model.predict(features, verbose=0)
            return float(prediction[0][0])
        except:
            return 0.5
    
    def train(self, training_data, epochs=10):
        """Train the model with labeled data.
        
        Args:
            training_data: List of (file_path, file_size, access_time, should_delete)
        """
        if not training_data:
            print("AI: No training data provided")
            return
        
        X = []
        y = []
        
        for file_path, size, access_time, should_delete in training_data:
            features = self.extract_features(file_path, size, access_time)
            X.append(features[0])
            y.append(1 if should_delete else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"AI: Training on {len(X)} samples...")
        history = self.model.fit(X, y, epochs=epochs, validation_split=0.2, verbose=0)
        
        # Save model
        self.model.save(self.MODEL_PATH)
        print("AI: Model saved")
        
        return history
    
    def get_recommendation(self, file_path, file_size_bytes):
        """Get human-readable recommendation based on AI prediction."""
        probability = self.predict_deletion(file_path, file_size_bytes)
        
        if probability >= 0.8:
            return "Strongly Recommended to Delete", "5★", "AI Prediction"
        elif probability >= 0.6:
            return "Recommended to Delete", "4★", "AI Prediction"
        elif probability >= 0.4:
            return "Maybe Delete", "3★", "AI Prediction"
        elif probability >= 0.2:
            return "Keep (Low Priority)", "2★", "AI Prediction"
        else:
            return "Keep (Important)", "1★", "AI Prediction"


# Singleton instance
_ai_engine = None

def get_ai_engine():
    """Get or create AI engine singleton."""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIDeletionEngine()
    return _ai_engine
