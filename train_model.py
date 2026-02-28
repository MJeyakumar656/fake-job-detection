"""
Combined Training Script - Fake Job Detection
This script supports multiple training approaches:
1. SMOTE Oversampling with Ensemble Models
2. DNN vs Random Forest Comparison
"""
import pandas as pd
import numpy as np
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, roc_auc_score, confusion_matrix, 
                             balanced_accuracy_score)
from sklearn.model_selection import StratifiedKFold
import joblib
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import SMOTE for oversampling
try:
    from imblearn.over_sampling import SMOTE, ADASYN, BorderlineSMOTE
    from imblearn.combine import SMOTETomek, SMOTEENN
    print("imbalanced-learn imported successfully")
except ImportError:
    print("Installing imbalanced-learn...")
    os.system("pip install imbalanced-learn")
    from imblearn.over_sampling import SMOTE, ADASYN, BorderlineSMOTE
    from imblearn.combine import SMOTETomek, SMOTEENN

from src.model_trainer import FakeJobDetector
from src.feature_extractor import FeatureExtractor


def load_and_prepare_data():
    """Load and prepare the dataset"""
    print("=" * 60)
    print("STEP 1: Loading Dataset")
    print("=" * 60)
    
    # Load dataset
    df = pd.read_csv('dataset/fake_job_final.csv')
    
    print(f"Dataset loaded successfully!")
    print(f"   Total records: {len(df)}")
    
    # Check label distribution
    print(f"\nLabel Distribution (BEFORE oversampling):")
    print(f"   Genuine Jobs (0): {len(df[df['label'] == 0])} ({len(df[df['label'] == 0])/len(df)*100:.1f}%)")
    print(f"   Fake Jobs (1): {len(df[df['label'] == 1])} ({len(df[df['label'] == 1])/len(df)*100:.1f}%)")
    
    # Handle missing values
    df['text'] = df['text'].fillna('')
    df['label'] = df['label'].fillna(0)
    
    # Clean data - remove empty texts
    df = df[df['text'].str.len() > 50]
    
    print(f"\nData cleaned: {len(df)} records after cleaning")
    
    return df


def prepare_training_data(df, sample_size=5000):
    """Prepare data for training with optional sampling"""
    print("\n" + "=" * 60)
    print("STEP 2: Preparing Training Data")
    print("=" * 60)
    
    # For faster training, we can sample the data
    if len(df) > sample_size:
        print(f"Sampling {sample_size} records for training (full dataset: {len(df)})")
        
        # Stratified sampling to maintain class balance
        df_genuine = df[df['label'] == 0].sample(n=min(sample_size//2, len(df[df['label'] == 0])), random_state=42)
        df_fake = df[df['label'] == 1].sample(n=min(sample_size//2, len(df[df['label'] == 1])), random_state=42)
        df = pd.concat([df_genuine, df_fake])
    
    print(f"   Training samples: {len(df)}")
    
    # Initialize detector
    detector = FakeJobDetector()
    
    # Prepare training data
    X, y = detector.prepare_training_data(df)
    
    print(f"\nTraining data prepared!")
    print(f"   X shape: {X.shape}")
    print(f"   y shape: {y.shape}")
    
    return X, y, detector


def prepare_training_data_comparison(df):
    """Prepare data for DNN vs RF comparison"""
    print("🔄 Preparing training data...")
    
    feature_extractor = FeatureExtractor()
    
    X_text = []
    X_features = []
    y = []
    
    for idx, row in df.iterrows():
        job_data = {
            'description': row.get('text', ''),
            'requirements': row.get('text', ''),
            'company_profile': '',
            'company_domain': '',
            'company_name': '',
            'salary': '',
        }
        
        features, combined_text = feature_extractor.extract_all_features(job_data)
        
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
    tfidf = TfidfVectorizer(max_features=500, min_df=2, max_df=0.8, ngram_range=(1, 2))
    X_tfidf = tfidf.fit_transform(X_text).toarray()
    
    # Combine TF-IDF with engineered features
    X_combined = np.hstack([X_tfidf, X_features])
    
    # Normalize features
    scaler = StandardScaler()
    X_combined = scaler.fit_transform(X_combined)
    
    return X_combined, np.array(y), tfidf, scaler


def apply_smote_oversampling(X, y, method='smote'):
    """Apply SMOTE oversampling to balance the dataset"""
    print(f"\nApplying {method.upper()} oversampling...")
    
    samplers = {
        'smote': SMOTE(random_state=42),
        'adasyn': ADASYN(random_state=42),
        'borderline': BorderlineSMOTE(random_state=42),
        'smote_tomek': SMOTETomek(random_state=42),
        'smote_enn': SMOTEENN(random_state=42),
    }
    
    sampler = samplers.get(method, SMOTE(random_state=42))
    
    try:
        X_resampled, y_resampled = sampler.fit_resample(X, y)
        
        print(f"   Original: {len(y)} samples")
        print(f"   After {method}: {len(y_resampled)} samples")
        print(f"   Class 0 (Genuine): {sum(y_resampled == 0)}")
        print(f"   Class 1 (Fake): {sum(y_resampled == 1)}")
        
        return X_resampled, y_resampled
    except Exception as e:
        print(f"   Error with {method}: {str(e)}")
        return X, y


def train_with_smote(X, y, detector, smote_method='smote'):
    """Train model with SMOTE oversampling"""
    print("\n" + "=" * 60)
    print(f"STEP 3: Training with {smote_method.upper()} Oversampling")
    print("=" * 60)
    
    # Split data FIRST (important: apply SMOTE only to training data)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Original Training set: {X_train.shape[0]} samples")
    print(f"   Validation set: {X_val.shape[0]} samples")
    
    # Apply SMOTE only to training data
    X_train_resampled, y_train_resampled = apply_smote_oversampling(X_train, y_train, smote_method)
    
    # Build model
    input_dim = X_train.shape[1]
    print(f"\nBuilding model with input dimension: {input_dim}")
    detector.build_model(input_dim)
    
    # Train model with class weights for additional balance
    print("\nTraining model with SMOTE + class weights...")
    history = detector.train(X_train_resampled, y_train_resampled, X_val, y_val, epochs=10, batch_size=32)
    
    return detector, history, X_val, y_val


def train_ensemble_models(X, y):
    """Train ensemble of different models"""
    print("\n" + "=" * 60)
    print("STEP 4: Training Ensemble Models")
    print("=" * 60)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Apply SMOTE to training data
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    
    results = {}
    
    # Model 1: Random Forest
    print("\nTraining Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=20, class_weight='balanced', random_state=42, n_jobs=-1)
    rf.fit(X_train_resampled, y_train_resampled)
    y_pred_rf = rf.predict(X_test)
    y_proba_rf = rf.predict_proba(X_test)[:, 1]
    
    results['Random Forest'] = {
        'accuracy': accuracy_score(y_test, y_pred_rf),
        'precision': precision_score(y_test, y_pred_rf),
        'recall': recall_score(y_test, y_pred_rf),
        'f1': f1_score(y_test, y_pred_rf),
        'balanced_accuracy': balanced_accuracy_score(y_test, y_pred_rf),
        'auc': roc_auc_score(y_test, y_proba_rf)
    }
    
    # Model 2: Gradient Boosting
    print("Training Gradient Boosting...")
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
    gb.fit(X_train_resampled, y_train_resampled)
    y_pred_gb = gb.predict(X_test)
    y_proba_gb = gb.predict_proba(X_test)[:, 1]
    
    results['Gradient Boosting'] = {
        'accuracy': accuracy_score(y_test, y_pred_gb),
        'precision': precision_score(y_test, y_pred_gb),
        'recall': recall_score(y_test, y_pred_gb),
        'f1': f1_score(y_test, y_pred_gb),
        'balanced_accuracy': balanced_accuracy_score(y_test, y_pred_gb),
        'auc': roc_auc_score(y_test, y_proba_gb)
    }
    
    # Model 3: Logistic Regression
    print("Training Logistic Regression...")
    lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    lr.fit(X_train_resampled, y_train_resampled)
    y_pred_lr = lr.predict(X_test)
    y_proba_lr = lr.predict_proba(X_test)[:, 1]
    
    results['Logistic Regression'] = {
        'accuracy': accuracy_score(y_test, y_pred_lr),
        'precision': precision_score(y_test, y_pred_lr),
        'recall': recall_score(y_test, y_pred_lr),
        'f1': f1_score(y_test, y_pred_lr),
        'balanced_accuracy': balanced_accuracy_score(y_test, y_pred_lr),
        'auc': roc_auc_score(y_test, y_proba_lr)
    }
    
    return results, X_test, y_test


def evaluate_model(model, X_test, y_test, model_name='Model'):
    """Evaluate model performance"""
    y_pred_proba = model.predict(X_test, verbose=0) if hasattr(model, 'predict') else model.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int).flatten()
    
    return {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0),
        'balanced_accuracy': balanced_accuracy_score(y_test, y_pred),
        'auc': roc_auc_score(y_test, y_pred_proba),
        'confusion_matrix': confusion_matrix(y_test, y_pred)
    }


def print_comparison_table(results):
    """Print comparison table of all models"""
    print("\n" + "=" * 60)
    print("MODEL COMPARISON RESULTS")
    print("=" * 60)
    
    print(f"\n{'Model':<25} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Balanced Acc':<15} {'AUC':<10}")
    print("-" * 100)
    
    for model_name, metrics in results.items():
        print(f"{model_name:<25} {metrics['accuracy']:.4f}      {metrics['precision']:.4f}      {metrics['recall']:.4f}      {metrics['f1']:.4f}      {metrics['balanced_accuracy']:.4f}          {metrics['auc']:.4f}")
    
    # Find best model
    best_model = max(results.items(), key=lambda x: x[1]['balanced_accuracy'])
    print(f"\nBest Model (by Balanced Accuracy): {best_model[0]}")
    print(f"  - Balanced Accuracy: {best_model[1]['balanced_accuracy']:.4f}")
    print(f"  - Recall (Fake Detection): {best_model[1]['recall']:.4f}")


def train_dnn_vs_rf(X, y):
    """Train and compare DNN vs Random Forest"""
    print("\n" + "=" * 60)
    print("TRAINING: DNN vs Random Forest Comparison")
    print("=" * 60)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )
    
    print(f"✓ Training set: {X_train.shape[0]} samples")
    print(f"✓ Validation set: {X_val.shape[0]} samples")
    print(f"✓ Test set: {X_test.shape[0]} samples")
    
    results = {}
    
    # Train DNN
    print("\n[1/2] Training DNN model...")
    detector = FakeJobDetector()
    detector.build_model(X_train.shape[1])
    detector.train(X_train, y_train, X_val, y_val, epochs=50, batch_size=32)
    
    dnn_results = evaluate_model(detector.model, X_test, y_test, 'DNN')
    results['DNN'] = dnn_results
    
    # Train Random Forest
    print("\n[2/2] Training Random Forest model...")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    rf.fit(X_train, y_train)
    
    y_pred_rf = rf.predict(X_test)
    y_proba_rf = rf.predict_proba(X_test)[:, 1]
    
    results['Random Forest'] = {
        'accuracy': accuracy_score(y_test, y_pred_rf),
        'precision': precision_score(y_test, y_pred_rf, zero_division=0),
        'recall': recall_score(y_test, y_pred_rf, zero_division=0),
        'f1': f1_score(y_test, y_pred_rf, zero_division=0),
        'balanced_accuracy': balanced_accuracy_score(y_test, y_pred_rf),
        'auc': roc_auc_score(y_test, y_proba_rf),
        'confusion_matrix': confusion_matrix(y_test, y_pred_rf)
    }
    
    # Print comparison
    print("\n" + "=" * 60)
    print("📊 FINAL COMPARISON: DNN vs Random Forest")
    print("=" * 60)
    print(f"{'Metric':<15} {'DNN':<15} {'Random Forest':<15}")
    print("-" * 45)
    print(f"{'Accuracy':<15} {dnn_results['accuracy']*100:.2f}%{'':<8} {results['Random Forest']['accuracy']*100:.2f}%")
    print(f"{'Precision':<15} {dnn_results['precision']*100:.2f}%{'':<8} {results['Random Forest']['precision']*100:.2f}%")
    print(f"{'Recall':<15} {dnn_results['recall']*100:.2f}%{'':<8} {results['Random Forest']['recall']*100:.2f}%")
    print(f"{'F1-Score':<15} {dnn_results['f1']*100:.2f}%{'':<8} {results['Random Forest']['f1']*100:.2f}%")
    print(f"{'AUC':<15} {dnn_results['auc']*100:.2f}%{'':<8} {results['Random Forest']['auc']*100:.2f}%")
    
    # Save models
    print("\n💾 Saving models...")
    detector.save_model()
    joblib.dump(rf, 'models/random_forest_model.pkl')
    
    return results


def main():
    """Main training pipeline"""
    print("\n" + "=" * 60)
    print("🤖 FAKE JOB DETECTION - COMBINED TRAINING")
    print("=" * 60)
    print("\nSelect training mode:")
    print("1. SMOTE Oversampling + Ensemble Models (Recommended)")
    print("2. DNN vs Random Forest Comparison")
    print("3. Exit")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    try:
        # Load data
        df = load_and_prepare_data()
        
        if choice == '1':
            # SMOTE + Ensemble approach
            X, y, detector = prepare_training_data(df)
            detector, history, X_val, y_val = train_with_smote(X, y, detector, 'smote')
            
            # Evaluate DNN
            print("\n" + "=" * 60)
            print("STEP 5: Evaluating DNN with SMOTE")
            print("=" * 60)
            detector.save_model()
            detector.load_model()
            
            dnn_results = evaluate_model(detector.model, X_val, y_val, 'DNN')
            
            print("\nDNN Results (with SMOTE):")
            print(f"   Accuracy: {dnn_results['accuracy']*100:.2f}%")
            print(f"   Precision: {dnn_results['precision']*100:.2f}%")
            print(f"   Recall: {dnn_results['recall']*100:.2f}%")
            print(f"   F1-Score: {dnn_results['f1']*100:.2f}%")
            print(f"   Balanced Accuracy: {dnn_results['balanced_accuracy']*100:.2f}%")
            print(f"   AUC: {dnn_results['auc']:.4f}")
            
            # Train ensemble models
            ensemble_results, X_test, y_test = train_ensemble_models(X, y)
            ensemble_results['DNN (SMOTE)'] = dnn_results
            
            print_comparison_table(ensemble_results)
            
        elif choice == '2':
            # DNN vs RF comparison
            X, y, tfidf, scaler = prepare_training_data_comparison(df)
            results = train_dnn_vs_rf(X, y)
            
        else:
            print("Exiting...")
            return
            
        print("\n" + "=" * 60)
        print("✅ TRAINING COMPLETED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nTraining failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
    sys.exit(0)
