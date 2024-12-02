def contar_palabras(texto):
    palabras = texto.split()
    return len(palabras)

def contar_caracteres(texto):
    return len(texto)

def frecuencia_palabras(texto):
    palabras = texto.split()
    frecuencia = {}
    for palabra in palabras:
        palabra = palabra.lower().strip(".,!?()[]{}\"'")
        if palabra in frecuencia:
            frecuencia[palabra] += 1
        else:
            frecuencia[palabra] = 1
    return frecuencia

def mostrar_resultados(texto):
    print("\n=== RESULTADOS DEL ANÁLISIS ===")
    print(f"Cantidad de palabras: {contar_palabras(texto)}")
    print(f"Cantidad de caracteres (incluyendo espacios): {contar_caracteres(texto)}")
    print("\nFrecuencia de palabras:")
    for palabra, frecuencia in frecuencia_palabras(texto).items():
        print(f"{palabra}: {frecuencia}")
        
# Programa principal
def main():
    print("=== BIENVENIDO AL ANALIZADOR DE TEXTO ===")
    texto = input("Introduce el texto a analizar:\n")
    if texto.strip():
        mostrar_resultados(texto)
    else:
        print("El texto introducido está vacío. Por favor, intenta de nuevo.")

# Ejecutar el programa
if __name__ == "__main__":
    main()
