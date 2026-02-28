import pandas as pd
from src.model_trainer import FakeJobDetector
from src.data_downloader import DatasetDownloader

def main():
    """Main training script"""
    
    print("=" * 60)
    print("🤖 FAKE JOB DETECTION MODEL TRAINING")
    print("=" * 60)
    
    # Step 1: Download and prepare dataset
    print("\n[1/4] Downloading dataset...")
    downloader = DatasetDownloader()
    df = downloader.download_kaggle_dataset()
    
    if df is None:
        print("❌ Please download dataset first!")
        return
    
    print(f"✅ Dataset loaded: {len(df)} records")
    
    # Step 2: Prepare data
    print("\n[2/4] Preparing data...")
    df = downloader.prepare_dataset(df)
    downloader.save_processed_data(df)
    
    # Check dataset
    print(f"✓ Genuine jobs: {(df['is_fake'] == 0).sum()}")
    print(f"✓ Fake jobs: {(df['is_fake'] == 1).sum()}")
    
    # Step 3: Initialize model and prepare training data
    print("\n[3/4] Initializing model and preparing training data...")
    detector = FakeJobDetector()
    
    X, y = detector.prepare_training_data(df)
    print(f"✓ Features shape: {X.shape}")
    print(f"✓ Labels shape: {y.shape}")
    
    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )
    
    print(f"✓ Training set: {X_train.shape[0]} samples")
    print(f"✓ Validation set: {X_val.shape[0]} samples")
    print(f"✓ Test set: {X_test.shape[0]} samples")
    
    # Step 4: Build and train model
    print("\n[4/4] Building and training model...")
    detector.build_model(X_train.shape[1])
    detector.train(X_train, y_train, X_val, y_val, epochs=50, batch_size=32)
    
    # Evaluate on test set
    print("\n📊 Evaluating on test set...")
    test_loss, test_accuracy, test_auc, test_precision, test_recall = detector.model.evaluate(X_test, y_test)
    
    print(f"✓ Test Accuracy: {test_accuracy:.4f}")
    print(f"✓ Test AUC: {test_auc:.4f}")
    print(f"✓ Test Precision: {test_precision:.4f}")
    print(f"✓ Test Recall: {test_recall:.4f}")
    
    # Save model
    detector.save_model()
    
    print("\n" + "=" * 60)
    print("✅ MODEL TRAINING COMPLETED!")
    print("=" * 60)

if __name__ == '__main__':
    main()
