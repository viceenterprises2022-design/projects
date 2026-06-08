import requests

url = "https://static.cryptopanic.com/static/js/cryptopanic.min.bbf252b11beb.js"
r = requests.get(url)
js = r.text

index = 0
while True:
    index = js.find("getPosts", index)
    if index == -1:
        break
    print(f"Found 'getPosts' at index {index}:")
    print(js[max(0, index-150):min(len(js), index+250)])
    print("-" * 50)
    index += 8
