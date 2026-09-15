import requests

# استبدل هذه القيم بمفاتيحك الحقيقية
keys = {
    "MASSIVE": "kddwFWHDr_6K5B3TFjrlYFtpI1jmnfsV",
    "FINNHUB": "d92l1mhr01qpou36m760d92l1mhr01qpou36m76g",
    "FMP": "WzZgK7341EU6gJ6ALUXv7ALgSZbXZkb7"
}

def test_connections():
    print("--- بدأ اختبار الاتصال ---")
    
    # 1. اختبار MASSIVE (Polygon)
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2026-06-01/2026-06-10?adjusted=true&sort=asc&apikey={keys['MASSIVE']}"
        res = requests.get(url, timeout=10)
        print(f"Massive (Polygon): {res.status_code} - {res.text[:100]}")
    except Exception as e:
        print(f"Massive Error: {e}")

    # 2. اختبار FINNHUB
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={keys['FINNHUB']}"
        res = requests.get(url, timeout=10)
        print(f"Finnhub: {res.status_code} - {res.text[:100]}")
    except Exception as e:
        print(f"Finnhub Error: {e}")

    # 3. اختبار FMP
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote-short/AAPL?apikey={keys['FMP']}"
        res = requests.get(url, timeout=10)
        print(f"FMP: {res.status_code} - {res.text[:100]}")
    except Exception as e:
        print(f"FMP Error: {e}")

if __name__ == "__main__":
    test_connections()

    