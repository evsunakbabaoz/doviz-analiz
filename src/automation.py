"""
automation.py
-------------
Tüm pipeline'ı sırayla çalıştıran modül.
Görev: Veri topla -> Temizle -> Analiz et -> Grafik çiz -> Excel raporu üret.
Bu dosya main.py tarafından çağrılır.
"""

import sys
import os

# src klasörünün üst dizinini Python path'e ekle
sys.path.append(os.path.dirname(__file__))

from data_collector import collect_all_data
from data_cleaner import clean_data, get_clean_summary
from analyzer import (
    calculate_statistics,
    calculate_weekly_summary,
    calculate_correlation,
    find_most_stable,
    get_best_investment
)
from visualizer import create_all_charts
from excel_report import create_excel_report


def run_full_pipeline(days=30):
    """
    Tam pipeline'ı çalıştırır.
    Parametre:
        days: Kaç günlük tarihsel veri çekileceği
    Döndürür:
        dict: Tüm sonuçları içeren sözlük (app.py'de kullanılır)
    """

    print("=" * 50)
    print("  DÖVIZ ANALİZ PİPELINE'I BAŞLADI")
    print("=" * 50)

    results = {}

    # ADIM 1: Veri Toplama
    print("\n[1/5] Veri toplanıyor...")
    try:
        raw_df = collect_all_data(days=days)
        results["raw_df"] = raw_df
        print(f"  {len(raw_df)} satır veri toplandı.")
    except Exception as e:
        print(f"  HATA: Veri toplanamadı - {e}")
        raise

    # ADIM 2: Veri Temizleme
    print("\n[2/5] Veri temizleniyor...")
    try:
        clean_df = clean_data(raw_df)
        results["clean_df"] = clean_df
    except Exception as e:
        print(f"  HATA: Temizleme başarısız - {e}")
        raise

    # ADIM 3: Analiz
    print("\n[3/5] Analizler yapılıyor...")
    try:
        stats_df = calculate_statistics(clean_df)
        weekly_df = calculate_weekly_summary(clean_df)
        corr_df = calculate_correlation(clean_df)
        stable_cur, stable_vol = find_most_stable(clean_df)
        best_cur, best_pct = get_best_investment(clean_df)

        results["stats_df"] = stats_df
        results["weekly_df"] = weekly_df
        results["corr_df"] = corr_df
        results["stable_currency"] = stable_cur
        results["stable_volatility"] = stable_vol
        results["best_currency"] = best_cur
        results["best_pct"] = best_pct

        print(f"  En stabil döviz: {stable_cur} (volatilite: %{stable_vol:.4f})")
        print(f"  En çok kazandıran: {best_cur} (%{best_pct:+.2f})")
    except Exception as e:
        print(f"  HATA: Analiz başarısız - {e}")
        raise

    # ADIM 4: Grafikleri Oluştur
    print("\n[4/5] Grafikler oluşturuluyor...")
    try:
        create_all_charts(clean_df, corr_df)
    except Exception as e:
        print(f"  UYARI: Grafik oluşturma hatası - {e}")
        # Grafik hatası pipeline'ı durdurmaz

    # ADIM 5: Excel Raporu Üret
    print("\n[5/5] Excel raporu oluşturuluyor...")
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
        results["excel_path"] = excel_path
    except Exception as e:
        print(f"  UYARI: Excel raporu oluşturulamadı - {e}")

    print("\n" + "=" * 50)
    print("  PİPELINE TAMAMLANDI!")
    print("=" * 50)

    return results


# --- Test: Doğrudan çalıştırma ---
if __name__ == "__main__":
    try:
        results = run_full_pipeline(days=30)
        print("\nSonuç anahtarları:", list(results.keys()))
    except Exception as e:
        print(f"\nPipeline hatası: {e}")
