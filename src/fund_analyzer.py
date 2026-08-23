"""
TEFAS Canlı ve Kapsamlı Yatırım Fonları Analiz ve Al/Sat Sinyal Modülü
Resmi TEFAS API'si üzerinden Türkiye'deki TÜM (1000+) Yatırım Fonlarını çeker,
Al/Sat Sinyalleri üretir, geçmiş fiyat grafiği ve DCA simülatörü sunar.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional


# TEFAS API Ayarları
TEFAS_LIST_URL = "https://www.tefas.gov.tr/api/funds/fonGetiriBazliBilgiGetir"
TEFAS_PRICE_URL = "https://www.tefas.gov.tr/api/funds/fonFiyatBilgiGetir"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.tefas.gov.tr/TarihselVeriler.aspx"
}

# Bellek içi önbellek (Saniyede tekrar tekrar internete gitmemek için)
_CACHED_ALL_FUNDS: Optional[pd.DataFrame] = None
_CACHE_TIMESTAMP: Optional[datetime] = None


def fetch_all_tefas_funds(force_refresh: bool = False) -> pd.DataFrame:
    """
    Resmi TEFAS API'sinden Türkiye'deki TÜM yatırım fonlarını (1000+ fon) canlı olarak çeker.
    """
    global _CACHED_ALL_FUNDS, _CACHE_TIMESTAMP

    now = datetime.now()
    if not force_refresh and _CACHED_ALL_FUNDS is not None and _CACHE_TIMESTAMP is not None:
        # 10 dakikalık önbellek
        if (now - _CACHE_TIMESTAMP).total_seconds() < 600:
            return _CACHED_ALL_FUNDS

    payload = {
        "dil": "TR",
        "fonTipi": "YAT",
        "kurucuKodu": None,
        "sfonTurKod": None,
        "fonTurAciklama": None,
        "islem": 1,
        "fonTurKod": None,
        "fonGrubu": None,
        "donemGetiri1a": "1",
        "donemGetiri3a": "1",
        "donemGetiri6a": "1",
        "donemGetiri1y": "1",
        "donemGetiriyb": "1",
        "donemGetiri3y": "1",
        "donemGetiri5y": "1",
        "basTarih": None,
        "bitTarih": None,
        "calismaTipi": 2,
        "getiriOrani": "1",
    }

    try:
        r = requests.post(TEFAS_LIST_URL, json=payload, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            raw_list = r.json().get("resultList", [])
            if raw_list:
                cleaned_rows = []
                for item in raw_list:
                    code = str(item.get("fonKodu", "")).strip().upper()
                    if not code:
                        continue
                    
                    title = item.get("fonUnvan", code)
                    cat = item.get("fonTurAciklama", "Diğer")
                    risk = item.get("riskDegeri", "5")
                    try:
                        risk_val = int(risk) if risk and str(risk).isdigit() else 5
                    except Exception:
                        risk_val = 5

                    ret_1m = float(item.get("getiri1a") or 0.0)
                    ret_3m = float(item.get("getiri3a") or 0.0)
                    ret_6m = float(item.get("getiri6a") or 0.0)
                    ret_1y = float(item.get("getiri1y") or 0.0)
                    ret_3y = float(item.get("getiri3y") or 0.0)
                    ret_5y = float(item.get("getiri5y") or 0.0)

                    # Sinyal Analizi Yap
                    sig_info = analyze_fund_metrics(ret_1m, ret_3m, ret_6m, ret_1y, risk_val)

                    cleaned_rows.append({
                        "code": code,
                        "name": title,
                        "category": cat,
                        "risk": risk_val,
                        "1m": round(ret_1m, 2),
                        "3m": round(ret_3m, 2),
                        "6m": round(ret_6m, 2),
                        "1y": round(ret_1y, 2),
                        "3y": round(ret_3y, 2),
                        "5y": round(ret_5y, 2),
                        "signal": sig_info["signal"],
                        "score": sig_info["score"],
                        "color": sig_info["color"],
                        "advice": sig_info["advice"]
                    })

                df = pd.DataFrame(cleaned_rows)
                _CACHED_ALL_FUNDS = df
                _CACHE_TIMESTAMP = now
                return df
    except Exception as e:
        print(f"TEFAS API Veri Çekme Hatası: {e}")

    # Hata durumunda boş değilse eski önbelleği dön
    if _CACHED_ALL_FUNDS is not None:
        return _CACHED_ALL_FUNDS
        
    return pd.DataFrame()


def analyze_fund_metrics(ret_1m: float, ret_3m: float, ret_6m: float, ret_1y: float, risk: int = 5) -> Dict[str, Any]:
    """
    Fonun kısa, orta ve uzun vadeli getirilerine ve riskine göre AL/SAT/BİRİKTİR kararı üretir.
    """
    score = 0
    reasons = []

    # 1. Kısa Vadeli İvme (1 Aylık)
    if ret_1m >= 10.0:
        score += 35
        reasons.append(f"🟢 **Çok Güçlü Aylık İvme (+%{ret_1m:.1f})**: Fon kısa vadede piyasayı yeniyor.")
    elif ret_1m >= 6.0:
        score += 25
        reasons.append(f"🟢 **Pozitif Aylık Getiri (+%{ret_1m:.1f})**: Yükseliş trendi korunuyor.")
    elif ret_1m >= 2.0:
        score += 15
        reasons.append(f"🟡 **Ilımlı Aylık İlerleme (+%{ret_1m:.1f})**: Dengeli getiri.")
    elif ret_1m < 0:
        score -= 20
        reasons.append(f"🔴 **Aylık Negatif Getiri (%{ret_1m:.1f})**: Kısa vadeli düzeltme sürecinde.")

    # 2. Orta & Uzun Vadeli Trend (1 Yıllık)
    if ret_1y >= 110.0:
        score += 35
        reasons.append(f"🟢 **Mükemmel 1 Yıllık Performans (+%{ret_1y:.1f})**: Enflasyon ve BIST endeksini belirgin şekilde aştı.")
    elif ret_1y >= 85.0:
        score += 25
        reasons.append(f"🟢 **Güçlü Yıllık Getiri (+%{ret_1y:.1f})**: Fon yönetimi başarılı bir getiri eğrisi çiziyor.")
    elif ret_1y >= 55.0:
        score += 15
    elif ret_1y > 0:
        score += 5
    else:
        score -= 15
        reasons.append(f"🔴 **Düşük Yıllık Getiri (+%{ret_1y:.1f})**: Endeksin gerisinde kalmış.")

    # 3. İvme Hızlanması (3 Aylık vs 1 Yıllık Ortalama)
    if ret_3m > 0 and (ret_3m * 4) > (ret_1y if ret_1y > 0 else 20):
        score += 20
        reasons.append("⚡ **Getiri İvmesi Hızlanıyor**: Son 3 aylık getiri yıllık ortalamanın üzerine çıkıyor.")
    else:
        score += 5

    # 4. Risk / Getiri Dengesi
    if risk <= 4 and ret_1y >= 60:
        score += 10
        reasons.append(f"🛡️ **Düşük Risk / Yüksek Verim**: Düşük risk ({risk}/7) ile yüksek getiri sağlıyor.")

    score = max(0, min(100, score))

    if score >= 75:
        signal = "GÜÇLÜ AL"
        color = "#00C853"
        action_advice = "Getiri ivmesi çok güçlü. Portföye ekleme veya yeni pozisyon açmak için ideal."
    elif score >= 50:
        signal = "KADEMELİ AL / BİRİKTİR"
        color = "#00E5FF"
        action_advice = "DCA (Düzenli Yatırım) ile her ay ekleme yapmak için çok uygun bir fon."
    elif score >= 35:
        signal = "TUT / İZLE"
        color = "#FFD600"
        action_advice = "Elinizdeki payları koruyun, yeni alım için ivmenin güçlenmesini bekleyin."
    elif score >= 20:
        signal = "KÂR AL / AZALT"
        color = "#FF9100"
        action_advice = "Aşırı yükseliş sonrası ivme yavaşlıyor, kısmi kâr realizasyonu düşünülebilir."
    else:
        signal = "SAT / DEĞİŞTİR"
        color = "#D50000"
        action_advice = "Getiri performansı zayıf, daha yüksek ivmeli alternatif fonlara geçiş değerlendirilmeli."

    return {
        "signal": signal,
        "score": score,
        "color": color,
        "advice": action_advice,
        "reasons": reasons
    }


def fetch_fund_price_history(code: str, period_months: int = 12) -> Optional[pd.DataFrame]:
    """
    Herhangi bir TEFAS fonunun (örn: PUK, TLY, MAC, TI2 vb.) geçmiş günlük fiyat serisini çeker.
    """
    code = code.strip().upper()
    payload = {
        "fonKodu": code,
        "dil": "TR",
        "periyod": period_months
    }
    try:
        r = requests.post(TEFAS_PRICE_URL, json=payload, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            raw_data = r.json().get("resultList", [])
            if raw_data:
                rows = []
                for item in raw_data:
                    dt_str = item.get("tarih")
                    price = item.get("fiyat")
                    if dt_str and price is not None:
                        rows.append({
                            "Date": pd.to_datetime(dt_str),
                            "Price": float(price),
                            "Rank": item.get("kategoriDerece", 0),
                            "Total": item.get("kategoriFonSay", 0)
                        })
                if rows:
                    df = pd.DataFrame(rows).sort_values(by="Date").reset_index(drop=True)
                    return df
    except Exception as e:
        print(f"Fiyat Geçmişi Çekme Hatası ({code}): {e}")
    return None


def get_single_fund_info(code: str) -> Optional[Dict[str, Any]]:
    """
    Tek bir fon kodunu (PUK, TLY vb.) arar, bulur ve detaylı Al/Sat raporunu döner.
    """
    code = code.strip().upper()
    all_funds = fetch_all_tefas_funds()
    
    if all_funds is not None and not all_funds.empty:
        matched = all_funds[all_funds["code"] == code]
        if not matched.empty:
            row = matched.iloc[0].to_dict()
            sig_info = analyze_fund_metrics(row["1m"], row["3m"], row["6m"], row["1y"], row["risk"])
            row["signal_analysis"] = sig_info
            return row

    # Eğer toplu listede hemen bulunamazsa direkt geçmiş fiyatından dene
    price_df = fetch_fund_price_history(code, period_months=12)
    if price_df is not None and len(price_df) > 10:
        first_p = price_df["Price"].iloc[0]
        last_p = price_df["Price"].iloc[-1]
        ret_1y = ((last_p - first_p) / first_p) * 100
        
        # 1 aylık
        p_1m = price_df["Price"].iloc[-22] if len(price_df) >= 22 else first_p
        ret_1m = ((last_p - p_1m) / p_1m) * 100
        
        # 3 aylık
        p_3m = price_df["Price"].iloc[-66] if len(price_df) >= 66 else first_p
        ret_3m = ((last_p - p_3m) / p_3m) * 100
        
        sig_info = analyze_fund_metrics(ret_1m, ret_3m, ret_1y / 2, ret_1y, risk=5)
        
        return {
            "code": code,
            "name": f"{code} Yatırım Fonu",
            "category": "Yatırım Fonu",
            "risk": 5,
            "1m": round(ret_1m, 2),
            "3m": round(ret_3m, 2),
            "6m": round(ret_1y / 2, 2),
            "1y": round(ret_1y, 2),
            "3y": 0.0,
            "5y": 0.0,
            "signal": sig_info["signal"],
            "score": sig_info["score"],
            "color": sig_info["color"],
            "advice": sig_info["advice"],
            "signal_analysis": sig_info
        }

    return None


def simulate_dca_investment(
    monthly_investment: float = 5000.0,
    years: int = 3,
    fund_annual_return_pct: float = 85.0,
    benchmark_annual_return_pct: float = 55.0
) -> Dict[str, Any]:
    """
    Düzenli Yatırım (Dolar Maliyeti Ortalaması / DCA) Simülatörü.
    """
    total_months = years * 12
    monthly_rate_fund = (1 + (fund_annual_return_pct / 100)) ** (1/12) - 1
    monthly_rate_bench = (1 + (benchmark_annual_return_pct / 100)) ** (1/12) - 1

    fund_balance = 0.0
    bench_balance = 0.0
    total_invested = 0.0
    
    monthly_records = []

    for m in range(1, total_months + 1):
        total_invested += monthly_investment
        fund_balance = (fund_balance + monthly_investment) * (1 + monthly_rate_fund)
        bench_balance = (bench_balance + monthly_investment) * (1 + monthly_rate_bench)

        monthly_records.append({
            "Ay": m,
            "Yatırılan_Toplam": round(total_invested, 2),
            "Fon_Portföy_Değeri": round(fund_balance, 2),
            "Mevduat_BIST_Kıyas": round(bench_balance, 2)
        })

    total_profit_fund = fund_balance - total_invested
    fund_roi_pct = (total_profit_fund / total_invested) * 100

    return {
        "total_invested": round(total_invested, 2),
        "final_fund_balance": round(fund_balance, 2),
        "final_bench_balance": round(bench_balance, 2),
        "net_profit": round(total_profit_fund, 2),
        "roi_pct": round(fund_roi_pct, 2),
        "multiplier": round(fund_balance / total_invested, 2),
        "timeline": pd.DataFrame(monthly_records)
    }
