from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
import tensorflow as tf
from tensorflow.keras import layers

def get_rf_model():
    return RandomForestRegressor(n_estimators=100)

def get_xgb_model():
    return XGBRegressor(n_estimators=100)

def get_lstm_model(input_shape):
    model = tf.keras.Sequential()
    model.add(layers.LSTM(50, activation='relu', input_shape=input_shape))
    model.add(layers.Dense(1))
    model.compile(optimizer='adam', loss='mae')
    return model