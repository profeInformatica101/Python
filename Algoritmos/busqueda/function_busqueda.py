import time
import random

def busqueda_lineal(lista, objetivo):
    for i, elemento in enumerate(lista):
        if elemento == objetivo:
            return i  # Retorna el índice donde se encontró el elemento
    return -1  # Retorna -1 si el elemento no está en la lista


def busqueda_binaria(lista, objetivo):
    inicio = 0
    fin = len(lista) - 1

    while inicio <= fin:
        medio = (inicio + fin) // 2
        if lista[medio] == objetivo:
            return medio
        elif lista[medio] < objetivo:
            inicio = medio + 1
        else:
            fin = medio - 1

    return -1  # Retorna -1 si el elemento no está en la lista


def busqueda_binaria_recursiva(lista, objetivo, inicio, fin):
    if inicio > fin:
        return -1  # Caso base: el elemento no está en la lista

    medio = (inicio + fin) // 2
    if lista[medio] == objetivo:
        return medio
    elif lista[medio] < objetivo:
        return busqueda_binaria_recursiva(lista, objetivo, medio + 1, fin)
    else:
        return busqueda_binaria_recursiva(lista, objetivo, inicio, medio - 1)


# Ejemplo
lista = [number for number in range(1,300)]
print(lista)
# Desordenar lista
random.shuffle(lista)
print(lista)
objetivo = 23

inicio = time.time()  # Tiempo inicial
resultado = busqueda_lineal(lista, objetivo)
fin = time.time()  # Tiempo final
print(f'Elemento encontrado en el índice {resultado}' if resultado != -1 else 'Elemento no encontrado')
print(f'Tiempo de ejecución: {fin - inicio} segundos')


inicio = time.time()  # Tiempo inicial
resultado = busqueda_binaria(lista, objetivo)
fin = time.time()  # Tiempo final
print(f'Elemento encontrado en el índice {resultado}' if resultado != -1 else 'Elemento no encontrado')
print(f'Tiempo de ejecución: {fin - inicio} segundos')


inicio = time.time()  # Tiempo inicial
resultado = busqueda_binaria_recursiva(lista, objetivo, 0, len(lista) - 1)
fin = time.time()  # Tiempo final
print(f'Elemento encontrado en el índice {resultado}' if resultado != -1 else 'Elemento no encontrado')
print(f'Tiempo de ejecución: {fin - inicio} segundos')
