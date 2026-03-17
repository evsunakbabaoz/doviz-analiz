"""
data_cleaner.py
---------------
Ham veriyi temizleyen ve düzenleyen modül.
Görev: Eksik değerleri doldur, outlier'ları tespit et, formatı standartlaştır.
"""

import pandas as pd
import numpy as np


def clean_data(df):
    """
    Ana temizleme fonksiyonu.
    Tüm temizleme adımlarını sırayla uygular.
    Döndürür: Temizlenmiş DataFrame
    """
    print("Veri temizleniyor...")

    df = df.copy()  # Orijinal veriyi bozmamak için kopya al

    # Adım 1: Sütun isimlerini düzenle
    df = _standardize_columns(df)

    # Adım 2: Tarih sütununu düzelt
    df = _fix_dates(df)

    # Adım 3: Kur değerlerini sayıya çevir
    df = _fix_numeric_values(df)

    # Adım 4: Eksik değerleri doldur
    df = _fill_missing_values(df)

    # Adım 5: Aykırı değerleri işaretle
    df = _flag_outliers(df)

    # Adım 6: Tekrar eden satırları kaldır
    before = len(df)
    df = df.drop_duplicates(subset=["tarih", "para_birimi"])
    after = len(df)
    if before != after:
        print(f"  {before - after} tekrar eden satır kaldırıldı.")

    # Adım 7: Tarihe göre sırala
    df = df.sort_values(["para_birimi", "tarih"]).reset_index(drop=True)

    print(f"  Temizleme tamamlandı. Toplam {len(df)} satır, {df['para_birimi'].nunique()} döviz.")
    return df


def _standardize_columns(df):
    """Sütun isimlerini küçük harfe ve Türkçe'ye çevirir."""
    df.columns = df.columns.str.lower().str.strip()
    return df


def _fix_dates(df):
    """Tarih sütununu datetime formatına çevirir."""
    try:
        df["tarih"] = pd.to_datetime(df["tarih"], errors="coerce")
        # Geçersiz tarihleri kaldır
        invalid_dates = df["tarih"].isna().sum()
        if invalid_dates > 0:
            print(f"  {invalid_dates} geçersiz tarih satırı kaldırıldı.")
        df = df.dropna(subset=["tarih"])
    except Exception as e:
        print(f"  Tarih düzeltme uyarısı: {e}")
    return df


def _fix_numeric_values(df):
    """Kur değerlerini sayısal formata çevirir."""
    df["kur"] = pd.to_numeric(df["kur"], errors="coerce")

    # Sıfır veya negatif kur değerlerini kaldır (mantıksız değerler)
    invalid_rates = (df["kur"] <= 0).sum()
    if invalid_rates > 0:
        print(f"  {invalid_rates} geçersiz kur değeri (≤0) kaldırıldı.")
    df = df[df["kur"] > 0]

    return df


def _fill_missing_values(df):
    """
    Her döviz için eksik değerleri doldurur.
    Forward fill: Önceki günün değerini kullanır (tatil/hafta sonu için mantıklı).
    """
    missing_before = df["kur"].isna().sum()

    if missing_before > 0:
        # Her döviz grubu için ayrı ayrı doldur
        df = df.sort_values(["para_birimi", "tarih"])
        df["kur"] = df.groupby("para_birimi")["kur"].transform(
            lambda x: x.fillna(method="ffill").fillna(method="bfill")
        )
        missing_after = df["kur"].isna().sum()
        print(f"  {missing_before - missing_after} eksik değer dolduruldu.")

    return df


def _flag_outliers(df):
    """
    IQR yöntemiyle aykırı değerleri tespit eder ve işaretler.
    Her döviz için ayrı ayrı hesaplar.
    """
    df["aykiri_deger"] = False

    for currency in df["para_birimi"].unique():
        mask = df["para_birimi"] == currency
        values = df.loc[mask, "kur"]

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = mask & ((df["kur"] < lower_bound) | (df["kur"] > upper_bound))
        df.loc[outlier_mask, "aykiri_deger"] = True

    outlier_count = df["aykiri_deger"].sum()
    if outlier_count > 0:
        print(f"  {outlier_count} aykırı değer tespit edildi ve işaretlendi.")

    return df


def get_clean_summary(df):
    """
    Temizlenmiş verinin özet istatistiklerini döndürür.
    Excel raporu ve Streamlit için kullanılır.
    """
    summary_records = []

    for currency in df["para_birimi"].unique():
        sub = df[df["para_birimi"] == currency]["kur"]

        summary_records.append({
            "Para Birimi": currency,
            "Ortalama Kur (TRY)": round(sub.mean(), 4),
            "En Düşük": round(sub.min(), 4),
            "En Yüksek": round(sub.max(), 4),
            "Std Sapma": round(sub.std(), 4),
            "Veri Sayısı": len(sub),
            "Aykırı Değer Sayısı": int(df[df["para_birimi"] == currency]["aykiri_deger"].sum())
        })

    return pd.DataFrame(summary_records)


# --- Test ---
if __name__ == "__main__":
    print("=== data_cleaner.py TEST ===")

    # Sahte veriyle test
    test_data = pd.DataFrame({
        "tarih": ["2024-01-01", "2024-01-02", None, "2024-01-04", "2024-01-05"],
        "kur":   [32.5, None, 32.8, 99999, 33.1],  # None ve aykırı değer var
        "para_birimi": ["USD"] * 5
    })

    cleaned = clean_data(test_data)
    print("\nTemizlenmiş veri:")
    print(cleaned.to_string(index=False))

    print("\nÖzet istatistikler:")
    print(get_clean_summary(cleaned).to_string(index=False))
