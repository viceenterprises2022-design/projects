import requests

url = "https://static.cryptopanic.com/static/js/cryptopanic.min.bbf252b11beb.js"
r = requests.get(url)
js = r.text

index = 0
while True:
    index = js.find("dcList", index)
    if index == -1:
        break
    print(f"Found 'dcList' at index {index}:")
    print(js[max(0, index-100):min(len(js), index+400)])
    print("-" * 50)
    index += 6
