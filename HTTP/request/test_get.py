import requests

response = requests.get("https://profeinformatica101.github.io/mi-web-estatica/")
if response.status_code == 200:
    print(response.text)
else:
    print(f"Error: {response.status_code}")