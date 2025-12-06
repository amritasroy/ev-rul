def engineer_features(df):
    # Example: moving averages + lags for time series
    for col in ['Voltage', 'Current', 'Temperature']:
        df[f'{col}_rolling_mean'] = df[col].rolling(window=5, min_periods=1).mean()
        df[f'{col}_lag1'] = df[col].shift(1).fillna(method='bfill')
    return df