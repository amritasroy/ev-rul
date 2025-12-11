# EV Battery RUL Prediction MLOps Pipeline (with MLflow)

This project predicts the Remaining Useful Life (RUL) for EV batteries using multiple regression models.
It includes an MLOps pipeline powered by MLflow for model tracking, drift detection, and automated retraining.

## 🚀 Setup Steps

1. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```
2. **Prepare the Data**
   - Place your dataset (`Battery_RUL.csv`) in the `data/` folder (already present).

3. **Project Structure**
   - `src/`: Code for data processing, feature engineering, model training, drift detection
   - `mlops/`: Orchestration scripts (pipelines)

4. **MLflow Tracking UI**
   - To launch MLflow UI:
     ```bash
     mlflow ui
     ```
   - Access the UI at: http://localhost:5000

## 📈 MLflow Usage
- All model runs (XGBoost, RandomForest, LSTM) are tracked in MLflow.
- Use the UI to compare models' MAE, RMSE, and download best models.
- Log artifacts, parameters, and metrics for model governance.

## 🔁 How to Trigger Retraining
- **Manual retrain:**
  ```bash
  python src/train.py
  ```
- **Automated retrain (with drift check):**
  ```bash
  python mlops/mlflow_pipeline.py
  ```
- Schedule/repeat by integrating `mlops/mlflow_pipeline.py` into a job scheduler or CI/CD system.

## ⚡ Drift Monitoring Explanation
- Uses two-sample Kolmogorov-Smirnov (KS) tests on feature distributions between reference (historical) and new data.
- If drift is detected (p < 0.01 in any feature), retraining is triggered.
- Modify `src/drift.py`/`mlops/mlflow_pipeline.py` to connect to real streaming or batch data updates as needed.

## 📊 Git Commit Tracker CLI
Track and analyze contributor value, work quality, and contribution patterns in your repository.

### Usage
```bash
# Analyze commits from the last 30 days (default)
python src/commit_tracker.py

# Analyze commits from the last 60 days
python src/commit_tracker.py --days 60

# Export analysis to JSON
python src/commit_tracker.py --export report.json

# Analyze a different repository
python src/commit_tracker.py --repo /path/to/repo
```

### Features
- **Contributor Metrics**: Shows commits, lines added/deleted, files changed
- **Quality Score**: Analyzes commit quality based on best practices (tests, fixes, documentation)
- **Difficulty Score**: Measures complexity based on scope, changes, and file diversity
- **Value Score**: Combined metric weighing quality, difficulty, and amount of work
- **Work Style Analysis**: Categorizes contributors by their work patterns
- **JSON Export**: Export detailed metrics for further analysis

### Metrics Explained
- **Quality Score (0-100)**: Higher scores for focused changes, bug fixes, tests, and documentation
- **Difficulty Score (0-100)**: Based on number of files, lines changed, and file type diversity
- **Value Score (0-100)**: Weighted combination: Quality (40%) + Difficulty (30%) + Amount (30%)
- **Work Style**: Automatically categorized as High-quality/Balanced/Rapid-iteration with complexity and scope indicators

## 👩‍💻 Contributing
- Extend feature engineering, plug in new models, or tune retraining and drift detection logic as your fleet or dataset evolves.

---