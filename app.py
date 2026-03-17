"""
app.py
------
Streamlit web arayüzü.
Çalıştırmak için terminalde: streamlit run app.py

3 sekme:
  1. Genel Bakış   - Anlık kurlar ve özet istatistikler
  2. Grafikler     - 4 farklı görselleştirme
  3. Analiz        - Araştırma sorusu cevabı + Excel indirme
"""

import streamlit as st
import pandas as pd
import os
import sys

# src klasörünü path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from data_collector import get_latest_rates, load_data_from_csv, collect_all_data
from data_cleaner import clean_data
from analyzer import (
    calculate_statistics, calculate_weekly_summary,
    calculate_correlation, find_most_stable, get_best_investment,
    calculate_daily_change
)
from visualizer import (
    plot_line_chart, plot_boxplot, plot_heatmap, plot_daily_change_bar
)
from excel_report import create_excel_report

# ─────────────────────────────────────────────
# Sayfa ayarları
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Döviz Analiz Paneli",
    page_icon="💱",
    layout="wide"
)

# ─────────────────────────────────────────────
# Yardımcı fonksiyonlar (önbellekleme ile)
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600)  # 1 saat önbellekte tut
def load_and_prepare_data(days):
    """Veriyi çek, temizle ve analiz et. Sonuçları önbellekle."""
    try:
        raw_df = collect_all_data(days=days)
    except Exception:
        raw_df = load_data_from_csv()

    clean_df = clean_data(raw_df)
    stats_df = calculate_statistics(clean_df)
    weekly_df = calculate_weekly_summary(clean_df)
    corr_df = calculate_correlation(clean_df)
    clean_df = calculate_daily_change(clean_df)
    stable_cur, stable_vol = find_most_stable(clean_df)
    best_cur, best_pct = get_best_investment(clean_df)

    return clean_df, stats_df, weekly_df, corr_df, stable_cur, stable_vol, best_cur, best_pct


# ─────────────────────────────────────────────
# Başlık
# ─────────────────────────────────────────────
st.title("💱 Döviz Kurları Analiz Paneli")
st.markdown("*ExchangeRate-API kullanılarak gerçek zamanlı verilerle hazırlanmıştır.*")
st.divider()

# ─────────────────────────────────────────────
# Kenar çubuğu (sidebar)
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Ayarlar")

    days = st.slider(
        "Analiz Dönemi (Gün)",
        min_value=7,
        max_value=60,
        value=30,
        step=7,
        help="Kaç günlük tarihsel veri analiz edilsin?"
    )

    st.divider()

    # Anlık kurlar
    st.subheader("📊 Anlık Kurlar")
    try:
        with st.spinner("Kurlar güncelleniyor..."):
            rates = get_latest_rates()
        for currency, rate in rates.items():
            st.metric(label=f"1 {currency}", value=f"{rate:.4f} TRY")
    except Exception as e:
        st.error(f"Anlık kur alınamadı: {e}")

    st.divider()
    st.caption("Veri: ExchangeRate-API | Son güncelleme: anlık")

# ─────────────────────────────────────────────
# Ana veriyi yükle
# ─────────────────────────────────────────────
with st.spinner("Veriler yükleniyor, lütfen bekleyin..."):
    try:
        (clean_df, stats_df, weekly_df, corr_df,
         stable_cur, stable_vol, best_cur, best_pct) = load_and_prepare_data(days)
        data_loaded = True
    except Exception as e:
        st.error(f"Veri yüklenemedi: {e}")
        st.info("Lütfen önce main.py'yi çalıştırarak veri oluşturun.")
        data_loaded = False
        st.stop()

# ─────────────────────────────────────────────
# Sekmeler
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Genel Bakış", "📈 Grafikler", "🔬 Analiz & Rapor"])

# ══════════════════════════════════════════
# SEKME 1: Genel Bakış
# ══════════════════════════════════════════
with tab1:
    st.subheader("Dönem Özeti")

    # Üst metrikler
    col1, col2, col3 = st.columns(3)
    col1.metric("Analiz Dönemi", f"{days} Gün")
    col2.metric("Takip Edilen Döviz", str(clean_df["para_birimi"].nunique()))
    col3.metric("Toplam Veri Noktası", str(len(clean_df)))

    st.divider()

    # En stabil ve en kazandıran bilgisi
    col4, col5 = st.columns(2)
    with col4:
        st.success(f"🏆 En Stabil Döviz: **{stable_cur}**\nVolatilite: %{stable_vol:.4f}")
    with col5:
        sign = "📈" if best_pct >= 0 else "📉"
        st.info(f"{sign} En Çok Değer Kazanan: **{best_cur}**\nDeğişim: %{best_pct:+.2f}")

    st.divider()

    # İstatistik tablosu
    st.subheader("İstatistiksel Özet")
    st.dataframe(
        stats_df.style.highlight_max(
            subset=["Toplam Değişim (%)"], color="#d5f5e3"
        ).highlight_min(
            subset=["Volatilite (%)"], color="#d6eaf8"
        ),
        use_container_width=True
    )

    # Ham veri önizleme
    st.subheader("Ham Veri Önizleme")
    currencies = st.multiselect(
        "Döviz seç:",
        options=clean_df["para_birimi"].unique().tolist(),
        default=clean_df["para_birimi"].unique().tolist()
    )
    filtered_df = clean_df[clean_df["para_birimi"].isin(currencies)]
    st.dataframe(filtered_df[["tarih", "para_birimi", "kur", "aykiri_deger"]].tail(50),
                 use_container_width=True)

# ══════════════════════════════════════════
# SEKME 2: Grafikler
# ══════════════════════════════════════════
with tab2:
    st.subheader("Veri Görselleştirmeleri")

    # Grafik 1: Çizgi grafik
    st.markdown("#### 📉 Zaman Serisi")
    fig1 = plot_line_chart(clean_df, save=False)
    st.pyplot(fig1)

    st.divider()

    # Grafik 2: Boxplot
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 📦 Kur Dağılımı (Boxplot)")
        fig2 = plot_boxplot(clean_df, save=False)
        st.pyplot(fig2)

    # Grafik 3: Heatmap
    with col_b:
        st.markdown("#### 🌡️ Korelasyon Heatmap")
        fig3 = plot_heatmap(corr_df, save=False)
        st.pyplot(fig3)

    st.divider()

    # Grafik 4: Bar grafik
    st.markdown("#### 📊 Toplam Değişim (%)")
    fig4 = plot_daily_change_bar(clean_df, save=False)
    st.pyplot(fig4)

# ══════════════════════════════════════════
# SEKME 3: Analiz & Rapor
# ══════════════════════════════════════════
with tab3:
    st.subheader("🔬 Araştırma Sorusu Analizi")

    st.markdown("""
    > **Araştırma Sorusu:**
    > *"Son 30 günde USD, EUR, GBP, JPY ve CHF'den hangisi
    > Türk Lirası karşısında en stabil seyirde oldu?
    > Hangisi en çok değer kazandırdı?"*
    """)

    st.divider()

    col6, col7 = st.columns(2)
    with col6:
        st.markdown("### 🧘 Stabilite Analizi")
        st.markdown(f"""
        **Yöntem:** Günlük değişimlerin standart sapması (volatilite)

        - En düşük volatilite = En stabil döviz
        - **Sonuç: {stable_cur}** (%{stable_vol:.4f} volatilite)

        Bu döviz, TL karşısında en az dalgalanma gösterdi.
        """)

    with col7:
        st.markdown("### 💰 Yatırım Analizi")
        st.markdown(f"""
        **Yöntem:** Dönem başından sonuna toplam değişim yüzdesi

        - En yüksek değişim = En çok değer kazandıran
        - **Sonuç: {best_cur}** (%{best_pct:+.2f})

        Bu döviz, dönem boyunca en yüksek getiriyi sağladı.
        """)

    st.divider()

    # Haftalık özet tablosu
    st.subheader("📅 Haftalık Ortalamalar")
    st.dataframe(weekly_df, use_container_width=True)

    st.divider()

    # Döviz çevirici
    st.subheader("🔄 Döviz Çevirici")
    conv_col1, conv_col2, conv_col3 = st.columns(3)
    with conv_col1:
        amount = st.number_input("Miktar", min_value=0.01, value=100.0, step=10.0)
    with conv_col2:
        from_cur = st.selectbox("Kaynak", options=["TRY"] + list(rates.keys()) if 'rates' in dir() else ["TRY", "USD", "EUR"])
    with conv_col3:
        to_cur = st.selectbox("Hedef", options=list(rates.keys()) + ["TRY"] if 'rates' in dir() else ["USD", "EUR", "TRY"])

    try:
        if 'rates' in dir() and rates:
            if from_cur == "TRY" and to_cur in rates:
                converted = amount / rates[to_cur]
            elif from_cur in rates and to_cur == "TRY":
                converted = amount * rates[from_cur]
            elif from_cur in rates and to_cur in rates:
                converted = amount * (rates[from_cur] / rates[to_cur])
            else:
                converted = amount
            st.success(f"**{amount:.2f} {from_cur} = {converted:.4f} {to_cur}**")
    except Exception:
        st.warning("Döviz çevirici için anlık kur verisi gereklidir.")

    st.divider()

    # Excel raporu indir
    st.subheader("📥 Excel Raporu İndir")
    if st.button("📊 Excel Raporu Oluştur ve İndir", type="primary"):
        with st.spinner("Excel raporu hazırlanıyor..."):
            try:
                excel_path = create_excel_report(
                    df=clean_df,
                    stats_df=stats_df,
                    weekly_df=weekly_df,
                    stable_currency=stable_cur,
                    stable_vol=stable_vol,
                    best_currency=best_cur,
                    best_pct=best_pct
                )
                with open(excel_path, "rb") as f:
                    st.download_button(
                        label="⬇️ İndir",
                        data=f,
                        file_name=os.path.basename(excel_path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                st.success("Excel raporu hazır!")
            except Exception as e:
                st.error(f"Excel oluşturulamadı: {e}")
