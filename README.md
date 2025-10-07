# Fake News Detection System

A machine learning system for detecting fake news using Natural Language Processing and tree-based/transformer-based models. The project includes model training, evaluation, a FastAPI server for predictions, and a browser extension for real-time fake news detection.

## 🎯 Features

- **Multiple Model Support**: Random Forest and RoBERTa-based classifiers
- **Feature Engineering**: TF-IDF features, manual features (speaker credibility, party affiliation, etc.)
- **REST API**: FastAPI server for real-time predictions
- **Browser Extension**: Chrome/Firefox extension for detecting fake news on web pages
- **MLflow Integration**: Experiment tracking and model versioning
- **Data Quality**: Great Expectations for data validation
- **Docker Support**: Containerized deployment options

## 🏗️ Project Structure

```
fake_news/
├── fake_news/
│   ├── model/
│   │   ├── base.py                    # Base model interface
│   │   ├── transformer_based.py       # RoBERTa model implementation
│   │   └── tree_based.py              # Random Forest model implementation
│   ├── server/
│   │   └── main.py                    # FastAPI server
│   ├── utils/
│   │   ├── constants.py               # Constants and mappings
│   │   ├── dataloaders.py             # Data loading utilities
│   │   ├── features.py                # Feature extraction and engineering
│   │   └── reader.py                  # Data readers
│   └── train.py                       # Model training script
├── config/
│   ├── random_forest.json             # Random Forest configuration
│   └── roberta.json                   # RoBERTa configuration
├── data/
│   ├── raw/                           # Raw datasets (DVC tracked)
│   └── processed/                     # Processed datasets
├── deploy/
│   ├── Dockerfile                     # Training container
│   ├── Dockerfile.serve               # Serving container
│   └── extension/                     # Browser extension files
├── scripts/
│   ├── normalize_and_clean_data.py    # Data preprocessing
│   └── compute_credit_bins.py         # Feature binning
├── tests/
│   ├── great_expectations/            # Data validation
│   ├── test_features.py               # Feature tests
│   └── test_model.py                  # Model tests
└── notebooks/
    ├── data_analysis.ipynb            # Exploratory data analysis
    └── error_analysis.ipynb           # Model error analysis
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip
- Docker (optional, for containerized deployment)
- DVC (for data versioning)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fake-news-detection
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Pull data with DVC**
   ```bash
   dvc pull
   ```

### Data Preprocessing

Process raw data and create cleaned datasets:

```bash
python scripts/normalize_and_clean_data.py \
  --train-data-path data/raw/train2.tsv \
  --val-data-path data/raw/val2.tsv \
  --test-data-path data/raw/test2.tsv \
  --output-dir data/processed
```

### Training Models

#### Random Forest Model

```bash
python fake_news/train.py --config-file config/random_forest.json
```

#### RoBERTa Model

```bash
python fake_news/train.py --config-file config/roberta.json
```

### Running the API Server

```bash
uvicorn fake_news.server.main:app --host 0.0.0.0 --port 8000 --env-file .env
```

The API will be available at `http://localhost:8000`

#### API Endpoints

**POST /api/predict-fakeness**
```json
Request:
{
  "text": "Statement to verify"
}

Response:
{
  "label": 0,
  "probs": [0.85, 0.15]
}
```

## 🐳 Docker Deployment

### Build Training Container

```bash
docker build -f deploy/Dockerfile -t fake-news-trainer .
```

### Build Serving Container

```bash
docker build -f deploy/Dockerfile.serve -t fake-news-server .
docker run -p 8000:8000 -e MODEL_DIR=/models fake-news-server
```

## 🔧 Browser Extension

The browser extension allows real-time fake news detection while browsing.

### Installation

1. Navigate to `deploy/extension/`
2. Open Chrome/Firefox extension settings
3. Enable "Developer mode"
4. Click "Load unpacked" and select the `deploy/extension/` directory

### Usage

Click the extension icon on any page with text to analyze statements for fake news.

## 📊 Model Features

The system uses a combination of features:

### Text Features
- **TF-IDF**: N-gram features from statements
- **Statement Length**: Character and word counts

### Speaker Credibility Features
- Historical accuracy counts (barely true, false, half true, mostly true, pants on fire)
- Speaker title and affiliation
- State information
- Party affiliation

### Feature Engineering
- Credit score binning for credibility metrics
- Canonical mappings for speaker titles and states
- Party affiliation normalization

## 🧪 Testing

Run all tests:

```bash
pytest tests/
```

Run data validation:

```bash
python tests/great_expectations/validate_data.py
```

## 📈 MLflow Tracking

View experiment results:

```bash
mlflow ui
```

Navigate to `http://localhost:5000` to view tracked experiments, metrics, and models.

## 🔬 Model Architectures

### Random Forest
- Feature extraction using TF-IDF + manual features
- Sklearn RandomForestClassifier
- Optimized hyperparameters via configuration

### RoBERTa
- Pre-trained RoBERTa base model
- Fine-tuned on fake news dataset
- Transformer-based contextualized embeddings

## 📝 Configuration Files

### `config/random_forest.json`
```json
{
  "model": "random_forest",
  "train_data_path": "data/processed/cleaned_train_data.json",
  "val_data_path": "data/processed/cleaned_val_data.json",
  "test_data_path": "data/processed/cleaned_test_data.json",
  "model_output_path": "models/random_forest",
  "featurizer_output_path": "models/random_forest",
  "credit_bins_path": "tests/fixtures/optimal_credit_bins.json",
  "evaluate": false
}
```

### `config/roberta.json`
```json
{
  "model": "roberta",
  "train_data_path": "data/processed/cleaned_train_data.json",
  "val_data_path": "data/processed/cleaned_val_data.json",
  "test_data_path": "data/processed/cleaned_test_data.json",
  "model_output_path": "models/roberta",
  "evaluate": false
}
```

## 🔐 Environment Variables

See `.env.example` for all configuration options:

- **MODEL_DIR**: Directory containing trained model files
- **SERVER_HOST/PORT**: API server configuration
- **ALLOWED_ORIGINS**: CORS configuration
- **MLFLOW_TRACKING_URI**: MLflow tracking server
- **Data paths**: Paths to train/val/test datasets

## 🛠️ Development

### Code Structure

- **Models** inherit from `BaseModel` interface
- **Features** are extracted using sklearn pipelines
- **Data validation** using Great Expectations
- **Logging** configured throughout for debugging

### Adding New Models

1. Create model class in `fake_news/model/`
2. Inherit from `BaseModel`
3. Implement `train()`, `predict()`, and `compute_metrics()`
4. Add configuration file in `config/`
5. Update `train.py` to handle new model type

## 📊 Data Format

Expected TSV format with columns:
- `id`: Unique identifier
- `statement`: The claim to verify
- `label`: Truth label (pants-fire, false, barely-true, half-true, mostly-true, true)
- `speaker`: Person making the statement
- `speaker_title`: Official title
- `state_info`: State location
- `party_affiliation`: Political party
- `barely_true_count`, `false_count`, etc.: Historical credibility counts
- `context`: Additional context
- `justification`: Fact-check reasoning

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request



## 🙏 Acknowledgments

- Dataset: LIAR dataset for fake news detection
- Models: Scikit-learn, Transformers (Hugging Face)
- Deployment: FastAPI, Docker

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Note**: This project is designed for research and educational purposes. Always verify information through multiple reliable sources.
