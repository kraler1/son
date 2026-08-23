# 📈 BIST Sinyal & Analiz Platformu (Borsa İstanbul)

Borsa İstanbul (BIST 30, BIST 50, BIST 100 ve tüm hisseler) için geliştirilmiş, teknik analiz göstergeleri ile **Alım / Satım Sinyalleri** üreten, hedef ve zarar durdur (Stop-Loss) seviyeleri hesaplayan, toplu piyasa taraması ve geriye dönük test (Backtest) yapabilen modern bir web uygulamasıdır.

---

## ✨ Özellikler

- 📊 **Detaylı Hisse Analizi**:
  - İnteraktif TradingView tarzı mum grafikler (Plotly).
  - EMA (9, 21, 50, 200), Supertrend, Bollinger Bantları, Hacim Ortalamaları.
  - Alt grafiklerde RSI (14) ve MACD göstergeleri.
  - Otomatik **Zarar Durdur (Stop-Loss)**, **Kar Al 1-2 (Take-Profit)** ve Destek/Direnç seviyeleri.
  - Sinyal Skoru (-100 ile +100 arası) ve Türkçe gerekçeli sinyal kartı (**GÜÇLÜ AL**, **AL**, **NÖTR**, **SAT**, **GÜÇLÜ SAT**).

- 🔍 **BIST Toplu Tarayıcı (Screener)**:
  - BIST 30, BIST 50 veya BIST 100 hisselerini tek tıkla tarama.
  - Sadece "AL & GÜÇLÜ AL" verenleri veya "RSI Dipte (<35)" olanları filtreleme.
  - Sıralanabilir canlı sonuç tablosu.

- 📈 **Strateji Backtest (Geçmiş Performans Simülatörü)**:
  - Seçilen hissede seçilen stratejinin (Ağırlıklı İndikatör, Trend Takipçisi, Dip Avcısı, MACD) geçmiş kârlılık testi.
  - Başarılı İşlem Oranı (Win Rate %), Toplam Getiri %, Portföy Gelişim Grafiği (Equity Curve) ve BIST kıyaslaması.
  - Tüm alım-satım geçmişi dökümü.

- 📚 **Eğitim & Rehber**:
  - İndikatörlerin çalışma mantığı ve borsa risk yönetimi kuralları.

---

## 🚀 Hızlı Başlangıç

### 1. Tek Tıkla Başlatma:
Klasör içindeki `baslat.bat` dosyasına çift tıklayarak uygulamayı başlatabilirsiniz.

### 2. Komut Satırından Başlatma:
```bash
cd C:\Users\Sem\.gemini\antigravity\scratch\bist_signal_bot
py -m streamlit run app.py
```

Uygulama otomatik olarak tarayıcınızda `http://localhost:8501` adresinde açılacaktır.

---

## 📁 Proje Yapısı

```
bist_signal_bot/
├── src/
│   ├── config.py             # BIST hisse listeleri ve parametreler
│   ├── data_fetcher.py       # Yahoo Finance veri çekme motoru
│   ├── indicators.py         # RSI, MACD, EMA, Supertrend, Bollinger hesaplamaları
│   ├── strategy.py           # Çoklu gösterge ağırlıklı sinyal üretim motoru
│   └── backtester.py         # Geçmişe dönük kârlılık simülatörü
├── app.py                    # Streamlit ana web arayüzü
├── baslat.bat                # Windows hızlı başlatıcı
├── test_system.py            # Entegrasyon test betiği
├── requirements.txt          # Gerekli kütüphaneler
└── README.md                 # Dokümantasyon
```
