"""
BIST Tavan Potansiyeli ve Kırılım Analiz Modülü (Breakout & Ceiling Predictor)
Hacim patlaması, volatilite sıkışması (Bollinger Squeeze), direnç kırılımları ve
momentum ivmesine dayalı "Tavan / Sert Yükseliş Adayı" skorlama motoru.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.indicators import add_all_indicators


def calculate_tavan_potential(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Bir hissenin tavan yapma veya sert yukarı patlama potansiyelini analiz eder ve 0-100 arası skor üretir.
    
    Kriterler:
    1. Hacim Patlaması (Volume Surge): Son gün hacmi 20 günlük ortalamanın katı mı?
    2. Direnç & Zirve Kırılımı (Breakout): Son 20/50 günün zirvesi kırıldı mı?
    3. Volatilite Sıkışması (Bollinger Squeeze & Expansion): Bant daralıp yukarı açıldı mı?
    4. Momentum Gücü (RSI & MACD Acceleration): İvme güçlü ve pozitif mi?
    5. Mum Gücü (Bullish Price Action): Alıcılar günü tavana yakın kapatıyor mu?
    """
    if df is None or len(df) < 30:
        return {
            "tavan_score": 0,
            "category": "Yetersiz Veri",
            "badge_color": "#888888",
            "volume_multiplier": 1.0,
            "is_breakout": False,
            "is_squeeze_breakout": False,
            "tavan_target_price": 0.0,
            "signals": [],
            "metrics": {}
        }

    df = add_all_indicators(df)
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    close = float(last['Close'])
    open_p = float(last['Open'])
    high = float(last['High'])
    low = float(last['Low'])
    
    prev_close = float(prev['Close'])
    
    # BIST Günlük Tavan Fiyatı Hesaplama (+%10 Limit)
    # BIST kurallarına göre tavan fiyatı bir önceki gün kapanışının %10 fazlasıdır (kuruş yuvarlaması ile)
    tavan_price = round(prev_close * 1.10, 2)
    daily_gain_pct = ((close - prev_close) / prev_close) * 100
    tavana_kalan_pct = round(((tavan_price - close) / close) * 100, 2)

    score = 0
    signals = []
    
    # ----------------------------------------------------
    # 1. HACİM PATLAMASI ANALİZİ (Max 30 Puan)
    # ----------------------------------------------------
    vol = float(last['Volume'])
    vol_ma = float(last.get('Volume_MA', vol))
    vol_ratio = vol / (vol_ma + 1e-10)
    
    if vol_ratio >= 3.0:
        score += 30
        signals.append(f"🔥 **Muazzam Hacim Patlaması ({vol_ratio:.1f}x)**: Hacim ortalamanın 3 katını aştı, yoğun para girişi var.")
    elif vol_ratio >= 2.0:
        score += 22
        signals.append(f"⚡ **Güçlü Hacim Artışı ({vol_ratio:.1f}x)**: 20 günlük ortalamanın 2 katı hacim gerçekleşti.")
    elif vol_ratio >= 1.5:
        score += 14
        signals.append(f"📈 **Belirgin Hacim Teyidi ({vol_ratio:.1f}x)**: Alımlar ortalama üzeri hacimle yapılıyor.")
    elif vol_ratio < 0.7:
        score -= 10

    # ----------------------------------------------------
    # 2. DİRENÇ VE ZİRVE KIRILIMI (Max 25 Puan)
    # ----------------------------------------------------
    recent_20 = df.iloc[-21:-1]
    high_20 = float(recent_20['High'].max())
    high_50 = float(df.iloc[-51:-1]['High'].max()) if len(df) >= 52 else high_20
    
    is_20d_breakout = close >= high_20
    is_50d_breakout = close >= high_50
    near_high = close >= (high_20 * 0.985)  # Zirveye %1.5 veya daha yakın
    
    if is_50d_breakout and vol_ratio >= 1.5:
        score += 25
        signals.append(f"🚀 **50 Günlük Zirve Kırılımı**: Fiyat {high_50:.2f} TL direncini hacimli kırarak yeni zirve yaptı.")
    elif is_20d_breakout:
        score += 20
        signals.append(f"🎯 **20 Günlük Direnç Kırıldı**: Fiyat son 1 ayın en yüksek seviyesinin ({high_20:.2f} TL) üzerine çıktı.")
    elif near_high:
        score += 12
        signals.append(f"⏳ **Kritik Direnç Eşiğinde**: Fiyat 20 günlük zirvesini ({high_20:.2f} TL) test ediyor, kırarsa sert fırlar.")

    # ----------------------------------------------------
    # 3. VOLATİLİTE SIKIŞMASI (BOLLINGER SQUEEZE - Max 20 Puan)
    # ----------------------------------------------------
    # Son 20 gündeki bant genişliklerinin en düşüğünde mi?
    bb_widths = df['BB_Width'].iloc[-20:]
    min_width = float(bb_widths.min())
    curr_width = float(last.get('BB_Width', 10))
    bb_upper = float(last.get('BB_Upper', close))
    
    is_squeeze = curr_width <= (min_width * 1.15)  # Çok dar bant
    is_squeeze_break = (close >= bb_upper) or (high >= bb_upper and close > prev_close)

    if is_squeeze and is_squeeze_break:
        score += 20
        signals.append("💣 **Bollinger Sıkışması Patladı (Squeeze Breakout)**: Daralan bant yukarı yönlü patladı, sert ralli tetiklenebilir.")
    elif is_squeeze_break:
        score += 14
        signals.append("💥 **Bollinger Üst Bant Kırılımı**: Fiyat üst bandı delerek yükseliş kanalını genişletiyor.")
    elif is_squeeze:
        score += 8
        signals.append("🗜️ **Fiyat Aşırı Sıkıştı**: Hissede büyük bir hareket için enerji toplanıyor.")

    # ----------------------------------------------------
    # 4. MOMENTUM & İVME GÜCÜ (RSI & MACD - Max 15 Puan)
    # ----------------------------------------------------
    rsi = float(last.get('RSI', 50))
    rsi_prev = float(prev.get('RSI', 50))
    macd_hist = float(last.get('MACD_Hist', 0))
    prev_macd_hist = float(prev.get('MACD_Hist', 0))
    
    if 55 <= rsi <= 75 and (rsi - rsi_prev) >= 4.0:
        score += 10
        signals.append(f"⚡ **Sert RSI İvmesi ({rsi:.1f})**: Momentum hızla güçleniyor (İdeal ralli bölgesi).")
    elif rsi > 78:
        # Aşırı şişmiş olabilir ama tavan serilerinde RSI 80+ olur, ufak puan ver
        score += 5
    elif rsi < 45:
        score -= 5

    if macd_hist > 0 and macd_hist > prev_macd_hist:
        score += 5
        signals.append("📊 **MACD Histogramı Genişliyor**: Alıcıların gücü giderek artıyor.")

    # ----------------------------------------------------
    # 5. MUM GÖVDE VE GÜÇ DİNAMİĞİ (Max 10 Puan)
    # ----------------------------------------------------
    candle_range = high - low
    body = close - open_p
    
    if candle_range > 0:
        body_pct = body / candle_range
        close_near_high = (high - close) / candle_range <= 0.15  # Mumun en tepesinde kapandı
        
        if body > 0 and close_near_high and daily_gain_pct >= 2.5:
            score += 10
            signals.append("🟢 **Günün En Yükseğinde Kapanış**: Satıcılar tamamen ezildi, alıcılar tavan baskısı kuruyor.")
        elif body > 0 and daily_gain_pct >= 1.5:
            score += 5

    # Skoru 0 ile 100 arasına sınırla
    score = max(0, min(100, score))

    # Kategori Belirleme
    if score >= 75:
        category = "🚀 YÜKSEK TAVAN POTANSİYELİ"
        badge_color = "#00E676"
        desc = "Hacim patlaması ve direnç kırılımı ile tavana kilitlenme veya +%7-%10 ralli potansiyeli çok yüksek."
    elif score >= 55:
        category = "⚡ GÜÇLÜ KIRILIM & TAKİP"
        badge_color = "#00B0FF"
        desc = "Yukarı yönlü sert hareket başladı, hacim desteğiyle tavan denemesi yapabilir."
    elif score >= 35:
        category = "🔍 RADARDA / SIKIŞMA VAR"
        badge_color = "#FFD600"
        desc = "Teknik sıkışma ve hazırlık mevcut. Hacimli bir haber/alım ile hareketlenebilir."
    else:
        category = "⚪ DÜŞÜK POTANSİYEL"
        badge_color = "#78909C"
        desc = "Şu an için belirgin bir tavan veya patlama emaresi bulunmuyor."

    return {
        "tavan_score": score,
        "category": category,
        "badge_color": badge_color,
        "description": desc,
        "volume_multiplier": round(vol_ratio, 2),
        "daily_gain_pct": round(daily_gain_pct, 2),
        "tavan_target_price": tavan_price,
        "tavana_kalan_pct": tavana_kalan_pct,
        "is_breakout": is_20d_breakout or is_50d_breakout,
        "is_squeeze_breakout": is_squeeze and is_squeeze_break,
        "high_20d": round(high_20, 2),
        "high_50d": round(high_50, 2),
        "signals": signals,
        "metrics": {
            "RSI": round(rsi, 1),
            "Hacim_Katı": f"{vol_ratio:.1f}x",
            "Bant_Genişliği": f"%{curr_width:.1f}",
            "Tavan_Fiyatı": f"{tavan_price:.2f} TL"
        }
    }
