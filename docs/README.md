# Fake Job Detection System

An AI-powered system to detect fraudulent job postings using Deep Learning and NLP analysis.

## Project Overview

This project implements a deep learning-based approach to automatically detect fake job postings from online recruitment platforms. The system uses Deep Neural Networks (DNN) combined with Natural Language Processing (NLP) techniques to classify job postings as real or fraudulent.

## Project Structure

```
.
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── routes.py             # API routes and endpoints
├── train_model.py        # Model training script
├── requirements.txt      # Python dependencies
├── dataset/              # Training and test data (17,880 jobs)
├── models/               # Trained model files
│   ├── fake_job_detector.h5
│   ├── best_dnn_model.h5
│   ├── random_forest_model.pkl
│   ├── tfidf_vectorizer.pkl
│   └── scaler.pkl
├── src/                  # Source code modules
│   ├── analyzer.py       # Main analyzer
│   ├── feature_extractor.py
│   ├── model_trainer.py  # DNN model training
│   ├── utils.py
│   └── scrapers/        # Web scrapers
│       ├── linkedin_scraper.py
│       ├── naukri_scraper.py
│       ├── indeed_scraper.py
│       └── internshala_scraper.py
├── utils/                # Utility modules
│   ├── domain_check.py
│   ├── nlp_analyzer.py
│   ├── red_flags.py
│   ├── text_cleaner.py
│   └── company_extractor.py
├── templates/            # HTML templates (index.html, result.html)
├── static/               # CSS, JS, and static assets
│   ├── css/style.css
│   └── js/script.js
└── docs/                 # Documentation
```

## Features

- Job posting analysis for authenticity detection
- Red flag detection in suspicious job postings
- Company domain verification
- Web scraping from multiple job portals:
  - LinkedIn
  - Naukri
  - Indeed
  - Internshala
- NLP-based feature extraction (TF-IDF + 14 engineered features)
- Real-time prediction with confidence scores
- Dual model support: DNN and Random Forest

## Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- Flask Framework

### Machine Learning & Deep Learning
- TensorFlow/Keras (Deep Neural Network)
- Scikit-learn (Random Forest)
- TF-IDF Vectorization
- SMOTE (Class Imbalance Handling)

### Web Scraping
- BeautifulSoup
- Requests

## Model Architecture

### Deep Neural Network (DNN)
- Input Layer: 514 features
- Dense Layer 1: 512 neurons (ReLU + BatchNorm + Dropout 0.3)
- Dense Layer 2: 256 neurons (ReLU + BatchNorm + Dropout 0.3)
- Dense Layer 3: 128 neurons (ReLU + BatchNorm + Dropout 0.2)
- Dense Layer 4: 64 neurons (ReLU + Dropout 0.2)
- Output Layer: 1 neuron (Sigmoid)

Total Parameters: 439,809

## Dataset

- Source: Kaggle Fake Job Postings Dataset
- Size: 17,880 job postings
- Features: 18 columns
- Class Distribution:
  - Genuine Jobs: 17,016 (95.16%)
  - Fake Jobs: 866 (4.84%)

## Experimental Results

### DNN Model Performance (Test Set)
| Metric | Value |
|--------|-------|
| Accuracy | 91.53% |
| Precision | 82.22% |
| Recall | 85.55% |
| AUC | 96.60% |

### DNN with SMOTE
| Metric | Value |
|--------|-------|
| Accuracy | 91.83% |
| Balanced Accuracy | 89.40% |
| Recall | 84.39% |
| AUC | 0.9560 |

## Setup

1. Install dependencies:
   
```
bash
   pip install -r requirements.txt
   
```

2. Run the application:
   
```
bash
   python app.py
   
```

3. Open browser and navigate to:
   
```
   http://localhost:5000
   
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/analyze` - Analyze job posting
- `GET /api/supported-portals` - List supported job portals

## Future Enhancements

- Integrate BERT/Transformer models for better NLP
- Add more job portals for wider coverage
- Browser extension for automatic verification
- Mobile application development
- Multi-language job detection support

## License

[Your License Here]
