import mlflow
import mlflow.sklearn
import mlflow.tensorflow
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from src.data_preprocessing import load_data, clean_data, scale_features
from src.feature_engineering import engineer_features
from src.models import get_rf_model, get_xgb_model, get_lstm_model

DATA_PATH = 'data/Battery_RUL.csv'
TARGET_COL = 'RUL'  # Adjust as per your file

def train_evaluate_save(model_name, model, X_train, y_train, X_val, y_val):
    with mlflow.start_run(run_name=model_name):
        if model_name == 'LSTM':
            model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_val, y_val), verbose=0)
            y_pred = model.predict(X_val)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            mlflow.sklearn.log_model(model, model_name)
        mae = mean_absolute_error(y_val, y_pred)
        rmse = mean_squared_error(y_val, y_pred, squared=False)
        mlflow.log_metric('mae', mae)
        mlflow.log_metric('rmse', rmse)
        if model_name == 'LSTM':
            mlflow.tensorflow.log_model(model, model_name)
        print(f"{model_name} MAE: {mae:.4f}, RMSE: {rmse:.4f}")
        return mae

def main():
    df = load_data(DATA_PATH)
    df = clean_data(df)
    df = engineer_features(df)
    feature_cols = [col for col in df.columns if col != TARGET_COL]
    df = scale_features(df, feature_cols)
    X, y = df[feature_cols].values, df[TARGET_COL].values
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # For LSTM reshape input (samples, timesteps, features)
    X_train_lstm = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))
    X_val_lstm = X_val.reshape((X_val.shape[0], 1, X_val.shape[1]))

    models = [
        ('XGBoost', get_xgb_model()),
        ('RandomForest', get_rf_model()),
        ('LSTM', get_lstm_model((1, X_train.shape[1])))
    ]
    best_model, best_score = None, float('inf')
    for (name, model) in models:
        if name == 'LSTM':
            mae = train_evaluate_save(name, model, X_train_lstm, y_train, X_val_lstm, y_val)
        else:
            mae = train_evaluate_save(name, model, X_train, y_train, X_val, y_val)
        if mae < best_score:
            best_score, best_model = mae, name
    print(f"Best model by MAE: {best_model}")

if __name__ == "__main__":
    main()