"""
visualizer.py
-------------
Grafikleri oluşturan modül.
Görev: En az 3 farklı görselleştirme (çizgi, boxplot, heatmap + bar).
"""

import matplotlib
matplotlib.use("Agg")  # GUI olmayan ortamlar için (Spyder dışı çalışmada gerekli)
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

# Grafiklerin kaydedileceği klasör
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")

# Genel stil ayarları
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.family"] = "DejaVu Sans"


def plot_line_chart(df, save=True):
    """
    GRAFİK 1: Çizgi Grafik
    Tüm dövizlerin zaman içindeki TRY değerini gösterir.
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    for currency in df["para_birimi"].unique():
        sub = df[df["para_birimi"] == currency].sort_values("tarih")
        ax.plot(sub["tarih"], sub["kur"], label=currency, linewidth=2, marker="o",
                markersize=3)

    ax.set_title("Döviz Kurları - Zaman Serisi (TRY Bazlı)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Tarih")
    ax.set_ylabel("Kur (1 Döviz = ? TRY)")
    ax.legend(title="Para Birimi", loc="upper left")
    ax.xaxis.set_major_locator(plt.MaxNLocator(8))
    plt.xticks(rotation=30)
    plt.tight_layout()

    if save:
        path = _save_figure(fig, "grafik1_zaman_serisi.png")
        print(f"  Grafik 1 kaydedildi: {path}")
    return fig


def plot_boxplot(df, save=True):
    """
    GRAFİK 2: Boxplot
    Her dövizin kur dağılımını ve aykırı değerleri gösterir.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    sns.boxplot(
        data=df,
        x="para_birimi",
        y="kur",
        ax=ax,
        palette="Set2",
        width=0.5,
        flierprops={"marker": "o", "markerfacecolor": "red", "markersize": 5}
    )

    ax.set_title("Döviz Kur Dağılımı - Boxplot (TRY Bazlı)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Para Birimi")
    ax.set_ylabel("Kur (TRY)")
    plt.tight_layout()

    if save:
        path = _save_figure(fig, "grafik2_boxplot.png")
        print(f"  Grafik 2 kaydedildi: {path}")
    return fig


def plot_heatmap(correlation_df, save=True):
    """
    GRAFİK 3: Korelasyon Heatmap
    Dövizler arasındaki ilişkiyi renkli matris olarak gösterir.
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    sns.heatmap(
        correlation_df,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        center=0,
        vmin=-1,
        vmax=1,
        ax=ax,
        linewidths=0.5,
        square=True
    )

    ax.set_title("Dövizler Arası Korelasyon Matrisi", fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save:
        path = _save_figure(fig, "grafik3_heatmap.png")
        print(f"  Grafik 3 kaydedildi: {path}")
    return fig


def plot_daily_change_bar(df, save=True):
    """
    GRAFİK 4 (Bonus): Bar Grafik
    Her dövizin toplam dönem değişimini gösterir.
    """
    # Her döviz için toplam değişim yüzdesi hesapla
    summary = []
    for currency in df["para_birimi"].unique():
        sub = df[df["para_birimi"] == currency].sort_values("tarih")
        first = sub["kur"].iloc[0]
        last = sub["kur"].iloc[-1]
        change_pct = ((last - first) / first) * 100
        summary.append({"Para Birimi": currency, "Değişim (%)": round(change_pct, 2)})

    summary_df = pd.DataFrame(summary).sort_values("Değişim (%)", ascending=False)

    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in summary_df["Değişim (%)"]]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(summary_df["Para Birimi"], summary_df["Değişim (%)"], color=colors, edgecolor="white")

    # Değerleri barların üstüne yaz
    for bar, val in zip(bars, summary_df["Değişim (%)"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"%{val:+.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("Dönem Toplam Değişim Yüzdesi (%)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Para Birimi")
    ax.set_ylabel("Değişim (%)")
    plt.tight_layout()

    if save:
        path = _save_figure(fig, "grafik4_degisim_bar.png")
        print(f"  Grafik 4 kaydedildi: {path}")
    return fig


def create_all_charts(df, correlation_df):
    """
    Tüm grafikleri tek seferde oluşturur.
    automation.py tarafından çağrılır.
    """
    print("Grafikler oluşturuluyor...")
    os.makedirs(REPORTS_DIR, exist_ok=True)

    plot_line_chart(df)
    plot_boxplot(df)
    plot_heatmap(correlation_df)
    plot_daily_change_bar(df)

    print("  Tüm grafikler oluşturuldu.")


def _save_figure(fig, filename):
    """Grafik dosyasını reports klasörüne kaydeder."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, filename)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


# --- Test ---
if __name__ == "__main__":
    import numpy as np
    from datetime import datetime, timedelta

    print("=== visualizer.py TEST ===")

    records = []
    base_date = datetime(2024, 1, 1)
    for i in range(30):
        for currency, base in [("USD", 32), ("EUR", 35), ("GBP", 41), ("JPY", 0.22)]:
            records.append({
                "tarih": base_date + timedelta(days=i),
                "kur": round(base * (1 + np.random.uniform(-0.02, 0.02)), 4),
                "para_birimi": currency,
                "aykiri_deger": False
            })

    df = pd.DataFrame(records)
    df["tarih"] = pd.to_datetime(df["tarih"])

    pivot = df.pivot_table(index="tarih", columns="para_birimi", values="kur")
    corr = pivot.corr().round(4)

    create_all_charts(df, corr)
    print("\nTüm grafikler 'reports/' klasörüne kaydedildi.")
