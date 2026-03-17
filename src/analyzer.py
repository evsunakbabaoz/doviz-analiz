"""
analyzer.py
-----------
İstatistiksel analizleri yapan modül.
Görev: Ortalama, değişim yüzdesi, volatilite, karşılaştırmalı analiz.
"""

import pandas as pd
import numpy as np


def calculate_statistics(df):
    """
    Her döviz için temel istatistikleri hesaplar.
    Döndürür: DataFrame (özet istatistikler)
    """
    results = []

    for currency in df["para_birimi"].unique():
        sub = df[df["para_birimi"] == currency].copy()
        sub = sub.sort_values("tarih")
        rates = sub["kur"]

        # Dönem başı ve sonu
        first_rate = rates.iloc[0]
        last_rate = rates.iloc[-1]

        # Değişim hesaplamaları
        total_change = last_rate - first_rate
        total_change_pct = ((last_rate - first_rate) / first_rate) * 100

        # Volatilite: Günlük değişimlerin standart sapması
        daily_returns = rates.pct_change().dropna()
        volatility = daily_returns.std() * 100  # Yüzde olarak

        # En iyi ve en kötü gün
        daily_change = rates.diff()
        best_day_idx = daily_change.idxmax()
        worst_day_idx = daily_change.idxmin()

        results.append({
            "Para Birimi": currency,
            "Dönem Başı (TRY)": round(first_rate, 4),
            "Dönem Sonu (TRY)": round(last_rate, 4),
            "Ortalama (TRY)": round(rates.mean(), 4),
            "En Düşük (TRY)": round(rates.min(), 4),
            "En Yüksek (TRY)": round(rates.max(), 4),
            "Toplam Değişim (TRY)": round(total_change, 4),
            "Toplam Değişim (%)": round(total_change_pct, 2),
            "Volatilite (%)": round(volatility, 4),
            "En İyi Gün": sub.loc[best_day_idx, "tarih"].strftime("%Y-%m-%d") if best_day_idx in sub.index else "-",
            "En Kötü Gün": sub.loc[worst_day_idx, "tarih"].strftime("%Y-%m-%d") if worst_day_idx in sub.index else "-",
        })

    return pd.DataFrame(results)


def calculate_weekly_summary(df):
    """
    Haftalık bazda ortalama kur hesaplar.
    Excel raporu için özet sekme içeriği.
    """
    df = df.copy()
    df["hafta"] = df["tarih"].dt.to_period("W").astype(str)

    weekly = df.groupby(["hafta", "para_birimi"])["kur"].agg(
        Ortalama="mean",
        En_Dusuk="min",
        En_Yuksek="max"
    ).round(4).reset_index()

    weekly.columns = ["Hafta", "Para Birimi", "Ortalama (TRY)", "En Düşük (TRY)", "En Yüksek (TRY)"]
    return weekly


def calculate_daily_change(df):
    """
    Günlük değişim yüzdelerini hesaplar.
    Grafik ve volatilite analizi için kullanılır.
    """
    df = df.copy()
    df = df.sort_values(["para_birimi", "tarih"])
    df["gunluk_degisim_pct"] = df.groupby("para_birimi")["kur"].pct_change() * 100
    df["gunluk_degisim_pct"] = df["gunluk_degisim_pct"].round(4)
    return df


def find_most_stable(df):
    """
    Araştırma sorusunu cevaplar:
    'Hangi döviz TL karşısında en stabil seyretti?'
    En düşük volatiliteye sahip dövizi döndürür.
    """
    stats = calculate_statistics(df)
    most_stable = stats.loc[stats["Volatilite (%)"].idxmin()]
    return most_stable["Para Birimi"], most_stable["Volatilite (%)"]


def calculate_correlation(df):
    """
    Dövizler arası korelasyon matrisini hesaplar.
    Heatmap için kullanılır.
    """
    pivot = df.pivot_table(index="tarih", columns="para_birimi", values="kur")
    correlation = pivot.corr().round(4)
    return correlation


def get_best_investment(df):
    """
    Dönem başından sonuna en çok değer kazanan dövizi bulur.
    """
    stats = calculate_statistics(df)
    best = stats.loc[stats["Toplam Değişim (%)"].idxmax()]
    return best["Para Birimi"], best["Toplam Değişim (%)"]


# --- Test ---
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))

    print("=== analyzer.py TEST ===")

    # Sahte veriyle test
    import numpy as np
    from datetime import datetime, timedelta

    records = []
    base_date = datetime(2024, 1, 1)
    for i in range(30):
        for currency, base in [("USD", 32), ("EUR", 35), ("GBP", 41)]:
            records.append({
                "tarih": base_date + timedelta(days=i),
                "kur": round(base + np.random.uniform(-0.5, 0.5), 4),
                "para_birimi": currency,
                "aykiri_deger": False
            })

    df = pd.DataFrame(records)

    print("\nTemel istatistikler:")
    stats = calculate_statistics(df)
    print(stats[["Para Birimi", "Ortalama (TRY)", "Toplam Değişim (%)", "Volatilite (%)"]].to_string(index=False))

    currency, vol = find_most_stable(df)
    print(f"\nEn stabil döviz: {currency} (volatilite: %{vol:.4f})")

    best_cur, best_pct = get_best_investment(df)
    print(f"En çok değer kazanan: {best_cur} (%{best_pct:.2f})")
