import requests
TOKEN = "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4"
CHAT_ID = "7246234100"
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": "Test message from agent"}
response = requests.post(url, json=payload)
print(response.json())
