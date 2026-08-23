"""
Sistem Entegrasyon ve Fonksiyonellik Testi
"""
import sys
import os

# Windows konsolunda UTF-8 karakterlerin sorunsuz yazdırılması için
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# src modülünü bulabilmesi için dizini ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_fetcher import fetch_stock_data, get_stock_info
from src.indicators import add_all_indicators
from src.strategy import analyze_stock
from src.backtester import run_backtest
from src.tavan_analyzer import calculate_tavan_potential

def main():
    print("--- 1. VERİ ÇEKME TESTİ (THYAO.IS) ---")
    df = fetch_stock_data("THYAO", period="1y")
    if df is None or df.empty:
        print("HATA: THYAO verisi çekilemedi!")
        return
    print(f"Başarılı! {len(df)} günlük veri çekildi. Son Kapanış: {df['Close'].iloc[-1]:.2f} TL")

    print("\n--- 2. ŞİRKET BİLGİSİ TESTİ ---")
    info = get_stock_info("THYAO")
    print(f"Şirket: {info['name']}, Fiyat: {info['current_price']:.2f} TL, Değişim: %{info['change_pct']:.2f}")

    print("\n--- 3. İNDİKATÖRLER VE SİNYAL ANALİZİ TESTİ ---")
    analysis = analyze_stock(df)
    print(f"Sinyal: {analysis['signal']} (Skor: {analysis['score']})")
    print(f"Stop-Loss: {analysis['stop_loss']} TL, Kar Al (TP1): {analysis['take_profit_1']} TL")
    print("Gerekçeler:")
    for r in analysis['reasons']:
        print(f"  - {r}")

    print("\n--- 4. TAVAN POTANSİYELİ VE KIRILIM TESTİ ---")
    tavan = calculate_tavan_potential(df)
    print(f"Tavan Skoru: {tavan['tavan_score']}/100 ({tavan['category']})")
    print(f"Hacim Katı: {tavan['volume_multiplier']}x, Günlük Tavan Limiti: {tavan['tavan_target_price']} TL")
    print(f"Direnç Kırılımı: {tavan['is_breakout']}, Sıkışma Patlaması: {tavan['is_squeeze_breakout']}")
    print("Tavan Sinyalleri:")
    for s in tavan['signals']:
        print(f"  - {s}")

    print("\n--- 5. TEFAS TÜM FONLAR VE PUK/TLY CANLI TESTİ ---")
    from src.fund_analyzer import fetch_all_tefas_funds, get_single_fund_info, fetch_fund_price_history
    all_f = fetch_all_tefas_funds()
    print(f"Toplam TEFAS Fon Sayısı: {len(all_f)}")
    puk_data = get_single_fund_info("PUK")
    print(f"PUK Fonu: {puk_data['name']} | Sinyal: {puk_data['signal']} | 1A: %{puk_data['1m']}, 3A: %{puk_data['3m']}")
    tly_data = get_single_fund_info("TLY")
    print(f"TLY Fonu: {tly_data['name']} | Sinyal: {tly_data['signal']} | 1A: %{tly_data['1m']}, 1Y: %{tly_data['1y']}")
    puk_hist = fetch_fund_price_history("PUK", period_months=6)
    print(f"PUK 6 Aylık Fiyat Sayısı: {len(puk_hist) if puk_hist is not None else 0}")

    print("\n--- 6. BACKTEST TESTİ ---")
    bt = run_backtest(df, initial_capital=100000, strategy_mode="Ağırlıklı Çoklu İndikatör")
    print(f"Strateji Getirisi: %{bt['total_return_pct']:.2f}")
    print(f"BIST Al-Tut Getirisi: %{bt['benchmark_return_pct']:.2f}")
    print(f"Win Rate: %{bt['win_rate']:.1f}, Toplam İşlem: {bt['total_trades']}")

    print("\n✅ TÜM TESTLER BAŞARIYLA TAMAMLANDI!")

if __name__ == "__main__":
    main()
