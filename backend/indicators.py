"""
Financial indicator calculations using pandas/numpy.
All functions take a DataFrame with a 'Close' column (and 'High'/'Low' where needed)
and return the DataFrame with new indicator columns appended.
"""
import numpy as np
import pandas as pd


def add_moving_average(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    df[f"MA_{window}"] = df["Close"].rolling(window=window).mean()
    return df


def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    df["RSI_14"] = rsi
    return df


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    df["MACD"] = macd_line
    df["MACD_Signal"] = signal_line
    df["MACD_Hist"] = histogram
    return df


def add_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    sma = df["Close"].rolling(window=window).mean()
    std = df["Close"].rolling(window=window).std()
    df["BB_Middle"] = sma
    df["BB_Upper"] = sma + (std * num_std)
    df["BB_Lower"] = sma - (std * num_std)
    return df


def add_volatility(df: pd.DataFrame, window: int = 21) -> pd.DataFrame:
    """Annualized rolling volatility based on daily log returns."""
    log_returns = np.log(df["Close"] / df["Close"].shift(1))
    df["Volatility"] = log_returns.rolling(window=window).std() * np.sqrt(252) * 100  # as %
    return df


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = add_moving_average(df, 20)
    df = add_moving_average(df, 50)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    df = add_volatility(df)
    return df
