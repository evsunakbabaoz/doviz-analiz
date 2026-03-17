"""
data_collector.py
-----------------
Frankfurter API'den döviz verisi çeken modül.
Kayıt gerektirmez, API key gerekmez, tarihsel veri destekler.
API: https://www.frankfurter.app
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os

BASE_URL = "https://api.frankfurter.app"

# TRY bazlı takip edilecek dövizler
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF"]

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def get_latest_rates():
    """
    API'den anlık döviz kurlarını çeker.
    Döndürür: dict (para birimi -> TRY kuru)
    """
    try:
        url = f"{BASE_URL}/latest?from=TRY&to={','.join(CURRENCIES)}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        rates = data.get("rates", {})
        # API: 1 TRY = X döviz → biz 1 döviz = Y TRY istiyoruz
        try_rates = {}
        for currency, rate in rates.items():
            if rate and rate != 0:
                try_rates[currency] = round(1 / rate, 4)
        return try_rates

    except requests.exceptions.ConnectionError:
        raise ConnectionError("İnternet bağlantısı kurulamadı.")
    except requests.exceptions.Timeout:
        raise TimeoutError("API isteği zaman aşımına uğradı.")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP Hatası: {e}")


def get_historical_rates(days=30):
    """
    Son N günün tarihsel döviz verilerini çeker.
    Frankfurter API tarih aralığı destekler.
    """
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        url = f"{BASE_URL}/{start_date}..{end_date}?from=TRY&to={','.join(CURRENCIES)}"
        print(f"  API isteği: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        records = []
        for date_str, rates in data.get("rates", {}).items():
            for currency, rate in rates.items():
                if rate and rate != 0:
                    records.append({
                        "tarih": date_str,
                        "kur": round(1 / rate, 4),
                        "para_birimi": currency
                    })

        if not records:
            raise ValueError("API'den veri gelmedi.")

        df = pd.DataFrame(records)
        df["tarih"] = pd.to_datetime(df["tarih"])
        df = df.sort_values(["para_birimi", "tarih"]).reset_index(drop=True)
        return df

    except requests.exceptions.ConnectionError:
        raise ConnectionError("İnternet bağlantısı kurulamadı.")
    except requests.exceptions.Timeout:
        raise TimeoutError("API zaman aşımına uğradı.")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP Hatası: {e}")


def collect_all_data(days=30):
    """
    Tüm veriyi çeker ve CSV'ye kaydeder.
    automation.py tarafından çağrılır.
    """
    print("Veriler API'den çekiliyor (Frankfurter)...")

    df = get_historical_rates(days=days)

    os.makedirs(DATA_DIR, exist_ok=True)
    csv_path = os.path.join(DATA_DIR, "doviz_verileri.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"  {len(df)} satır veri kaydedildi: {csv_path}")

    return df


def load_data_from_csv():
    """Daha önce kaydedilen CSV'den veri yükler."""
    csv_path = os.path.join(DATA_DIR, "doviz_verileri.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError("Veri dosyası bulunamadı. Önce main.py çalıştırın.")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["tarih"] = pd.to_datetime(df["tarih"])
    return df


if __name__ == "__main__":
    print("=== data_collector.py TEST ===")
    try:
        print("\n1) Anlık kurlar:")
        rates = get_latest_rates()
        for k, v in rates.items():
            print(f"   1 {k} = {v} TRY")

        print("\n2) Son 7 günlük tarihsel veri:")
        df = get_historical_rates(days=7)
        print(df.to_string(index=False))
    except Exception as e:
        print(f"HATA: {e}")
