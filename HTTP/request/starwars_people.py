import requests

# URL base de la API de Star Wars

url = "https://swapi.dev/api/people/1/"  # Luke Skywalker
'''
    Planetas: https://swapi.dev/api/planets/1/
    Naves: https://swapi.dev/api/starships/9/

'''
try:
    # Realizar una solicitud GET
    response = requests.get(url)
    if response.status_code == 200:
        # Convertir la respuesta JSON en un diccionario de Python
        data = response.json()
        print(f"Nombre: {data['name']}")
        print(f"Altura: {data['height']} cm")
        print(f"Peso: {data['mass']} kg")
        print(f"Género: {data['gender']}")
        print(f"Nacimiento: {data['birth_year']}")
    else:
        print(f"Error en la solicitud. Código de estado: {response.status_code}")
except Exception as e:
    print(f"Ocurrió un error: {e}")

