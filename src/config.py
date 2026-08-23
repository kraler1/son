"""
Borsa Istanbul (BIST) Signal & Analysis Bot Configuration
BIST Hisse Kodları, Gösterge Parametreleri ve Strateji Konfigürasyonu
"""

# BIST Endeks ve Popüler Hisse Listeleri
BIST_30 = [
    "AKBNK", "ALARK", "ARCLK", "ASELS", "ASTOR", "BIMAS", "BRSAN", "DOAS",
    "EKGYO", "ENKAI", "EREGL", "FROTO", "GARAN", "GUBRF", "HEKTS", "ISCTR",
    "KCHOL", "KONTR", "KOZAL", "KRDMD", "OYAKC", "PETKM", "PGSUS", "SAHOL",
    "SASA", "SISE", "TCELL", "THYAO", "TOASO", "TUPRS", "YKBNK"
]

BIST_50 = sorted(list(set(BIST_30 + [
    "AEFES", "AGHOL", "AHGAZ", "AKFGY", "AKSA", "ALFAS", "ANSGR", "CANTE",
    "CIMSA", "CLEBI", "DOHOL", "ECILC", "EGEEN", "EUREN", "GESAN", "HALKB",
    "ISGYO", "KAYSE", "KORDS", "MAVI", "MGROS", "ODAS", "OTKAR", "QUAGR",
    "SKBNK", "SOKM", "TABGD", "TKFEN", "TSKB", "TTKOM", "ULKER", "VAKBN",
    "VESTL", "YEOTK", "ZOREN"
])))

BIST_100 = sorted(list(set(BIST_50 + [
    "AGROT", "AKCNS", "ALBRK", "ALGYO", "ALKIM", "BERA", "BIOEN", "BOBET",
    "BRYAT", "BUCIM", "BTCIM", "CANTE", "CCOLA", "CEMAS", "CWENE", "DEVA",
    "EUPWR", "GENIL", "GLYHO", "GSDHO", "GWIND", "IPEKE", "ISDMR", "ISMEN",
    "IZMDC", "KARSN", "KCAER", "KLSER", "KMPUR", "KONYA", "KOZAA", "KZBGY",
    "MIATK", "MPARK", "NTHOL", "PAPIL", "PENTA", "PSGYO", "REEDR", "SDTTR",
    "SMRTG", "TATEN", "TKNSA", "TMSN", "TRGYO", "TSPOR", "TTRAK", "TURSG",
    "VAKKO", "VESBE", "YGGYO"
])))

SECTOR_MAP = {
    "Bankacılık": ["AKBNK", "GARAN", "ISCTR", "YKBNK", "HALKB", "VAKBN", "SKBNK", "TSKB", "ALBRK"],
    "Havacılık": ["THYAO", "PGSUS", "CLEBI", "TAVHL"],
    "Holding & Yatırım": ["KCHOL", "SAHOL", "AGHOL", "DOHOL", "ALARK", "BERA", "GLYHO", "GSDHO"],
    "Sanayi & Üretim": ["EREGL", "KRDMD", "SISE", "ARCLK", "TOASO", "FROTO", "OTKAR", "BRSAN", "EGEEN", "TTRAK"],
    "Enerji & Elektrik": ["ASTOR", "KONTR", "EUPWR", "CWENE", "SMRTG", "YEOTK", "GESAN", "ALFAS", "ODAS", "ZOREN", "GWIND", "CANTE"],
    "Perakende & Gıda": ["BIMAS", "MGROS", "SOKM", "CCOLA", "AEFES", "ULKER", "TABGD"],
    "Telekom & Teknoloji": ["TCELL", "TTKOM", "MIATK", "REEDR", "PAPIL", "SDTTR"],
    "Kimya & Petrol": ["TUPRS", "PETKM", "SASA", "HEKTS", "AKSA", "GUBRF", "ALKIM", "KMPUR"],
    "GYO & Gayrimenkul": ["EKGYO", "ISGYO", "AKFGY", "TRGYO", "KZBGY", "PSGYO"],
    "Çimento & İnşaat": ["OYAKC", "CIMSA", "AKCNS", "BOBET", "BUCIM", "BTCIM", "ENKAI", "TKFEN"]
}

# Şirket Tam İsimleri ve Açıklamaları
COMPANY_NAMES = {
    "THYAO": "Türk Hava Yolları",
    "ASELS": "Aselsan Elektronik",
    "GARAN": "Garanti BBVA",
    "AKBNK": "Akbank",
    "ISCTR": "Türkiye İş Bankası (C)",
    "YKBNK": "Yapı ve Kredi Bankası",
    "KCHOL": "Koç Holding",
    "SAHOL": "Sabancı Holding",
    "TUPRS": "Tüpraş Türkiye Petrol Rafinerileri",
    "EREGL": "Ereğli Demir ve Çelik Fabrikaları",
    "SISE": "Türkiye Şişe ve Cam Fabrikaları",
    "BIMAS": "BİM Birleşik Mağazalar",
    "FROTO": "Ford Otomotiv Sanayi",
    "TOASO": "Tofaş Türk Otomobil Fabrikası",
    "TCELL": "Turkcell İletişim Hizmetleri",
    "TTKOM": "Türk Telekomünikasyon",
    "PGSUS": "Pegasus Hava Taşımacılığı",
    "PETKM": "Petkim Petrokimya Holding",
    "SASA": "SASA Polyester Sanayi",
    "HEKTS": "Hektaş Ticaret",
    "ASTOR": "Astor Enerji",
    "KONTR": "Kontrolmatik Teknoloji",
    "ALARK": "Alarko Holding",
    "ARCLK": "Arçelik",
    "BRSAN": "Borusan Birleşik Boru",
    "DOAS": "Doğuş Otomotiv",
    "EKGYO": "Emlak Konut Gayrimenkul Yatırım Ortaklığı",
    "ENKAI": "Enka İnşaat ve Sanayi",
    "GUBRF": "Gübre Fabrikaları",
    "KOZAL": "Koza Altın İşletmeleri",
    "KRDMD": "Kardemir Karabük Demir Çelik (D)",
    "OYAKC": "Oyak Çimento",
    "MGROS": "Migros Ticaret",
    "SOKM": "Şok Marketler Ticaret",
    "ULKER": "Ülker Bisküvi Sanayi",
    "HALKB": "Türkiye Halk Bankası",
    "VAKBN": "Türkiye Vakıflar Bankası",
    "TSKB": "Türkiye Sınai Kalkınma Bankası",
    "DOHOL": "Doğan Şirketler Grubu Holding",
    "AGHOL": "Anadolu Grubu Holding",
    "CIMSA": "Çimsa Çimento Sanayi",
    "CLEBI": "Çelebi Hava Servisi",
    "EGEEN": "Ege Endüstri ve Ticaret",
    "GESAN": "Girişim Elektrik Sanayi",
    "MAVI": "Mavi Giyim Sanayi",
    "ODAS": "Odaş Elektrik Üretim",
    "OTKAR": "Otokar Otomotiv ve Savunma",
    "TKFEN": "Tekfen Holding",
    "VESTL": "Vestel Elektronik Sanayi",
    "YEOTK": "YEO Teknoloji Enerji",
    "ZOREN": "Zorlu Enerji Elektrik Üretim"
}

# Varsayılan İndikatör Ayarları
DEFAULT_INDICATOR_PARAMS = {
    "RSI_PERIOD": 14,
    "RSI_OVERSOLD": 30,
    "RSI_OVERBOUGHT": 70,
    "MACD_FAST": 12,
    "MACD_SLOW": 26,
    "MACD_SIGNAL": 9,
    "EMA_SHORT": 9,
    "EMA_MEDIUM": 21,
    "EMA_LONG": 50,
    "EMA_TREND": 200,
    "BB_PERIOD": 20,
    "BB_STD": 2.0,
    "STOCH_K": 14,
    "STOCH_D": 3,
    "STOCH_SMOOTH": 3,
    "SUPERTREND_PERIOD": 10,
    "SUPERTREND_MULTIPLIER": 3.0,
    "VOLUME_MA_PERIOD": 20,
    "VOLUME_SPIKE_FACTOR": 1.5
}
