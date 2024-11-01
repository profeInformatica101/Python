import random

# Ejemplo
lista = [number for number in range(1,10)]
print("Lista generada:",lista)

# Desordenar lista
lista_desordenada = lista.copy()
random.shuffle(lista_desordenada)
print("Lista desordenada:",lista_desordenada)


def bubble_sort(lista):
    n = len(lista)
    for i in range(n):
        for j in range(0, n - i - 1):
            if lista[j] > lista[j + 1]:
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
    return lista

print("bubble_sort:", bubble_sort(lista))