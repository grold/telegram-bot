import requests
import json

def test_rbc():
    url = "https://www.rbc.ru/quote/v2/publisher/ticker/item/USDRUB"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.rbc.ru/quote/",
        "Origin": "https://www.rbc.ru"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content Type: {response.headers.get('Content-Type')}")
        if "application/json" in response.headers.get("Content-Type", ""):
            print("Response is JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Response is not JSON. Start of content:")
            print(response.text[:500])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_rbc()
