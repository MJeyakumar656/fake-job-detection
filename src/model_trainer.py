import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import joblib
from pathlib import Path
from src.feature_extractor import FeatureExtractor

class FakeJobDetector:
    """Deep Learning Model for Fake Job Detection"""
    
    def __init__(self, model_path='models'):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)
        
        self.model = None
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=500,
            min_df=2,
            max_df=0.8,
            ngram_range=(1, 2)
        )
        self.scaler = None
        self.feature_extractor = FeatureExtractor()
    
    def prepare_training_data(self, df):
        """Prepare data for training"""
        print("🔄 Preparing training data...")
        
        X_text = []
        X_features = []
        y = []
        
        for idx, row in df.iterrows():
            # Use 'text' column as description (our dataset format)
            job_data = {
                'description': row.get('text', ''),
                'requirements': row.get('text', ''),  # Use text for requirements too
                'company_profile': '',
                'company_domain': '',
                'company_name': '',
                'salary': '',
            }
            
            # Extract features
            features, combined_text = self.feature_extractor.extract_all_features(job_data)
            
            X_text.append(combined_text)
            X_features.append([
                features['text_length'],
                features['word_count'],
                features['avg_word_length'],
                features['unique_word_ratio'],
                features['uppercase_ratio'],
                features['digit_ratio'],
                features['spelling_errors'],
                features['grammar_score'],
                features['sentence_count'],
                features['domain_exists'],
                features['domain_length'],
                features['has_suspicious_domain'],
                features['company_name_length'],
                features['red_flag_count'],
            ])
            
            y.append(row['label'])
            
            if (idx + 1) % 100 == 0:
                print(f"  ✓ Processed {idx + 1} records")
        
        # Vectorize text using TF-IDF
        print("📊 Vectorizing text with TF-IDF...")
        X_tfidf = self.tfidf_vectorizer.fit_transform(X_text).toarray()
        
        # Combine TF-IDF with engineered features
        X_combined = np.hstack([X_tfidf, X_features])
        
        # Normalize features
        self.scaler = StandardScaler()
        X_combined = self.scaler.fit_transform(X_combined)
        
        return X_combined, np.array(y)
    
    def build_model(self, input_dim):
        """Build deep learning model"""
        print("🏗️ Building neural network...")
        
        self.model = Sequential([
            layers.Input(shape=(input_dim,)),
            
            # First block
            layers.Dense(512, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Second block
            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Third block
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            # Fourth block
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            
            # Output layer
            layers.Dense(1, activation='sigmoid')
        ])
        
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC(), keras.metrics.Precision(), keras.metrics.Recall()]
        )
        
        self.model.summary()
        return self.model
    
    def train(self, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
        """Train the model"""
        print("\n🚀 Training model...")
        
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True,
                verbose=1
            ),
            ModelCheckpoint(
                str(self.model_path / 'best_model.h5'),
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            )
        ]
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    def save_model(self):
        """Save trained model and preprocessors"""
        print("💾 Saving model...")
        
        self.model.save(str(self.model_path / 'fake_job_detector.h5'))
        joblib.dump(self.tfidf_vectorizer, str(self.model_path / 'tfidf_vectorizer.pkl'))
        joblib.dump(self.scaler, str(self.model_path / 'scaler.pkl'))
        
        print(f"✅ Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model and preprocessors"""
        print("📂 Loading model...")
        
        self.model = keras.models.load_model(str(self.model_path / 'fake_job_detector.h5'))
        self.tfidf_vectorizer = joblib.load(str(self.model_path / 'tfidf_vectorizer.pkl'))
        self.scaler = joblib.load(str(self.model_path / 'scaler.pkl'))
        
        print("✅ Model loaded successfully")
    
    def predict(self, job_data):
        """Predict if job is fake"""
        # Extract features
        features, combined_text = self.feature_extractor.extract_all_features(job_data)
        
        # Vectorize text
        X_tfidf = self.tfidf_vectorizer.transform([combined_text]).toarray()
        
        # Combine with features
        X_features = np.array([[
            features['text_length'],
            features['word_count'],
            features['avg_word_length'],
            features['unique_word_ratio'],
            features['uppercase_ratio'],
            features['digit_ratio'],
            features['spelling_errors'],
            features['grammar_score'],
            features['sentence_count'],
            features['domain_exists'],
            features['domain_length'],
            features['has_suspicious_domain'],
            features['company_name_length'],
            features['red_flag_count'],
        ]])
        
        X_combined = np.hstack([X_tfidf, X_features])
        X_combined = self.scaler.transform(X_combined)
        
        # Get prediction
        prediction = self.model.predict(X_combined, verbose=0)[0][0]
        
        return {
            'confidence': float(prediction),
            'is_fake': prediction > 0.5,
            'red_flags': features['red_flags'],
            'red_flag_count': features['red_flag_count'],
        }