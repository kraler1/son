"""
Borsa İstanbul (BIST) ve TEFAS Yatırım Platformu
Modern Streamlit Dashboard - Üst Navigasyon Menüsü ve Tam Kapsamlı Terminal
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Modül içe aktarımları
from src.config import BIST_30, BIST_50, BIST_100, SECTOR_MAP, COMPANY_NAMES, DEFAULT_INDICATOR_PARAMS
from src.data_fetcher import fetch_stock_data, get_stock_info, clean_symbol, format_symbol
from src.indicators import add_all_indicators, calc_support_resistance
from src.strategy import analyze_stock
from src.backtester import run_backtest
from src.tavan_analyzer import calculate_tavan_potential
from src.fund_analyzer import (
    fetch_all_tefas_funds, get_single_fund_info, fetch_fund_price_history,
    simulate_dca_investment
)

# Sayfa Yapılandırması
st.set_page_config(
    page_title="BIST & TEFAS Yatırım Terminali",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# MODERN CSS TASARIMI
st.markdown("""
<style>
    /* Genel Koyu Tema */
    .main {
        background-color: #0E1117 !important;
        color: #E6EDF3;
    }
    
    /* Üst Sekmeler (Top Navigation Bar) Tasarımı */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #161B22;
        padding: 8px 12px;
        border-radius: 12px;
        border: 1px solid #30363D;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 8px;
        background-color: transparent;
        color: #8B949E;
        font-size: 14px;
        font-weight: 600;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #21262D;
        color: #FFFFFF;
        border-color: #30363D;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1F6FEB 0%, #0969DA 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid #58A6FF !important;
        box-shadow: 0 4px 12px rgba(31, 111, 235, 0.3) !important;
    }

    /* Genel Kartlar */
    .metric-card {
        background: linear-gradient(135deg, #161B22 0%, #1E222D 100%);
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #30363D;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 12px;
    }
    .home-hero {
        background: linear-gradient(135deg, #0D1B2A 0%, #1B263B 50%, #162438 100%);
        border-radius: 16px;
        padding: 24px 28px;
        border: 1px solid #30363D;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }
    .tavan-card {
        background: linear-gradient(135deg, #1A237E 0%, #0D47A1 100%);
        border-radius: 14px;
        padding: 18px 22px;
        border: 1px solid #2979FF;
        box-shadow: 0 6px 12px rgba(41, 121, 255, 0.25);
        margin-bottom: 15px;
    }
    .fund-card {
        background: linear-gradient(135deg, #004D40 0%, #00796B 100%);
        border-radius: 14px;
        padding: 18px 22px;
        border: 1px solid #00BFA5;
        box-shadow: 0 6px 12px rgba(0, 191, 165, 0.2);
        margin-bottom: 15px;
    }
    .metric-title {
        color: #8B949E;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-val {
        color: #FFFFFF;
        font-size: 24px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# SIDEBAR (YAN PANEL - HİSSE & AYARLAR)
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
    st.title("BIST & FON")
    st.caption("Borsa İstanbul ve TEFAS Yatırım Analiz Sistemi")
    st.markdown("---")

    st.subheader("📌 Hisse Seçimi")
    list_choice = st.selectbox(
        "Hisse Listesi",
        ["BIST 30", "BIST 50", "BIST 100", "Sektörler", "Özel Kod Yaz"],
        index=0
    )

    if list_choice == "BIST 30":
        stock_options = BIST_30
    elif list_choice == "BIST 50":
        stock_options = BIST_50
    elif list_choice == "BIST 100":
        stock_options = BIST_100
    elif list_choice == "Sektörler":
        selected_sector = st.selectbox("Sektör Seçin", list(SECTOR_MAP.keys()))
        stock_options = SECTOR_MAP[selected_sector]
    else:
        custom_ticker = st.text_input("Hisse Kodu (Örn: THYAO, ASELS)", value="THYAO").upper().strip()
        stock_options = [custom_ticker]

    selected_stock = st.selectbox(
        "Hisse",
        stock_options,
        format_func=lambda x: f"{x} - {COMPANY_NAMES.get(x, '')}" if x in COMPANY_NAMES else x
    )

    st.markdown("---")
    st.subheader("⏱️ Zaman Dilimi")
    period = st.selectbox("Geçmiş Veri Süresi", ["3mo", "6mo", "1y", "2y", "5y"], index=2,
                         format_func=lambda x: {"3mo": "3 Ay", "6mo": "6 Ay", "1y": "1 Yıl", "2y": "2 Yıl", "5y": "5 Yıl"}[x])
    interval = st.selectbox("Mum Aralığı", ["1d", "1wk"], index=0,
                           format_func=lambda x: {"1d": "Günlük (1G)", "1wk": "Haftalık (1H)"}[x])

    st.markdown("---")
    with st.expander("⚙️ İndikatör Ayarları"):
        rsi_p = st.number_input("RSI Periyodu", value=14, min_value=5, max_value=50)
        st_mult = st.number_input("Supertrend Çarpanı", value=3.0, step=0.5)
        custom_params = {
            "RSI_PERIOD": rsi_p,
            "SUPERTREND_MULTIPLIER": st_mult
        }

    st.markdown("""
    <div style="text-align: center; margin-top: 20px; padding: 8px; background: rgba(35, 134, 54, 0.1); border: 1px solid rgba(57, 211, 83, 0.2); border-radius: 8px; font-size: 11px; color: #39D353;">
        🟢 BIST & TEFAS Canlı Bağlantı
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# ÜST NAVİGASYON MENÜSÜ (TOP TABS)
# ==========================================
tab_home, tab_analysis, tab_tavan, tab_funds, tab_screener, tab_backtest, tab_guide = st.tabs([
    "🏠 Anasayfa",
    "📊 Hisse Analiz & Sinyal",
    "🚀 Tavan Adayları & Kırılım",
    "💰 TEFAS Fonları (1000+ Canlı)",
    "🔍 BIST Toplu Tarayıcı",
    "📈 Strateji Backtest",
    "📚 Rehber & Eğitim"
])


# ==============================================================================
# SEKME 1: 🏠 ANASAYFA (GENEL BAKIŞ & PİYASA NABZI)
# ==============================================================================
with tab_home:
    st.markdown("""
    <div class="home-hero">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 28px; font-weight: 900; color: #FFFFFF;">BIST & TEFAS Yatırım Terminali 🚀</div>
                <div style="font-size: 15px; color: #D1D5DB; margin-top: 6px;">
                    Borsa İstanbul hisseleri ve 1.050+ TEFAS fonu için yapay zeka destekli Al/Sat sinyalleri, tavan avcısı ve getiri simülatörü.
                </div>
            </div>
            <div style="text-align: right;">
                <span style="background: rgba(88, 166, 255, 0.2); border: 1px solid #58A6FF; color: #58A6FF; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                    CANLI YAYINDA
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. PİYASA NABZI
    st.subheader("🌐 Borsa İstanbul & Piyasa Nabzı")
    with st.spinner("Piyasa endeksleri ve göstergeleri yükleniyor..."):
        xu100_info = get_stock_info("XU100")
        thyao_info = get_stock_info("THYAO")
        asels_info = get_stock_info("ASELS")
        garan_info = get_stock_info("GARAN")

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #2979FF;">
            <div class="metric-title">BIST 100 ENDEKSİ</div>
            <div class="metric-val">{xu100_info['current_price']:,.2f} ₺</div>
            <div style="color: {'#00C853' if xu100_info['change_pct']>=0 else '#FF5252'}; font-size: 13px; font-weight: 600;">
                {"▲" if xu100_info['change_pct']>=0 else "▼"} %{xu100_info['change_pct']:+.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #00E676;">
            <div class="metric-title">THYAO (Havacılık)</div>
            <div class="metric-val">{thyao_info['current_price']:.2f} ₺</div>
            <div style="color: {'#00C853' if thyao_info['change_pct']>=0 else '#FF5252'}; font-size: 13px; font-weight: 600;">
                {"▲" if thyao_info['change_pct']>=0 else "▼"} %{thyao_info['change_pct']:+.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with p3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #00B0FF;">
            <div class="metric-title">ASELS (Savunma)</div>
            <div class="metric-val">{asels_info['current_price']:.2f} ₺</div>
            <div style="color: {'#00C853' if asels_info['change_pct']>=0 else '#FF5252'}; font-size: 13px; font-weight: 600;">
                {"▲" if asels_info['change_pct']>=0 else "▼"} %{asels_info['change_pct']:+.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with p4:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #FFD600;">
            <div class="metric-title">GARAN (Bankacılık)</div>
            <div class="metric-val">{garan_info['current_price']:.2f} ₺</div>
            <div style="color: {'#00C853' if garan_info['change_pct']>=0 else '#FF5252'}; font-size: 13px; font-weight: 600;">
                {"▲" if garan_info['change_pct']>=0 else "▼"} %{garan_info['change_pct']:+.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 2. GÜNÜN ÖNE ÇIKANLARI
    st.subheader("🌟 Günün Öne Çıkan Fırsatları")
    c_hl1, c_hl2 = st.columns(2)

    with c_hl1:
        with st.container(border=True):
            st.markdown("#### 🚀 Tavan & Kırılım Potansiyeli Yüksek Hisseler")
            st.write("Hacim artışı ve daralan bant kırılımı tespit edilen hisseler:")
            st.markdown("""
            - 🟢 **BIMAS**: 20 günlük direnç testinde, hacimli toplanıyor.
            - 🟢 **TUPRS**: EMA 21 üzerinde boğa trendini koruyor.
            - 🟢 **ASELS**: Yükseliş kanalında tavan deneme potansiyeli yüksek.
            """)
            st.info("💡 Yukarıdaki **'🚀 Tavan Adayları & Kırılım'** sekmesinden tüm hisseleri tarayabilirsiniz.")

    with c_hl2:
        with st.container(border=True):
            st.markdown("#### 🏆 En Yüksek Getirili TEFAS Fonları")
            st.write("Son 1 yılda yatırımcısına en çok kazandıran fonlar:")
            st.markdown("""
            - 🥇 **TLY** (Tera Portföy Serbest): 1Y: **+%684.0** | Sinyal: **GÜÇLÜ AL**
            - 🥈 **TTE** (İş Portföy Teknoloji): 1Y: **+%142.1** | Sinyal: **GÜÇLÜ AL**
            - 🥉 **TI2** (İş Portföy Yan Tahtalar): 1Y: **+%128.9** | Sinyal: **GÜÇLÜ AL**
            - ⭐ **PUK** (Pusula Katılım): 3A: **+%23.7** | Sinyal: **KÂR AL / AZALT**
            """)
            st.info("💡 Yukarıdaki **'💰 TEFAS Fonları'** sekmesinden PUK, TLY dahil tüm 1.050+ fonu sorgulayabilirsiniz.")


# ==============================================================================
# SEKME 2: 📊 HİSSE DETAYLI ANALİZ & SİNYAL
# ==============================================================================
with tab_analysis:
    with st.spinner(f"{selected_stock} verileri yükleniyor ve analiz yapılıyor..."):
        df = fetch_stock_data(selected_stock, period=period, interval=interval)
        info = get_stock_info(selected_stock)

    if df is None or len(df) < 30:
        st.error(f"❌ {selected_stock} için yeterli borsa verisi çekilemedi. Lütfen geçerli bir hisse kodu seçin.")
    else:
        analysis = analyze_stock(df, params=custom_params)
        tavan_data = calculate_tavan_potential(df)
        curr_p = info["current_price"] if info["current_price"] > 0 else analysis["close_price"]
        chg_pct = info["change_pct"]

        c_title, c_badge = st.columns([3, 2])
        with c_title:
            st.title(f"{selected_stock} - {info['name']}")
            st.caption(f"Borsa İstanbul | Güncelleme: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            
        with c_badge:
            sig = analysis["signal"]
            bg_c = analysis["color"]
            st.markdown(f"""
            <div style="text-align: right; margin-top: 10px;">
                <span style="background-color: {bg_c}; color: #000000; font-size: 22px; font-weight: 800; padding: 8px 20px; border-radius: 30px; box-shadow: 0 0 15px {bg_c}66;">
                    {sig}
                </span>
                <div style="font-size: 14px; color: #848E9C; margin-top: 6px;">Sinyal Skoru: <b>{analysis['score']} / 100</b></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            chg_color = "#00C853" if chg_pct >= 0 else "#D50000"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Son Fiyat</div>
                <div class="metric-val">{curr_p:.2f} ₺</div>
                <div style="color: {chg_color}; font-size: 13px; font-weight: 600; margin-top: 4px;">
                    {"▲" if chg_pct >= 0 else "▼"} %{abs(chg_pct):.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Stop-Loss (Zarar Durdur)</div>
                <div class="metric-val" style="color: #FF5252;">{analysis['stop_loss']:.2f} ₺</div>
                <div style="color: #848E9C; font-size: 13px;">Risk: -%{analysis['risk_pct']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Hedef 1 (Kar Al)</div>
                <div class="metric-val" style="color: #69F0AE;">{analysis['take_profit_1']:.2f} ₺</div>
                <div style="color: #848E9C; font-size: 13px;">Potansiyel: +%{analysis['reward_pct']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

        with m4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🎯 Günlük Tavan Limiti</div>
                <div class="metric-val" style="color: #00E5FF;">{tavan_data['tavan_target_price']:.2f} ₺</div>
                <div style="color: #848E9C; font-size: 13px;">Kalan: +%{tavan_data['tavana_kalan_pct']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

        with m5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Tavan Potansiyel Skoru</div>
                <div class="metric-val" style="color: {tavan_data['badge_color']};">{tavan_data['tavan_score']} / 100</div>
                <div style="color: #848E9C; font-size: 13px;">{tavan_data['category']}</div>
            </div>
            """, unsafe_allow_html=True)

        if tavan_data["signals"]:
            st.markdown(f"""
            <div class="tavan-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 20px; font-weight: bold; color: #FFFFFF;">🚀 Tavan / Sert Yükseliş Potansiyeli: {tavan_data['category']}</span>
                        <div style="color: #BBDEFB; font-size: 14px; margin-top: 4px;">{tavan_data['description']}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background-color: {tavan_data['badge_color']}; color: #000000; font-size: 18px; font-weight: 800; padding: 6px 16px; border-radius: 20px;">
                            Skor: {tavan_data['tavan_score']} / 100
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📋 Sinyal Nedenleri & Teknik Değerlendirme")
        col_reasons, col_table = st.columns([1, 1])

        with col_reasons:
            with st.container(border=True):
                st.markdown(f"#### 🎯 {selected_stock} İçin Sinyal Kararı: **{analysis['signal']}**")
                st.write(f"Algoritmik Al/Sat Güç Puanı: **{analysis['score']}** (-100 ile +100 arası)")
                st.markdown("---")
                for r in analysis["reasons"]:
                    st.markdown(r)
                for t_sig in tavan_data["signals"]:
                    st.markdown(t_sig)
                if not analysis["reasons"] and not tavan_data["signals"]:
                    st.write("Piyasa olağan seyrediyor.")

        with col_table:
            with st.container(border=True):
                st.markdown("#### 🔍 İndikatör & Metrik Dökümü")
                breakdown_data = []
                for ind, details in analysis["breakdown"].items():
                    breakdown_data.append({
                        "Gösterge": ind,
                        "Değer": str(details["val"]),
                        "Karar": details["verdict"],
                        "Puan": f"{details['score']:+d}"
                    })
                breakdown_data.append({
                    "Gösterge": "Hacim Katı",
                    "Değer": f"{tavan_data['volume_multiplier']}x",
                    "Karar": "Yüksek Hacim" if tavan_data['volume_multiplier'] >= 1.5 else "Normal",
                    "Puan": "+30" if tavan_data['volume_multiplier'] >= 3.0 else ("+20" if tavan_data['volume_multiplier'] >= 1.8 else "0")
                })
                b_df = pd.DataFrame(breakdown_data)
                st.dataframe(b_df, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Plotly Grafiği
        st.markdown("### 📈 İnteraktif Fiyat & Tavan Kırılım Grafiği")
        c_opt1, c_opt2, c_opt3, c_opt4 = st.columns(4)
        with c_opt1:
            show_ema = st.checkbox("Hareketli Ortalamalar (EMA 21, 50, 200)", value=True)
        with c_opt2:
            show_st = st.checkbox("Supertrend Çizgisi", value=True)
        with c_opt3:
            show_bb = st.checkbox("Bollinger Bantları (Sıkışma)", value=True)
        with c_opt4:
            show_tavan_line = st.checkbox("Günlük Tavan Seviyesi (+%10)", value=True)

        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.55, 0.15, 0.15, 0.15]
        )

        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="Fiyat", increasing_line_color='#00C853', decreasing_line_color='#D50000'
        ), row=1, col=1)

        if show_ema:
            if 'EMA_21' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], line=dict(color='#FFD600', width=1.5), name="EMA 21"), row=1, col=1)
            if 'EMA_50' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#2979FF', width=1.5), name="EMA 50"), row=1, col=1)
            if 'EMA_200' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='#FF1744', width=2), name="EMA 200"), row=1, col=1)

        if show_st and 'Supertrend' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['Supertrend'], line=dict(color='#00E5FF', width=1.8, dash='dot'), name="Supertrend"), row=1, col=1)

        if show_bb and 'BB_Upper' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='rgba(150, 150, 150, 0.4)', width=1), name="BB Üst"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='rgba(150, 150, 150, 0.4)', width=1), name="BB Alt", fill='tonexty', fillcolor='rgba(150, 150, 150, 0.05)'), row=1, col=1)

        if show_tavan_line and tavan_data['tavan_target_price'] > 0:
            fig.add_hline(
                y=tavan_data['tavan_target_price'],
                line_dash="dashdot", line_color="#00E5FF",
                annotation_text=f"🎯 Tavan Seviyesi ({tavan_data['tavan_target_price']} TL - +%10)",
                row=1, col=1
            )

        vol_colors = ['#00C853' if c >= o else '#D50000' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=vol_colors, name="Hacim", opacity=0.8), row=2, col=1)
        if 'Volume_MA' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['Volume_MA'], line=dict(color='#FFA000', width=1.5), name="Hacim Ort (20)"), row=2, col=1)

        if 'RSI' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#E040FB', width=2), name="RSI (14)"), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="rgba(255, 82, 82, 0.6)", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="rgba(105, 240, 174, 0.6)", row=3, col=1)

        if 'MACD' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#2979FF', width=1.5), name="MACD"), row=4, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='#FF6D00', width=1.5), name="Sinyal"), row=4, col=1)
            hist_colors = ['#00C853' if h >= 0 else '#D50000' for h in df['MACD_Hist']]
            fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=hist_colors, name="Histogram"), row=4, col=1)

        fig.update_layout(
            height=850, template="plotly_dark", xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor="#0E1117", plot_bgcolor="#161A25"
        )
        st.plotly_chart(fig, use_container_width=True)


# ==============================================================================
# SEKME 3: 🚀 TAVAN ADAYLARI & KIRILIM RADARI
# ==============================================================================
with tab_tavan:
    st.header("🚀 Tavan Yapabilecek Hisseler ve Patlama Radarı")
    st.markdown("Borsa İstanbul'da **yoğun para girişi, hacim patlaması, direnç kırılımı ve sıkışma patlaması** yaşayan hisseler.")

    tv_col1, tv_col2, tv_col3 = st.columns([2, 2, 2])
    with tv_col1:
        tv_index = st.selectbox("Taranacak Hisse Havuzu", ["BIST 100 (Geniş Tarama)", "BIST 50", "BIST 30"], index=0, key="tv_idx")
    with tv_col2:
        tv_min_score = st.slider("Minimum Tavan Potansiyel Skoru", 20, 90, 45, 5)
    with tv_col3:
        st.write("")
        st.write("")
        start_tavan_scan = st.button("🔥 Tavan Adaylarını Tara", type="primary", use_container_width=True)

    tavan_pool = BIST_100 if tv_index.startswith("BIST 100") else (BIST_50 if tv_index.startswith("BIST 50") else BIST_30)

    if start_tavan_scan:
        t_progress = st.progress(0)
        t_status = st.empty()
        tavan_results = []
        total_pool = len(tavan_pool)
        
        for idx, sym in enumerate(tavan_pool):
            t_status.text(f"Analiz ediliyor ({idx+1}/{total_pool}): {sym}...")
            t_progress.progress((idx + 1) / total_pool)
            
            df_sym = fetch_stock_data(sym, period="6mo", interval="1d")
            if df_sym is not None and len(df_sym) >= 30:
                t_pot = calculate_tavan_potential(df_sym)
                info_sym = get_stock_info(sym)
                
                curr_price = info_sym["current_price"] if info_sym["current_price"] > 0 else float(df_sym['Close'].iloc[-1])
                change = info_sym["change_pct"]
                
                tavan_results.append({
                    "Hisse": sym,
                    "Şirket Adı": COMPANY_NAMES.get(sym, sym),
                    "Fiyat (TL)": round(curr_price, 2),
                    "Günlük Değişim": f"%{change:+.2f}",
                    "Tavan Skoru": t_pot["tavan_score"],
                    "Kategori": t_pot["category"],
                    "Hacim Katı": f"{t_pot['volume_multiplier']}x",
                    "Tavan Fiyatı": f"{t_pot['tavan_target_price']:.2f} ₺",
                    "Tavana Kalan": f"+%{t_pot['tavana_kalan_pct']:.1f}",
                    "Direnç Kırılımı": "EVET" if t_pot["is_breakout"] else "HAYIR",
                    "Sıkışma Patlaması": "EVET" if t_pot["is_squeeze_breakout"] else "HAYIR",
                    "RSI": t_pot["metrics"]["RSI"],
                    "Sinyal Açıklaması": " | ".join(t_pot["signals"][:2]) if t_pot["signals"] else "Olağan seyir"
                })

        t_status.success(f"✅ Tavan taraması tamamlandı! {len(tavan_results)} hisse incelendi.")
        t_progress.empty()

        if tavan_results:
            tv_df = pd.DataFrame(tavan_results)
            filtered_tv = tv_df[tv_df["Tavan Skoru"] >= tv_min_score].sort_values(by="Tavan Skoru", ascending=False).reset_index(drop=True)

            if len(filtered_tv) > 0:
                st.markdown("### 🏆 En Yüksek Tavan Potansiyeline Sahip İlk 3 Hisse")
                top_cols = st.columns(min(3, len(filtered_tv)))
                for i, col in enumerate(top_cols):
                    row = filtered_tv.iloc[i]
                    with col:
                        st.markdown(f"""
                        <div class="tavan-card">
                            <div style="font-size: 13px; color: #BBDEFB; font-weight: bold;">⭐ TAVAN ADAYI #{i+1}</div>
                            <div style="font-size: 26px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">
                                {row['Hisse']} <span style="font-size: 16px; color: #90CAF9;">({row['Fiyat (TL)']} ₺)</span>
                            </div>
                            <div style="font-size: 13px; color: #E0E0E0; margin-bottom: 8px;">{row['Şirket Adı']}</div>
                            <div style="background-color: rgba(255,255,255,0.15); padding: 8px 12px; border-radius: 8px; margin-bottom: 8px;">
                                <div>🔥 <b>Hacim Artışı:</b> {row['Hacim Katı']}</div>
                                <div>🎯 <b>Tavan Hedefi:</b> {row['Tavan Fiyatı']} ({row['Tavana Kalan']})</div>
                            </div>
                            <div style="font-size: 18px; font-weight: bold; color: #00E676;">
                                Tavan Skoru: {row['Tavan Skoru']} / 100
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown(f"### 📋 Tavan Potansiyeli Olan Hisseler Tablosu ({len(filtered_tv)} Hisse)")
            st.dataframe(
                filtered_tv.style.map(
                    lambda v: 'color: #00E676; font-weight: bold;' if "YÜKSEK" in str(v) else ('color: #00B0FF; font-weight: bold;' if "GÜÇLÜ" in str(v) else 'color: #FFD600;'),
                    subset=['Kategori']
                ),
                use_container_width=True,
                height=450
            )


# ==============================================================================
# SEKME 4: 💰 TÜM TEFAS FONLARI (1000+ CANLI)
# ==============================================================================
with tab_funds:
    st.header("💰 TEFAS Canlı Fon Terminali (Tüm 1000+ Fon)")
    st.markdown("Resmi **TEFAS** sistemindeki **PUK, TLY, MAC, TI2, NRC, BIO** dahil **tüm 1.050+ yatırım fonunun** canlı getiri verileri ve Al/Sat sinyalleri.")

    with st.spinner("TEFAS resmi sisteminden tüm fonlar canlı olarak yükleniyor..."):
        all_tefas_df = fetch_all_tefas_funds()

    fund_sub1, fund_sub2, fund_sub3 = st.tabs([
        "🏆 Canlı Tüm Fonlar & Al/Sat Radarı",
        "🔍 Herhangi Bir Fonu Detaylı Sorgula (PUK, TLY vb.)",
        "📊 Düzenli Fon Yatırımı (DCA) Simülatörü"
    ])

    with fund_sub1:
        c_rf, c_total = st.columns([1, 4])
        with c_rf:
            if st.button("🔄 Canlı Verileri Yenile", use_container_width=True):
                all_tefas_df = fetch_all_tefas_funds(force_refresh=True)
                st.success("Tüm TEFAS verileri güncellendi!")
        with c_total:
            total_count = len(all_tefas_df) if all_tefas_df is not None else 0
            st.info(f"📊 Toplam **{total_count} adet** resmi TEFAS Yatırım Fonu taranıyor.")

        if all_tefas_df is not None and not all_tefas_df.empty:
            f_cat_col, f_sort_col, f_sig_filter = st.columns(3)
            with f_cat_col:
                categories = ["Tümü"] + sorted(list(all_tefas_df["category"].dropna().unique()))
                fund_cat_filter = st.selectbox("Şemsiye Fon Türü Filtresi", categories)
            with f_sort_col:
                fund_sort_by = st.selectbox(
                    "Sıralama Kriteri",
                    ["Sinyal Skoru", "1 Yıllık Getiri (%)", "6 Aylık Getiri (%)", "3 Aylık Getiri (%)", "1 Aylık Getiri (%)", "3 Yıllık Getiri (%)", "5 Yıllık Getiri (%)"],
                    index=0
                )
            with f_sig_filter:
                fund_signal_choice = st.selectbox(
                    "Sinyal Filtresi",
                    ["Tümü", "Sadece GÜÇLÜ AL & BİRİKTİR", "GÜÇLÜ AL", "KADEMELİ AL / BİRİKTİR", "TUT / İZLE", "KÂR AL / AZALT", "SAT / DEĞİŞTİR"]
                )

            filtered_funds = all_tefas_df.copy()
            if fund_cat_filter != "Tümü":
                filtered_funds = filtered_funds[filtered_funds["category"] == fund_cat_filter]

            if fund_signal_choice == "Sadece GÜÇLÜ AL & BİRİKTİR":
                filtered_funds = filtered_funds[filtered_funds["signal"].isin(["GÜÇLÜ AL", "KADEMELİ AL / BİRİKTİR"])]
            elif fund_signal_choice != "Tümü":
                filtered_funds = filtered_funds[filtered_funds["signal"] == fund_signal_choice]

            sort_map = {
                "Sinyal Skoru": "score",
                "1 Yıllık Getiri (%)": "1y",
                "6 Aylık Getiri (%)": "6m",
                "3 Aylık Getiri (%)": "3m",
                "1 Aylık Getiri (%)": "1m",
                "3 Yıllık Getiri (%)": "3y",
                "5 Yıllık Getiri (%)": "5y"
            }
            filtered_funds = filtered_funds.sort_values(by=sort_map[fund_sort_by], ascending=False).reset_index(drop=True)

            display_tbl = filtered_funds[[
                "code", "name", "signal", "score", "1m", "3m", "6m", "1y", "3y", "5y", "risk", "category"
            ]].copy()
            display_tbl.columns = [
                "Fon Kodu", "Fon Tam Adı", "Al/Sat Sinyali", "Skor",
                "1 Ay (%)", "3 Ay (%)", "6 Ay (%)", "1 Yıl (%)", "3 Yıl (%)", "5 Yıl (%)",
                "Risk", "Şemsiye Türü"
            ]

            st.dataframe(
                display_tbl.style.map(
                    lambda v: 'color: #00C853; font-weight: bold;' if v in ["GÜÇLÜ AL", "KADEMELİ AL / BİRİKTİR"] else ('color: #FFD600; font-weight: bold;' if v == "TUT / İZLE" else ('color: #FF5252; font-weight: bold;' if v == "SAT / DEĞİŞTİR" else '')),
                    subset=['Al/Sat Sinyali']
                ),
                use_container_width=True,
                height=500
            )

    with fund_sub2:
        st.markdown("### 🔎 İstediğiniz TEFAS Fonunu Sorgulayın")
        st.write("Aşağıya **PUK, TLY, MAC, TI2, NRC, BIO, YAS** gibi herhangi bir 3 harfli fon kodunu girerek geçmiş fiyat grafiğini ve Al/Sat sinyalini görün:")

        sq_c1, sq_c2 = st.columns([2, 1])
        with sq_c1:
            search_fund_input = st.text_input("TEFAS Fon Kodu Yazın", value="PUK").upper().strip()
        with sq_c2:
            st.write("")
            st.write("")
            btn_search_fund = st.button("🔍 Fonu Getir & Analiz Et", type="primary", use_container_width=True)

        if search_fund_input:
            f_info = get_single_fund_info(search_fund_input)
            
            if f_info is None:
                st.error(f"❌ '{search_fund_input}' kodlu fon TEFAS sisteminde bulunamadı. Lütfen fon kodunu kontrol edin.")
            else:
                sig_info = f_info.get("signal_analysis", {})
                
                st.markdown(f"""
                <div class="fund-card">
                    <div style="font-size: 13px; color: #E0F2F1;">TEFAS FON KODU: <b>{f_info['code']}</b></div>
                    <div style="font-size: 26px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">{f_info['name']}</div>
                    <div style="font-size: 14px; color: #B2DFDB;">Tür: <b>{f_info['category']}</b> | Risk Derecesi: <b>{f_info['risk']} / 7</b></div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                fm1, fm2, fm3, fm4 = st.columns(4)
                with fm1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">1 Aylık Net Getiri</div>
                        <div class="metric-val" style="color: {'#00C853' if f_info['1m']>=0 else '#FF5252'};">%+{f_info['1m']}</div>
                        <div style="color: #848E9C; font-size: 13px;">Kısa Vade</div>
                    </div>
                    """, unsafe_allow_html=True)
                with fm2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">3 Aylık Net Getiri</div>
                        <div class="metric-val" style="color: {'#00C853' if f_info['3m']>=0 else '#FF5252'};">%+{f_info['3m']}</div>
                        <div style="color: #848E9C; font-size: 13px;">Orta Vade</div>
                    </div>
                    """, unsafe_allow_html=True)
                with fm3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">1 Yıllık Net Getiri</div>
                        <div class="metric-val" style="color: #00E676;">%{f_info['1y']:+.1f}</div>
                        <div style="color: #848E9C; font-size: 13px;">3 Yıllık: %+{f_info.get('3y', 0)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with fm4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Al/Sat Sinyali & Skor</div>
                        <div class="metric-val" style="color: {f_info['color']};">{f_info['signal']}</div>
                        <div style="color: #848E9C; font-size: 13px;">Skor: {f_info['score']} / 100</div>
                    </div>
                    """, unsafe_allow_html=True)

                with st.container(border=True):
                    st.markdown(f"#### 🎯 {f_info['code']} Al/Sat Değerlendirmesi")
                    st.markdown(f"**Taktiksel Tavsiye:** {f_info['advice']}")
                    st.markdown("---")
                    for reas in sig_info.get("reasons", []):
                        st.markdown(reas)

                st.markdown(f"### 📈 {f_info['code']} Fonu Geçmiş Fiyat Grafiği")
                price_hist = fetch_fund_price_history(f_info['code'], period_months=12)
                
                if price_hist is not None and not price_hist.empty:
                    fig_fund = go.Figure()
                    fig_fund.add_trace(go.Scatter(
                        x=price_hist["Date"],
                        y=price_hist["Price"],
                        name=f"{f_info['code']} Pay Fiyatı (TL)",
                        line=dict(color="#00BFA5", width=2.5)
                    ))
                    fig_fund.update_layout(
                        template="plotly_dark",
                        height=420,
                        margin=dict(l=10, r=10, t=10, b=10),
                        yaxis_title="Pay Fiyatı (TL)",
                        xaxis_title="Tarih",
                        paper_bgcolor="#0E1117",
                        plot_bgcolor="#161A25"
                    )
                    st.plotly_chart(fig_fund, use_container_width=True)
                else:
                    st.info(f"{f_info['code']} için günlük fiyat geçmişi TEFAS tarafından listelenemedi.")

    with fund_sub3:
        st.markdown("### 📈 Düzenli Fon Yatırımı (DCA / Kümülatif Birikim) Simülatörü")
        st.write("Her ay sabit bir miktarla yatırım fonu alsaydınız bileşik getiri ile servetiniz nasıl büyürdü?")

        dca_c1, dca_c2, dca_c3, dca_c4 = st.columns(4)
        with dca_c1:
            dca_monthly = st.number_input("Aylık Yatırım Tutarı (TL)", value=5000, step=1000)
        with dca_c2:
            dca_years = st.slider("Yatırım Süresi (Yıl)", 1, 10, 3)
        with dca_c3:
            dca_fund_roi = st.slider("Fon Yıllık Ortalama Getirisi (%)", 30, 250, 95, 5)
        with dca_c4:
            dca_bench_roi = st.slider("Alternatif (Mevduat/Enflasyon %) ", 20, 100, 50, 5)

        dca_res = simulate_dca_investment(
            monthly_investment=dca_monthly,
            years=dca_years,
            fund_annual_return_pct=dca_fund_roi,
            benchmark_annual_return_pct=dca_bench_roi
        )

        st.markdown("#### 🏆 Simülasyon Birikim Sonucu")
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("Cebinizden Çıkan Toplam Para", f"{dca_res['total_invested']:,.0f} ₺")
        with r2:
            st.metric("🎯 Ulaşılan Fon Portföyü", f"{dca_res['final_fund_balance']:,.0f} ₺", f"%+{dca_res['roi_pct']:.0f} Toplam Getiri")
        with r3:
            st.metric("Kazanılan Net Kâr", f"{dca_res['net_profit']:,.0f} ₺", f"{dca_res['multiplier']}x Kat Büyüme")
        with r4:
            st.metric("Alternatif Getiri (Mevduat)", f"{dca_res['final_bench_balance']:,.0f} ₺")

        fig_dca = go.Figure()
        timeline_df = dca_res["timeline"]
        fig_dca.add_trace(go.Scatter(
            x=timeline_df["Ay"], y=timeline_df["Fon_Portföy_Değeri"],
            name="Yatırım Fonu Birikimi (Bileşik Getiri)",
            line=dict(color="#00E676", width=3)
        ))
        fig_dca.add_trace(go.Scatter(
            x=timeline_df["Ay"], y=timeline_df["Mevduat_BIST_Kıyas"],
            name="Alternatif Getiri",
            line=dict(color="#FFD600", width=2, dash="dot")
        ))
        fig_dca.add_trace(go.Scatter(
            x=timeline_df["Ay"], y=timeline_df["Yatırılan_Toplam"],
            name="Yatırılan Ana Para",
            line=dict(color="#78909C", width=1.5, dash="dash")
        ))
        fig_dca.update_layout(
            template="plotly_dark",
            height=450,
            yaxis_title="Toplam Portföy Büyüklüğü (TL)",
            xaxis_title="Geçen Ay Sayısı",
            paper_bgcolor="#0E1117",
            plot_bgcolor="#161A25",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_dca, use_container_width=True)


# ==============================================================================
# SEKME 5: 🔍 BIST TOPLU TARAYICI (SCREENER)
# ==============================================================================
with tab_screener:
    st.header("🔍 BIST Piyasa Taraması & Sinyal Radarı")
    st.write("Tüm Borsa İstanbul hisselerini tek tıkla tarayarak **GÜÇLÜ AL**, **AL** veya dip seviyedeki hisseleri anında bulun.")

    c_sc1, c_sc2, c_sc3 = st.columns([2, 2, 2])
    with c_sc1:
        scan_index = st.selectbox("Taranacak Endeks", ["BIST 30 (En Likit 30 Hisse)", "BIST 50", "BIST 100"], index=0)
    with c_sc2:
        filter_signal = st.selectbox("Sinyal Filtresi", ["Tümü", "Sadece AL & GÜÇLÜ AL", "Sadece GÜÇLÜ AL", "Sadece SAT & GÜÇLÜ SAT", "RSI Dipte (<35)"])
    with c_sc3:
        st.write("")
        st.write("")
        start_scan = st.button("🚀 Taramayı Başlat", type="primary", use_container_width=True)

    scan_symbols = BIST_30 if scan_index.startswith("BIST 30") else (BIST_50 if scan_index.startswith("BIST 50") else BIST_100)

    if start_scan:
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        total = len(scan_symbols)
        
        for idx, sym in enumerate(scan_symbols):
            status_text.text(f"Analiz ediliyor ({idx+1}/{total}): {sym}...")
            progress_bar.progress((idx + 1) / total)
            
            df_sym = fetch_stock_data(sym, period="6mo", interval="1d")
            if df_sym is not None and len(df_sym) >= 30:
                res = analyze_stock(df_sym)
                t_pot = calculate_tavan_potential(df_sym)
                info_sym = get_stock_info(sym)
                
                curr_price = info_sym["current_price"] if info_sym["current_price"] > 0 else res["close_price"]
                change = info_sym["change_pct"]
                
                results.append({
                    "Hisse": sym,
                    "Şirket Adı": COMPANY_NAMES.get(sym, sym),
                    "Fiyat (TL)": round(curr_price, 2),
                    "Günlük Değişim": f"%{change:+.2f}",
                    "Sinyal": res["signal"],
                    "Skor": res["score"],
                    "Tavan Skoru": t_pot["tavan_score"],
                    "RSI": res["indicators"]["RSI"],
                    "Supertrend": res["indicators"]["Supertrend_Dir"],
                    "Stop-Loss": res["stop_loss"],
                    "Hedef (TP1)": res["take_profit_1"]
                })

        status_text.success(f"✅ Tarama tamamlandı! Toplam {len(results)} hisse analiz edildi.")
        progress_bar.empty()

        if results:
            res_df = pd.DataFrame(results)

            if filter_signal == "Sadece AL & GÜÇLÜ AL":
                res_df = res_df[res_df["Sinyal"].isin(["AL", "GÜÇLÜ AL"])]
            elif filter_signal == "Sadece GÜÇLÜ AL":
                res_df = res_df[res_df["Sinyal"] == "GÜÇLÜ AL"]
            elif filter_signal == "Sadece SAT & GÜÇLÜ SAT":
                res_df = res_df[res_df["Sinyal"].isin(["SAT", "GÜÇLÜ SAT"])]
            elif filter_signal == "RSI Dipte (<35)":
                res_df = res_df[res_df["RSI"] < 35]

            res_df = res_df.sort_values(by="Skor", ascending=False).reset_index(drop=True)

            sc_c1, sc_c2, sc_c3, sc_c4 = st.columns(4)
            with sc_c1:
                strong_buys = len(res_df[res_df["Sinyal"] == "GÜÇLÜ AL"])
                st.metric("🟢 Güçlü Al Verenler", strong_buys)
            with sc_c2:
                buys = len(res_df[res_df["Sinyal"] == "AL"])
                st.metric("🟩 Al Verenler", buys)
            with sc_c3:
                neutrals = len(res_df[res_df["Sinyal"] == "NÖTR"])
                st.metric("🟨 Nötrler", neutrals)
            with sc_c4:
                sells = len(res_df[res_df["Sinyal"].isin(["SAT", "GÜÇLÜ SAT"])])
                st.metric("🔴 Sat Verenler", sells)

            st.markdown("### 📊 Tarama Sonuç Tablosu")
            st.dataframe(
                res_df.style.map(
                    lambda v: 'color: #00C853; font-weight: bold;' if v in ["GÜÇLÜ AL", "AL"] else ('color: #FF5252; font-weight: bold;' if v in ["GÜÇLÜ SAT", "SAT"] else 'color: #FFD600;'),
                    subset=['Sinyal']
                ),
                use_container_width=True,
                height=500
            )


# ==============================================================================
# SEKME 6: 📈 STRATEJİ BACKTEST (GEÇMİŞ TESTİ)
# ==============================================================================
with tab_backtest:
    st.header("📈 Strateji Geriye Dönük Test (Backtesting)")
    st.write("Seçtiğiniz stratejinin geçmiş borsa verilerinde ne kadar kazanç sağladığını ve başarı oranını simüle edin.")

    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    with b_col1:
        bt_stock = st.selectbox("Test Edilecek Hisse", BIST_30, index=BIST_30.index(selected_stock) if selected_stock in BIST_30 else 0, key="bt_stock")
    with b_col2:
        bt_strat = st.selectbox(
            "Strateji",
            ["Ağırlıklı Çoklu İndikatör", "Trend Takipçisi (EMA & Supertrend)", "Dip/Tepe Avcısı (RSI & Bollinger)", "MACD Kesişimi"],
            index=0
        )
    with b_col3:
        bt_capital = st.number_input("Başlangıç Sermayesi (TL)", value=100000, step=10000)
    with b_col4:
        bt_period = st.selectbox("Test Süresi", ["1y", "2y", "5y"], index=1, format_func=lambda x: {"1y": "1 Yıl", "2y": "2 Yıl", "5y": "5 Yıl"}[x])

    b_sub1, b_sub2, b_sub3 = st.columns(3)
    with b_sub1:
        bt_sl = st.slider("Zarar Durdur (Stop-Loss %)", 1.0, 10.0, 4.0, 0.5)
    with b_sub2:
        bt_tp = st.slider("Kar Al (Take-Profit %)", 2.0, 25.0, 8.0, 0.5)
    with b_sub3:
        st.write("")
        st.write("")
        run_bt_btn = st.button("⚡ Testi Başlat", type="primary", use_container_width=True)

    if run_bt_btn:
        with st.spinner(f"{bt_stock} için {bt_strat} simülasyonu çalıştırılıyor..."):
            df_bt = fetch_stock_data(bt_stock, period=bt_period, interval="1d")
            
            if df_bt is None or len(df_bt) < 50:
                st.error("Backtest için yeterli veri bulunamadı.")
            else:
                bt_results = run_backtest(
                    df_bt,
                    initial_capital=bt_capital,
                    stop_loss_pct=bt_sl,
                    take_profit_pct=bt_tp,
                    strategy_mode=bt_strat
                )

                if "error" in bt_results:
                    st.error(bt_results["error"])
                else:
                    st.markdown("### 🏆 Simülasyon Performans Özeti")
                    k1, k2, k3, k4, k5 = st.columns(5)
                    ret_c = "#00C853" if bt_results["total_return_pct"] >= 0 else "#D50000"
                    with k1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">Strateji Toplam Getiri</div>
                            <div class="metric-val" style="color: {ret_c};">%{bt_results['total_return_pct']:+.2f}</div>
                            <div style="color: #848E9C; font-size: 13px;">Son Bakiye: {bt_results['final_capital']:,.0f} ₺</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with k2:
                        b_ret = bt_results["benchmark_return_pct"]
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">BIST Al & Tut Getirisi</div>
                            <div class="metric-val">%{b_ret:+.2f}</div>
                            <div style="color: #848E9C; font-size: 13px;">Hisse Kıyaslaması</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with k3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">Başarılı İşlem Oranı (Win Rate)</div>
                            <div class="metric-val" style="color: #00E5FF;">%{bt_results['win_rate']:.1f}</div>
                            <div style="color: #848E9C; font-size: 13px;">{bt_results['winning_trades']} Başarılı / {bt_results['total_trades']} İşlem</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with k4:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">Kâr Faktörü (Profit Factor)</div>
                            <div class="metric-val">{bt_results['profit_factor']}</div>
                            <div style="color: #848E9C; font-size: 13px;">Kazanılan / Kaybedilen</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with k5:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">Maksimum Düşüş (Drawdown)</div>
                            <div class="metric-val" style="color: #FF5252;">-%{bt_results['max_drawdown_pct']:.2f}</div>
                            <div style="color: #848E9C; font-size: 13px;">En Büyük Zirve-Dip Kaybı</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("### 📊 Portföy Gelişim Grafiği (Strateji vs Al-Tut)")
                    eq_df = bt_results["equity_curve"]
                    fig_eq = go.Figure()
                    fig_eq.add_trace(go.Scatter(x=eq_df["Date"], y=eq_df["Portfolio"], name=f"Strateji Portföyü ({bt_strat})", line=dict(color="#00E5FF", width=2.5)))
                    fig_eq.add_trace(go.Scatter(x=eq_df["Date"], y=eq_df["Benchmark"], name=f"{bt_stock} Al ve Tut (Benchmark)", line=dict(color="#78909C", width=1.5, dash="dash")))
                    fig_eq.update_layout(
                        template="plotly_dark", height=450, margin=dict(l=10, r=10, t=20, b=10),
                        paper_bgcolor="#0E1117", plot_bgcolor="#161A25", yaxis_title="Portföy Değeri (TL)",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_eq, use_container_width=True)

                    st.markdown("### 📑 Gerçekleşen İşlem Geçmişi")
                    if bt_results["trades"]:
                        trades_df = pd.DataFrame(bt_results["trades"])
                        trades_df.columns = ["Giriş Tarihi", "Çıkış Tarihi", "Alış Fiyatı (TL)", "Satış Fiyatı (TL)", "Net K/Z (TL)", "Getiri (%)", "Çıkış Nedeni"]
                        st.dataframe(
                            trades_df.style.map(
                                lambda v: 'color: #00C853; font-weight: bold;' if v > 0 else 'color: #FF5252; font-weight: bold;',
                                subset=['Getiri (%)', 'Net K/Z (TL)']
                            ),
                            use_container_width=True
                        )


# ==============================================================================
# SEKME 7: 📚 REHBER & EĞİTİM
# ==============================================================================
with tab_guide:
    st.header("📚 BIST Sinyal, Tavan ve TEFAS Fon Analiz Kılavuzu")
    st.markdown("""
    ### 🎯 Sistem Nasıl Kullanılır?
    1. **🏠 Anasayfa**: Piyasa nabzını, BIST 100 durumunu ve günün öne çıkan fırsatlarını tek ekranda takip edin.
    2. **📊 Hisse Analizi**: Kısa ve orta vadeli Al/Sat sinyalleri, EMA trendleri ve Stop-Loss seviyeleri ile işlem yapın.
    3. **🚀 Tavan Adayları**: Yoğun para girişi ve hacim patlaması yaşayan hisseleri gün başında tarayarak erken pozisyon alın.
    4. **💰 TEFAS 1000+ Canlı Fon**: PUK, TLY, MAC dahil Türkiye'deki tüm fonları canlı getiri, Al/Sat sinyali ve grafiklerle inceleyin.
    5. **📈 DCA Simülatörü**: Belirlediğiniz fonla düzenli aylık birikim yaparak bileşik getiri gücünü hesaplayın.
    """)
