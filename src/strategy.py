"""
BIST Strategy & Signal Generation Engine
Çoklu teknik göstergeleri ağırlıklandırarak AL/SAT sinyalleri ve hedef fiyatlar üretir.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from src.indicators import add_all_indicators, calc_support_resistance


def analyze_stock(df: pd.DataFrame, params: dict = None) -> Dict[str, Any]:
    """
    DataFrame içindeki verileri analiz ederek detaylı sinyal raporu üretir.
    """
    if df is None or len(df) < 35:
        return {
            "signal": "Yetersiz Veri",
            "score": 0,
            "color": "#888888",
            "reasons": ["Analiz için yeterli geçmiş veri bulunamadı."],
            "details": {}
        }

    # İndikatörleri ekle
    df = add_all_indicators(df, params=params)
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    close = last['Close']
    
    score = 0
    reasons = []
    signals_breakdown = {}

    # 1. RSI ANALİZİ (Ağırlık: ±20)
    rsi = last.get('RSI', 50)
    prev_rsi = prev.get('RSI', 50)
    
    if rsi < 30:
        score += 20
        reasons.append(f"🟢 **RSI Aşırı Satım Bölgesinde ({rsi:.1f})**: Hisse dip seviyelerde, tepki alımı beklenir.")
        signals_breakdown['RSI'] = {"verdict": "GÜÇLÜ AL", "score": +20, "val": round(rsi, 1)}
    elif rsi < 45 and rsi > prev_rsi:
        score += 10
        reasons.append(f"🟢 **RSI Yükseliş Eğiliminde ({rsi:.1f})**: Alıcılar güçleniyor.")
        signals_breakdown['RSI'] = {"verdict": "AL", "score": +10, "val": round(rsi, 1)}
    elif rsi > 70:
        score -= 20
        reasons.append(f"🔴 **RSI Aşırı Alım Bölgesinde ({rsi:.1f})**: Hisse tepe seviyelerde, kâr satışı riski var.")
        signals_breakdown['RSI'] = {"verdict": "GÜÇLÜ SAT", "score": -20, "val": round(rsi, 1)}
    elif rsi > 55 and rsi < prev_rsi:
        score -= 10
        reasons.append(f"🔴 **RSI Güç Kaybediyor ({rsi:.1f})**: Momentum zayıflıyor.")
        signals_breakdown['RSI'] = {"verdict": "SAT", "score": -10, "val": round(rsi, 1)}
    else:
        signals_breakdown['RSI'] = {"verdict": "NÖTR", "score": 0, "val": round(rsi, 1)}

    # 2. MACD ANALİZİ (Ağırlık: ±25)
    macd = last.get('MACD', 0)
    macd_sig = last.get('MACD_Signal', 0)
    macd_hist = last.get('MACD_Hist', 0)
    prev_macd = prev.get('MACD', 0)
    prev_macd_sig = prev.get('MACD_Signal', 0)

    # Yukarı Kesişim (Bullish Crossover)
    if prev_macd <= prev_macd_sig and macd > macd_sig:
        score += 25
        reasons.append("🟢 **MACD Al Sinyali Kesti**: MACD çizgisi sinyal çizgisini yukarı yönlü kesti.")
        signals_breakdown['MACD'] = {"verdict": "GÜÇLÜ AL", "score": +25, "val": f"{macd:.2f} / {macd_sig:.2f}"}
    elif macd > macd_sig and macd_hist > 0:
        score += 15
        reasons.append("🟢 **MACD Pozitif Bölgede**: Pozitif trend devam ediyor.")
        signals_breakdown['MACD'] = {"verdict": "AL", "score": +15, "val": f"{macd:.2f} / {macd_sig:.2f}"}
    # Aşağı Kesişim (Bearish Crossover)
    elif prev_macd >= prev_macd_sig and macd < macd_sig:
        score -= 25
        reasons.append("🔴 **MACD Sat Sinyali Kesti**: MACD çizgisi sinyal çizgisini aşağı yönlü kırdı.")
        signals_breakdown['MACD'] = {"verdict": "GÜÇLÜ SAT", "score": -25, "val": f"{macd:.2f} / {macd_sig:.2f}"}
    elif macd < macd_sig and macd_hist < 0:
        score -= 15
        reasons.append("🔴 **MACD Negatif Bölgede**: Satış baskısı sürüyor.")
        signals_breakdown['MACD'] = {"verdict": "SAT", "score": -15, "val": f"{macd:.2f} / {macd_sig:.2f}"}
    else:
        signals_breakdown['MACD'] = {"verdict": "NÖTR", "score": 0, "val": f"{macd:.2f} / {macd_sig:.2f}"}

    # 3. HAREKETLİ ORTALAMALAR / EMA TRENDİ (Ağırlık: ±25)
    ema9 = last.get('EMA_9', close)
    ema21 = last.get('EMA_21', close)
    ema50 = last.get('EMA_50', close)
    ema200 = last.get('EMA_200', close)

    if close > ema21 > ema50 > ema200:
        score += 25
        reasons.append("🟢 **Mükemmel Yükseliş Trendi**: Fiyat > EMA21 > EMA50 > EMA200 dizilimi (Boğa Trendi).")
        signals_breakdown['EMA_Trend'] = {"verdict": "GÜÇLÜ AL", "score": +25, "val": f"Fiyat: {close:.2f} > EMA21: {ema21:.2f}"}
    elif close > ema21:
        score += 15
        reasons.append(f"🟢 **Kısa Vadeli EMA21 Üzerinde**: Fiyat ({close:.2f}) EMA21 ({ema21:.2f}) üzerinde seyrediyor.")
        signals_breakdown['EMA_Trend'] = {"verdict": "AL", "score": +15, "val": f"EMA21: {ema21:.2f}"}
    elif close < ema21 < ema50 < ema200:
        score -= 25
        reasons.append("🔴 **Belirgin Düşüş Trendi**: Fiyat < EMA21 < EMA50 < EMA200 dizilimi (Ayı Trendi).")
        signals_breakdown['EMA_Trend'] = {"verdict": "GÜÇLÜ SAT", "score": -25, "val": f"Fiyat: {close:.2f} < EMA21: {ema21:.2f}"}
    elif close < ema21:
        score -= 15
        reasons.append(f"🔴 **EMA21 Altında Kırılma**: Fiyat ({close:.2f}) EMA21 ({ema21:.2f}) altında zayıf.")
        signals_breakdown['EMA_Trend'] = {"verdict": "SAT", "score": -15, "val": f"EMA21: {ema21:.2f}"}
    else:
        signals_breakdown['EMA_Trend'] = {"verdict": "NÖTR", "score": 0, "val": f"EMA21: {ema21:.2f}"}

    # 4. SUPERTREND ANALİZİ (Ağırlık: ±20)
    st_dir = last.get('Supertrend_Direction', 1)
    prev_st_dir = prev.get('Supertrend_Direction', 1)
    st_val = last.get('Supertrend', close)

    if prev_st_dir == -1 and st_dir == 1:
        score += 25
        reasons.append("🟢 **Supertrend AL Döndü**: Trend göstergesi yeşile döndü, yükseliş başladı.")
        signals_breakdown['Supertrend'] = {"verdict": "GÜÇLÜ AL", "score": +25, "val": round(st_val, 2)}
    elif st_dir == 1:
        score += 15
        reasons.append(f"🟢 **Supertrend Boğa Modunda**: Destek seviyesi: {st_val:.2f} TL.")
        signals_breakdown['Supertrend'] = {"verdict": "AL", "score": +15, "val": round(st_val, 2)}
    elif prev_st_dir == 1 and st_dir == -1:
        score -= 25
        reasons.append("🔴 **Supertrend SAT Döndü**: Trend kırmızıya döndü, stop olunmalı.")
        signals_breakdown['Supertrend'] = {"verdict": "GÜÇLÜ SAT", "score": -25, "val": round(st_val, 2)}
    else:
        score -= 15
        reasons.append(f"🔴 **Supertrend Ayı Modunda**: Direnç seviyesi: {st_val:.2f} TL.")
        signals_breakdown['Supertrend'] = {"verdict": "SAT", "score": -15, "val": round(st_val, 2)}

    # 5. BOLLINGER BANTLARI (Ağırlık: ±10)
    bb_upper = last.get('BB_Upper', close)
    bb_lower = last.get('BB_Lower', close)
    bb_mid = last.get('BB_Middle', close)

    if close <= bb_lower:
        score += 15
        reasons.append("🟢 **Bollinger Alt Bandına Değdi**: Fiyat aşırı ucuzladı, tepki sıçraması olası.")
        signals_breakdown['Bollinger'] = {"verdict": "AL", "score": +15, "val": f"Alt: {bb_lower:.2f}"}
    elif close >= bb_upper:
        score -= 15
        reasons.append("🔴 **Bollinger Üst Bandı Zorlanıyor**: Fiyat aşırı yükseldi, direnç bölgesinde.")
        signals_breakdown['Bollinger'] = {"verdict": "SAT", "score": -15, "val": f"Üst: {bb_upper:.2f}"}
    else:
        signals_breakdown['Bollinger'] = {"verdict": "NÖTR", "score": 0, "val": f"Orta: {bb_mid:.2f}"}

    # 6. HACİM TEYİDİ (Ağırlık: ±10)
    vol_ratio = last.get('Volume_Ratio', 1.0)
    price_up = close > prev['Close']
    
    if vol_ratio >= 1.5 and price_up:
        score += 10
        reasons.append(f"🟢 **Güçlü Hacim Teyidi ({vol_ratio:.1f}x)**: Yükseliş yüksek hacimle destekleniyor.")
        signals_breakdown['Hacim'] = {"verdict": "GÜÇLÜ AL", "score": +10, "val": f"{vol_ratio:.1f}x"}
    elif vol_ratio >= 1.5 and not price_up:
        score -= 10
        reasons.append(f"🔴 **Hacimli Satış Baskısı ({vol_ratio:.1f}x)**: Düşüş yüksek hacimle gerçekleşti.")
        signals_breakdown['Hacim'] = {"verdict": "GÜÇLÜ SAT", "score": -10, "val": f"{vol_ratio:.1f}x"}
    else:
        signals_breakdown['Hacim'] = {"verdict": "NÖTR", "score": 0, "val": f"{vol_ratio:.1f}x"}

    # Sinyal Kararı ve Renk Belirleme
    score = max(-100, min(100, score))
    
    if score >= 45:
        verdict = "GÜÇLÜ AL"
        badge_color = "#00C853"
    elif score >= 15:
        verdict = "AL"
        badge_color = "#69F0AE"
    elif score <= -45:
        verdict = "GÜÇLÜ SAT"
        badge_color = "#D50000"
    elif score <= -15:
        verdict = "SAT"
        badge_color = "#FF5252"
    else:
        verdict = "NÖTR"
        badge_color = "#FFD600"

    # Stop-Loss ve Hedef Seviyeleri (ATR & Destek/Direnç Bazlı)
    atr = last.get('ATR', close * 0.03)
    sr = calc_support_resistance(df)

    stop_loss = round(max(close - (2.0 * atr), sr['support_1'] if sr['support_1'] > 0 else close * 0.95), 2)
    take_profit_1 = round(min(close + (2.0 * atr), sr['resistance_1'] if sr['resistance_1'] > 0 else close * 1.05), 2)
    take_profit_2 = round(close + (3.5 * atr), 2)

    risk_pct = ((close - stop_loss) / close) * 100
    reward_pct = ((take_profit_1 - close) / close) * 100
    rr_ratio = round(reward_pct / (risk_pct + 1e-5), 2)

    return {
        "signal": verdict,
        "score": score,
        "color": badge_color,
        "close_price": round(close, 2),
        "stop_loss": stop_loss,
        "take_profit_1": take_profit_1,
        "take_profit_2": take_profit_2,
        "risk_reward_ratio": rr_ratio,
        "risk_pct": round(risk_pct, 2),
        "reward_pct": round(reward_pct, 2),
        "support_resistance": sr,
        "reasons": reasons,
        "breakdown": signals_breakdown,
        "indicators": {
            "RSI": round(rsi, 2),
            "MACD": round(macd, 2),
            "MACD_Signal": round(macd_sig, 2),
            "EMA_9": round(ema9, 2),
            "EMA_21": round(ema21, 2),
            "EMA_50": round(ema50, 2),
            "EMA_200": round(ema200, 2),
            "Supertrend": round(st_val, 2),
            "Supertrend_Dir": "Boğa (Al)" if st_dir == 1 else "Ayı (Sat)",
            "ATR": round(atr, 2),
            "BB_Upper": round(bb_upper, 2),
            "BB_Lower": round(bb_lower, 2),
            "Volume_Ratio": round(vol_ratio, 2)
        }
    }
