import requests
try:
    response = requests.get("https://www.google.com", timeout=5)
    print(f"Internet Status: {response.status_code} - Success!")
except Exception as e:
    print(f"Internet Connection Error: {e}")

    