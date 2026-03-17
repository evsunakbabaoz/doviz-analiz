"""
main.py
-------
Projeyi başlatan ana dosya.
Spyder'da bu dosyayı çalıştır (F5) → pipeline başlar.

Kullanım:
    Spyder'da: F5 tuşuna bas
    Terminal:  python main.py
               python main.py --days 7   (7 günlük veri için)
"""

import sys
import os

# src klasörünü Python path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from automation import run_full_pipeline


def main():
    """Ana giriş noktası."""

    # Komut satırından gün sayısı alınabilir: python main.py --days 14
    days = 30
    if "--days" in sys.argv:
        try:
            idx = sys.argv.index("--days")
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("UYARI: --days için geçerli bir sayı girilmedi. Varsayılan: 30 gün")

    print(f"Döviz Analiz Paneli başlatılıyor... ({days} günlük veri)")
    print(f"Çalışma dizini: {os.getcwd()}")
    print()

    try:
        results = run_full_pipeline(days=days)

        # Özet yazdır
        print("\n--- ÖZET ---")
        if "clean_df" in results:
            df = results["clean_df"]
            print(f"Toplam veri: {len(df)} satır")
            print(f"Takip edilen dövizler: {', '.join(df['para_birimi'].unique())}")

        if "stable_currency" in results:
            print(f"En stabil: {results['stable_currency']} "
                  f"(volatilite: %{results['stable_volatility']:.4f})")

        if "best_currency" in results:
            print(f"En çok kazandıran: {results['best_currency']} "
                  f"(%{results['best_pct']:+.2f})")

        if "excel_path" in results:
            print(f"Excel raporu: {results['excel_path']}")

        print("\nStreamlit arayüzü için: terminalde 'streamlit run app.py' yazın")

    except ConnectionError:
        print("\nHATA: İnternet bağlantısı yok!")
        print("Lütfen bağlantınızı kontrol edip tekrar deneyin.")
        sys.exit(1)
    except Exception as e:
        print(f"\nBeklenmeyen hata: {e}")
        sys.exit(1)


# Bu dosya doğrudan çalıştırıldığında main() fonksiyonu çağrılır
if __name__ == "__main__":
    main()
