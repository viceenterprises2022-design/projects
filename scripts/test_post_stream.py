import requests
import json

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://cryptopanic.com/",
    "Origin": "https://cryptopanic.com",
})

# GET first to get CSRF cookie
print("GETing homepage...")
r1 = session.get("https://cryptopanic.com/")
print("GET Status:", r1.status_code)
csrf_token = session.cookies.get("csrftoken")
print("CSRF Token from cookie:", csrf_token)

if not csrf_token:
    print("Could not get CSRF token!")
    exit(1)

# POST with CSRF token in header
url = "https://cryptopanic.com/web-api/posts/"
headers = {
    "X-CSRFToken": csrf_token,
}

data = {
    "filters": json.dumps({})
}

print("POSTing to web-api...")
r2 = session.post(url, headers=headers, data=data)
print("POST Status Code:", r2.status_code)
try:
    res = r2.json()
    print("Response JSON keys:", res.keys())
    print("Status:", res.get("status"))
    print("Count:", res.get("count"))
    if "s" in res:
        print("Data string length:", len(res["s"]))
        print("Data string prefix:", res["s"][:100])
except Exception as e:
    print("Failed to parse JSON:", e)
    print("Response text length:", len(r2.text))
    print("Response text prefix:", r2.text[:500])
