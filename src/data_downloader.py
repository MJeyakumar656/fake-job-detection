import os
import pandas as pd
import requests
from pathlib import Path

class DatasetDownloader:
    """Download fake job detection datasets"""
    
    def __init__(self):
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
    
    def download_kaggle_dataset(self):
        """Download from Kaggle fake job detection dataset"""
        print("📥 Downloading dataset from Kaggle...")
        
        # Manual download: https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction
        # Place CSV in data/ folder
        
        dataset_path = self.data_dir / 'fake_job_postings.csv'
        
        if not dataset_path.exists():
            print("⚠️ Please download dataset from Kaggle and place in 'data/' folder")
            print("📌 URL: https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction")
            return None
        
        return pd.read_csv(dataset_path)
    
    def prepare_dataset(self, df):
        """Prepare and clean dataset"""
        print("🧹 Preparing dataset...")
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        df['description'] = df['description'].fillna('')
        df['company_profile'] = df['company_profile'].fillna('')
        df['requirements'] = df['requirements'].fillna('')
        
        # Create target variable (0 = genuine, 1 = fake)
        df['is_fake'] = df['fraudulent']
        
        # Select relevant columns
        relevant_cols = [
            'title', 'company_profile', 'description', 'requirements',
            'salary_range', 'location', 'is_fake'
        ]
        
        df = df[relevant_cols]
        
        return df
    
    def save_processed_data(self, df, filename='processed_jobs.csv'):
        """Save processed dataset"""
        output_path = self.data_dir / filename
        df.to_csv(output_path, index=False)
        print(f"✅ Dataset saved to {output_path}")
        return output_path

# Usage
if __name__ == '__main__':
    downloader = DatasetDownloader()
    df = downloader.download_kaggle_dataset()
    if df is not None:
        df_processed = downloader.prepare_dataset(df)
        downloader.save_processed_data(df_processed)
        print(f"✅ Total records: {len(df_processed)}")