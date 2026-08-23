"""
BIST Technical Analysis Indicators Module
Saf Python, Pandas ve Numpy ile hesaplanan teknik indikatörler.
"""

import pandas as pd
import numpy as np


def calc_ema(df: pd.DataFrame, periods: list = [9, 21, 50, 200]) -> pd.DataFrame:
    """Hesaplanan EMA serilerini DataFrame'e ekler."""
    df = df.copy()
    for p in periods:
        df[f'EMA_{p}'] = df['Close'].ewm(span=p, adjust=False).mean()
        df[f'SMA_{p}'] = df['Close'].rolling(window=p).mean()
    return df


def calc_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder's RSI (Göreceli Güç Endeksi) hesaplar."""
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # Wilder's Smoothing
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calc_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD, Sinyal çizgisi ve Histogram değerlerini hesaplar."""
    df = df.copy()
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    
    df['MACD'] = ema_fast - ema_slow
    df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    return df


def calc_bollinger_bands(df: pd.DataFrame, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bantları (Üst, Orta, Alt) ve Bant Genişliğini hesaplar."""
    df = df.copy()
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()
    df['BB_Std'] = df['Close'].rolling(window=period).std()
    
    df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * num_std)
    df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * num_std)
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / (df['BB_Middle'] + 1e-10) * 100
    df['BB_Pct'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'] + 1e-10)
    return df


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (Ortalama Gerçek Aralık - Volatilite) hesaplar."""
    high = df['High']
    low = df['Low']
    close_prev = df['Close'].shift(1)

    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr


def calc_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3, smooth_k: int = 3) -> pd.DataFrame:
    """Stokastik Osilatör (%K ve %D) hesaplar."""
    df = df.copy()
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()

    fast_k = 100 * ((df['Close'] - low_min) / (high_max - low_min + 1e-10))
    df['Stoch_K'] = fast_k.rolling(window=smooth_k).mean().bfill()
    df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean().bfill()
    return df


def calc_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """Supertrend İndikatörünü hesaplar (Trend Yönü & Seviyesi)."""
    df = df.copy()
    atr = calc_atr(df, period=period)
    
    hl2 = (df['High'] + df['Low']) / 2
    upper_basic = hl2 + (multiplier * atr)
    lower_basic = hl2 - (multiplier * atr)

    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(1, index=df.index, dtype=int)  # 1 = Bullish, -1 = Bearish

    upper_final = upper_basic.copy()
    lower_final = lower_basic.copy()

    for i in range(1, len(df)):
        # NaN kontrolü
        prev_uf = upper_final.iloc[i-1] if not pd.isna(upper_final.iloc[i-1]) else upper_basic.iloc[i]
        prev_lf = lower_final.iloc[i-1] if not pd.isna(lower_final.iloc[i-1]) else lower_basic.iloc[i]
        
        # Upper Final
        if upper_basic.iloc[i] < prev_uf or df['Close'].iloc[i-1] > prev_uf:
            upper_final.iloc[i] = upper_basic.iloc[i]
        else:
            upper_final.iloc[i] = prev_uf

        # Lower Final
        if lower_basic.iloc[i] > prev_lf or df['Close'].iloc[i-1] < prev_lf:
            lower_final.iloc[i] = lower_basic.iloc[i]
        else:
            lower_final.iloc[i] = prev_lf

        # Supertrend direction
        if df['Close'].iloc[i] > prev_uf:
            direction.iloc[i] = 1
        elif df['Close'].iloc[i] < prev_lf:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]

        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower_final.iloc[i]
        else:
            supertrend.iloc[i] = upper_final.iloc[i]

    # İlk satırı doldur
    if len(supertrend) > 0 and pd.isna(supertrend.iloc[0]):
        supertrend.iloc[0] = supertrend.iloc[1] if len(supertrend) > 1 else df['Close'].iloc[0]

    df['Supertrend'] = supertrend.bfill()
    df['Supertrend_Direction'] = direction
    return df


def calc_volume_analysis(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Hacim hareketli ortalaması ve Hacim patlamalarını tespit eder."""
    df = df.copy()
    df['Volume_MA'] = df['Volume'].rolling(window=period).mean()
    df['Volume_Ratio'] = df['Volume'] / (df['Volume_MA'] + 1e-10)
    
    # OBV (On-Balance Volume)
    obv_change = np.where(df['Close'] > df['Close'].shift(1), df['Volume'],
                 np.where(df['Close'] < df['Close'].shift(1), -df['Volume'], 0))
    df['OBV'] = pd.Series(obv_change, index=df.index).cumsum()
    return df


def calc_support_resistance(df: pd.DataFrame, window: int = 20) -> dict:
    """Pivot noktaları ve son döngü tepe/dip noktalarına göre destek & direnç hesaplar."""
    if len(df) < window:
        return {"support_1": 0, "support_2": 0, "resistance_1": 0, "resistance_2": 0, "pivot": 0}
    
    recent = df.iloc[-window:]
    last_close = df['Close'].iloc[-1]
    last_high = df['High'].iloc[-1]
    last_low = df['Low'].iloc[-1]

    # Klasik Pivot Noktası
    pivot = (last_high + last_low + last_close) / 3
    r1 = 2 * pivot - last_low
    s1 = 2 * pivot - last_high
    r2 = pivot + (last_high - last_low)
    s2 = pivot - (last_high - last_low)

    # Son dönemin en yüksek ve en düşükleri
    recent_high = recent['High'].max()
    recent_low = recent['Low'].min()

    return {
        "pivot": round(pivot, 2),
        "support_1": round(s1, 2),
        "support_2": round(s2, 2),
        "resistance_1": round(r1, 2),
        "resistance_2": round(r2, 2),
        "recent_high": round(recent_high, 2),
        "recent_low": round(recent_low, 2)
    }


def add_all_indicators(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Tüm indikatörleri tek adımda DataFrame'e hesaplayıp ekler."""
    if df is None or len(df) < 30:
        return df

    from src.config import DEFAULT_INDICATOR_PARAMS
    p = DEFAULT_INDICATOR_PARAMS if params is None else {**DEFAULT_INDICATOR_PARAMS, **params}

    df = calc_ema(df, periods=[p['EMA_SHORT'], p['EMA_MEDIUM'], p['EMA_LONG'], p['EMA_TREND']])
    df['RSI'] = calc_rsi(df, period=p['RSI_PERIOD'])
    df = calc_macd(df, fast=p['MACD_FAST'], slow=p['MACD_SLOW'], signal=p['MACD_SIGNAL'])
    df = calc_bollinger_bands(df, period=p['BB_PERIOD'], num_std=p['BB_STD'])
    df['ATR'] = calc_atr(df, period=14)
    df = calc_stochastic(df, k_period=p['STOCH_K'], d_period=p['STOCH_D'], smooth_k=p['STOCH_SMOOTH'])
    df = calc_supertrend(df, period=p['SUPERTREND_PERIOD'], multiplier=p['SUPERTREND_MULTIPLIER'])
    df = calc_volume_analysis(df, period=p['VOLUME_MA_PERIOD'])

    return df
