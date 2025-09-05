from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
import mlflow
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping


def prepare_lstm_data(series: pd.Series, lookback: int = 12) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare data for LSTM training.
    
    Args:
        series: Time series data
        lookback: Number of previous periods to use for prediction
    
    Returns:
        Tuple of (X, y) arrays for training
    """
    # Normalize data
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(series.values.reshape(-1, 1))
    
    X, y = [], []
    for i in range(lookback, len(scaled_data)):
        X.append(scaled_data[i-lookback:i, 0])
        y.append(scaled_data[i, 0])
    
    return np.array(X), np.array(y), scaler


def create_lstm_model(
    input_shape: Tuple[int, int],
    lstm_units: int = 50,
    dropout_rate: float = 0.2,
    learning_rate: float = 0.001
) -> Sequential:
    """
    Create LSTM model architecture.
    
    Args:
        input_shape: Input shape (lookback, features)
        lstm_units: Number of LSTM units
        dropout_rate: Dropout rate
        learning_rate: Learning rate
    
    Returns:
        Compiled LSTM model
    """
    model = Sequential([
        LSTM(lstm_units, return_sequences=True, input_shape=input_shape),
        Dropout(dropout_rate),
        LSTM(lstm_units, return_sequences=False),
        Dropout(dropout_rate),
        Dense(25),
        Dense(1)
    ])
    
    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss='mse',
        metrics=['mae']
    )
    
    return model


def fit_lstm_and_forecast(
    series: pd.Series,
    horizon: int,
    lookback: int = 12,
    lstm_units: int = 50,
    epochs: int = 100,
    batch_size: int = 32,
    validation_split: float = 0.2,
    dropout_rate: float = 0.2,
    learning_rate: float = 0.001
) -> pd.DataFrame:
    """
    Fit LSTM model and generate forecasts.
    
    Args:
        series: Time series data
        horizon: Forecast horizon
        lookback: Number of previous periods to use for prediction
        lstm_units: Number of LSTM units
        epochs: Number of training epochs
        batch_size: Batch size for training
        validation_split: Fraction of data to use for validation
        dropout_rate: Dropout rate
        learning_rate: Learning rate
    
    Returns:
        DataFrame with columns: step, yhat
    """
    with mlflow.start_run(nested=True):
        # Log parameters
        mlflow.log_params({
            "model": "LSTM",
            "horizon": horizon,
            "lookback": lookback,
            "lstm_units": lstm_units,
            "epochs": epochs,
            "batch_size": batch_size,
            "dropout_rate": dropout_rate,
            "learning_rate": learning_rate
        })
        
        # Prepare data
        X, y, scaler = prepare_lstm_data(series, lookback)
        
        # Reshape for LSTM (samples, timesteps, features)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Create model
        model = create_lstm_model(
            input_shape=(lookback, 1),
            lstm_units=lstm_units,
            dropout_rate=dropout_rate,
            learning_rate=learning_rate
        )
        
        # Early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        # Train model
        history = model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Log metrics
        mlflow.log_metric("final_loss", float(history.history['loss'][-1]))
        mlflow.log_metric("final_val_loss", float(history.history['val_loss'][-1]))
        mlflow.log_metric("epochs_trained", len(history.history['loss']))
        
        # Generate forecasts
        forecasts = []
        current_sequence = X[-1].reshape(1, lookback, 1)
        
        for _ in range(horizon):
            # Predict next value
            next_pred = model.predict(current_sequence, verbose=0)
            forecasts.append(next_pred[0, 0])
            
            # Update sequence (shift and add new prediction)
            current_sequence = np.roll(current_sequence, -1, axis=1)
            current_sequence[0, -1, 0] = next_pred[0, 0]
        
        # Inverse transform forecasts
        forecasts = scaler.inverse_transform(np.array(forecasts).reshape(-1, 1))
        forecasts = forecasts.flatten()
        
        # Create output DataFrame
        result_df = pd.DataFrame({
            'step': range(1, horizon + 1),
            'yhat': forecasts
        })
        
        return result_df


def create_ensemble_lstm(
    series: pd.Series,
    horizon: int,
    n_models: int = 3,
    lookback: int = 12
) -> pd.DataFrame:
    """
    Create ensemble of LSTM models for more robust forecasting.
    
    Args:
        series: Time series data
        horizon: Forecast horizon
        n_models: Number of LSTM models in ensemble
        lookback: Number of previous periods to use for prediction
    
    Returns:
        DataFrame with columns: step, yhat, yhat_lower, yhat_upper
    """
    with mlflow.start_run(nested=True):
        mlflow.log_params({
            "model": "Ensemble_LSTM",
            "horizon": horizon,
            "n_models": n_models,
            "lookback": lookback
        })
        
        # Train multiple models with different random seeds
        all_forecasts = []
        
        for i in range(n_models):
            # Set random seed for reproducibility
            np.random.seed(42 + i)
            
            # Train model
            forecast_df = fit_lstm_and_forecast(
                series=series,
                horizon=horizon,
                lookback=lookback,
                lstm_units=50 + i * 10,  # Vary architecture slightly
                epochs=50,  # Fewer epochs for ensemble
                dropout_rate=0.1 + i * 0.05
            )
            
            all_forecasts.append(forecast_df['yhat'].values)
        
        # Calculate ensemble statistics
        all_forecasts = np.array(all_forecasts)
        mean_forecast = np.mean(all_forecasts, axis=0)
        std_forecast = np.std(all_forecasts, axis=0)
        
        # Create confidence intervals
        lower_bound = mean_forecast - 1.96 * std_forecast
        upper_bound = mean_forecast + 1.96 * std_forecast
        
        # Log ensemble metrics
        mlflow.log_metric("ensemble_std", float(np.mean(std_forecast)))
        mlflow.log_metric("forecast_range", float(np.max(mean_forecast) - np.min(mean_forecast)))
        
        # Create output DataFrame
        result_df = pd.DataFrame({
            'step': range(1, horizon + 1),
            'yhat': mean_forecast,
            'yhat_lower': lower_bound,
            'yhat_upper': upper_bound
        })
        
        return result_df
