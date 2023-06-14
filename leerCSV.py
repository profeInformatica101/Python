import csv
import requests

# URL del archivo CSV
url = "https://raw.githubusercontent.com/profeInformatica101/HojasDeCalculo/main/titanic3.csv"

# Realizar la solicitud GET y obtener el contenido del archivo CSV
response = requests.get(url)
content = response.text

# Leer el contenido del archivo CSV y guardar la información en una lista de diccionarios
data = []
csv_reader = csv.DictReader(content.splitlines())
for row in csv_reader:
    data.append(row)

# Imprimir la lista de diccionarios
for item in data:
    print(item)
