#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import csv
import os
import time

# ==============================
# CONFIG
# ==============================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Check-Ramas-DAW"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

CSV_SALIDA = "ramas_daw.csv"

# ==============================
# REPOS Y RAMAS
# ==============================
REPO_CLOUD = "cloud_edge_daw"
REPO_IA = "ia_daw"

RAMAS_CLOUD = [
    "tarea/cloud-a-b",
    "tarea/cloud-c-d-e"
]

RAMAS_IA = [
    "tarea/ia-a",
    "tarea/ia-bc",
    "tarea/ia-de",
    "tarea/ia-f"
]

# ==============================
# ALUMNOS
# ==============================
alumnos = [
    {"github_user": "Joselitoo777", "info": "AM, J"},
    {"github_user": "Alonsosanchezlaura-maker", "info": "AS, L"},
    {"github_user": "dbarfer2609", "info": "BF, D"},
    {"github_user": "LopeDelgado", "info": "DS, L"},
    {"github_user": "dominguezobreroadrian", "info": "DO, A"},
    {"github_user": "", "info": "GD, Á"},
    {"github_user": "", "info": "HG, A"},
    {"github_user": "ManuelFLopez", "info": "LI, MF"},
    {"github_user": "daanielalpz", "info": "LL, D"},
    {"github_user": "", "info": "LP, L"},
    {"github_user": "Martinezsalgadomanuel-cyber", "info": "MS, M"},
    {"github_user": "joseluisms24", "info": "MS, JL"},
    {"github_user": "saraniievess", "info": "NI, S"},
    {"github_user": "ortegaromerodaniel", "info": "OR, D"},
    {"github_user": "JoelParrondo", "info": "PC, J"},
    {"github_user": "Programador-123", "info": "PG, MÁ"},
    {"github_user": "josecarlosquiroga05", "info": "QQ, JC"},
    {"github_user": "MarcoRiv27", "info": "RF, M"},
    {"github_user": "JoseManuel737", "info": "RR, JM"},
    {"github_user": "carlosruizgarrido", "info": "RG, CM"},
    {"github_user": "pruizsalado", "info": "RS, P"},
    {"github_user": "", "info": "SA, C"},
    {"github_user": "suareznicolas7", "info": "SP, N"},
    {"github_user": "", "info": "UR, DF"},
    {"github_user": "franciscovalencia14", "info": "VL, F"},
    {"github_user": "JoaquinVasa", "info": "VS, J"},
    {"github_user": "gabrivillegas", "info": "VF, G"},
]

# ==============================
# FUNCIONES
# ==============================
def gh_get(url):
    try:
        return SESSION.get(url, timeout=15)
    except:
        return None


def obtener_ramas(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/branches"
    r = gh_get(url + "?per_page=100")

    if not r or r.status_code != 200:
        return []

    return [b["name"] for b in r.json()]


# ==============================
# EVALUACIÓN
# ==============================
def evaluar(alumno):

    user = alumno["github_user"].strip()
    info = alumno["info"]

    resultado = {
        "info": info,
        "usuario": user if user else "SIN_USUARIO",

        # CLOUD
        "cloud_ok": 0,
        "cloud_faltan": "",

        # IA
        "ia_ok": 0,
        "ia_faltan": "",
    }

    if not user:
        return resultado

    # CLOUD
    ramas_cloud = obtener_ramas(user, REPO_CLOUD)
    ok_cloud = [r for r in RAMAS_CLOUD if r in ramas_cloud]
    faltan_cloud = [r for r in RAMAS_CLOUD if r not in ramas_cloud]

    resultado["cloud_ok"] = len(ok_cloud)
    resultado["cloud_faltan"] = ", ".join(faltan_cloud)

    # IA
    ramas_ia = obtener_ramas(user, REPO_IA)
    ok_ia = [r for r in RAMAS_IA if r in ramas_ia]
    faltan_ia = [r for r in RAMAS_IA if r not in ramas_ia]

    resultado["ia_ok"] = len(ok_ia)
    resultado["ia_faltan"] = ", ".join(faltan_ia)

    return resultado


# ==============================
# CSV
# ==============================
def guardar_csv(resultados):

    campos = [
        "info",
        "usuario",
        "cloud_ok",
        "cloud_faltan",
        "ia_ok",
        "ia_faltan"
    ]

    with open(CSV_SALIDA, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)


# ==============================
# MAIN
# ==============================
def main():

    resultados = []

    print("🔍 Comprobando ramas CLOUD + IA...\n")

    for i, alumno in enumerate(alumnos, 1):
        user = alumno["github_user"] or "SIN_USUARIO"
        print(f"[{i:02d}] {user}")

        res = evaluar(alumno)
        resultados.append(res)

        time.sleep(0.3)

    guardar_csv(resultados)

    print("\n✅ CSV generado: ramas_daw.csv")


if __name__ == "__main__":
    main()
