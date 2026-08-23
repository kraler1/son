"""
BIST Stock Data Fetcher Module
Yahoo Finance API üzerinden BIST verilerini çeker, temizler ve önbelleğe alır.
"""

import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any, List
from src.config import COMPANY_NAMES


def format_symbol(symbol: str) -> str:
    """BIST hisse kodunu yfinance formatına dönüştürür (örn: THYAO -> THYAO.IS)."""
    symbol = symbol.strip().upper()
    if not symbol.endswith(".IS"):
        return f"{symbol}.IS"
    return symbol


def clean_symbol(symbol: str) -> str:
    """Sembolü temiz BIST koduna dönüştürür (örn: THYAO.IS -> THYAO)."""
    return symbol.replace(".IS", "").strip().upper()


def fetch_stock_data(symbol: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
    """
    Belirtilen BIST hissesinin geçmiş OHLCV fiyat verilerini çeker.
    
    :param symbol: Hisse kodu (örn: THYAO veya THYAO.IS)
    :param period: 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    :param interval: 1d, 1wk, 1h
    :return: Temizlenmiş pandas DataFrame (Open, High, Low, Close, Volume)
    """
    yf_symbol = format_symbol(symbol)
    try:
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
        
        if df is None or df.empty or len(df) < 10:
            return None

        # MultiIndex sütun yapısını düzleştir (yfinance yeni sürümleri için)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Gerekli sütunları kontrol et ve seç
        req_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        available_cols = [c for c in req_cols if c in df.columns]
        
        if len(available_cols) < 5:
            return None
            
        df = df[req_cols].copy()
        
        # Sayısal değerlere dönüştür ve eksik verileri temizle
        for col in req_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna()
        
        # Sıfır hacimli günleri veya hatalı satırları filtrele
        df = df[df['Close'] > 0]
        
        # İndeks saat dilimi bilgisini kaldır (Streamlit ve Plotly uyumu için)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        return df

    except Exception as e:
        print(f"Veri çekme hatası ({symbol}): {e}")
        return None


def get_stock_info(symbol: str) -> Dict[str, Any]:
    """Hisse ile ilgili temel özet bilgileri döndürür."""
    clean = clean_symbol(symbol)
    yf_symbol = format_symbol(symbol)
    company_name = COMPANY_NAMES.get(clean, f"{clean} Sanayi ve Ticaret A.Ş.")
    
    info = {
        "symbol": clean,
        "yf_symbol": yf_symbol,
        "name": company_name,
        "current_price": 0.0,
        "previous_close": 0.0,
        "change_pct": 0.0,
        "day_high": 0.0,
        "day_low": 0.0,
        "volume": 0,
        "market_cap": 0,
        "pe_ratio": None,
        "high_52w": 0.0,
        "low_52w": 0.0
    }

    try:
        ticker = yf.Ticker(yf_symbol)
        fast_info = getattr(ticker, 'fast_info', None)
        
        if fast_info:
            info["current_price"] = getattr(fast_info, 'last_price', 0.0) or 0.0
            info["previous_close"] = getattr(fast_info, 'previous_close', 0.0) or 0.0
            info["day_high"] = getattr(fast_info, 'day_high', 0.0) or 0.0
            info["day_low"] = getattr(fast_info, 'day_low', 0.0) or 0.0
            info["high_52w"] = getattr(fast_info, 'year_high', 0.0) or 0.0
            info["low_52w"] = getattr(fast_info, 'year_low', 0.0) or 0.0
            info["market_cap"] = getattr(fast_info, 'market_cap', 0) or 0
            
            if info["previous_close"] > 0 and info["current_price"] > 0:
                info["change_pct"] = ((info["current_price"] - info["previous_close"]) / info["previous_close"]) * 100
                
        # Eğer fast_info eksikse geçmiş verinin son satırından tamamla
        if info["current_price"] == 0.0:
            df = fetch_stock_data(clean, period="5d")
            if df is not None and len(df) >= 2:
                info["current_price"] = float(df['Close'].iloc[-1])
                info["previous_close"] = float(df['Close'].iloc[-2])
                info["day_high"] = float(df['High'].iloc[-1])
                info["day_low"] = float(df['Low'].iloc[-1])
                info["volume"] = int(df['Volume'].iloc[-1])
                info["change_pct"] = ((info["current_price"] - info["previous_close"]) / info["previous_close"]) * 100
    except Exception as e:
        print(f"Bilgi çekme hatası ({symbol}): {e}")

    return info


def fetch_batch_data(symbols: List[str], period: str = "6mo") -> Dict[str, pd.DataFrame]:
    """Birden fazla hissenin verilerini toplu olarak çeker."""
    results = {}
    for s in symbols:
        df = fetch_stock_data(s, period=period)
        if df is not None and len(df) > 20:
            results[clean_symbol(s)] = df
    return results
