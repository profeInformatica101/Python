#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

# ==============================
# CONFIG
# ==============================
REPO = "plantilla_endes"
CSV_SALIDA = "correccion_endes.csv"

# Cierre: miércoles, 18 de marzo de 2026, 13:15 hora peninsular española
# El 18 de marzo de 2026 España está en CET (UTC+1), por tanto:
# 13:15 CET = 12:15 UTC
FECHA_CIERRE = datetime(2026, 3, 18, 13, 15, 0, tzinfo=ZoneInfo("Europe/Madrid"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Correccion-ENDES"
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

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

RAMAS_REQUERIDAS = [
    "codigo_sin_pruebas",
    "prueba/comercial",
    "dev/contratarEmpleado",
    "prueba/plantilla",
    "doc/javadoc",
    "main",
]

# ==============================
# FUNCIONES AUXILIARES
# ==============================
def parse_github_date(date_str: str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def gh_get(url: str, params=None):
    try:
        r = SESSION.get(url, params=params, timeout=20)
        return r
    except requests.RequestException as e:
        return e


def repo_existe(user: str):
    url = f"https://api.github.com/repos/{user}/{REPO}"
    r = gh_get(url)
    if isinstance(r, Exception):
        return False, f"Error de red: {r}"
    if r.status_code == 200:
        return True, ""
    if r.status_code == 404:
        return False, "Repo no encontrado"
    return False, f"GitHub API {r.status_code}: {r.text[:120]}"


def obtener_ramas(user: str):
    url = f"https://api.github.com/repos/{user}/{REPO}/branches"
    r = gh_get(url, params={"per_page": 100})
    if isinstance(r, Exception):
        return [], f"Error de red: {r}"
    if r.status_code != 200:
        return [], f"GitHub API {r.status_code}: {r.text[:120]}"
    try:
        data = r.json()
        return [b["name"] for b in data], ""
    except Exception as e:
        return [], f"Error parseando ramas: {e}"


def ultimo_commit_de_rama(user: str, branch: str):
    url = f"https://api.github.com/repos/{user}/{REPO}/commits"
    r = gh_get(url, params={"sha": branch, "per_page": 1})
    if isinstance(r, Exception):
        return None, f"Error de red en commits de {branch}: {r}"
    if r.status_code != 200:
        return None, f"GitHub API {r.status_code} en commits de {branch}: {r.text[:120]}"
    try:
        data = r.json()
        if not data:
            return None, ""
        fecha_str = data[0]["commit"]["committer"]["date"]
        return parse_github_date(fecha_str), ""
    except Exception as e:
        return None, f"Error parseando commits de {branch}: {e}"


def formatear_fecha(dt):
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def comprobar_fuera_de_plazo(user: str, ramas_existentes):
    ramas_fuera = []
    ultima_fecha = None
    errores = []

    for rama in ramas_existentes:
        fecha, err = ultimo_commit_de_rama(user, rama)
        if err:
            errores.append(err)
            continue

        if fecha is None:
            continue

        if ultima_fecha is None or fecha > ultima_fecha:
            ultima_fecha = fecha

        if fecha > FECHA_CIERRE:
            ramas_fuera.append(f"{rama} ({formatear_fecha(fecha)})")

    return ramas_fuera, ultima_fecha, " | ".join(errores)


def evaluar(alumno):
    user = alumno["github_user"].strip()
    info = alumno["info"]

    resultado = {
        "info": info,
        "usuario": user if user else "SIN_USUARIO",
        "repo": "NO",
        "ramas_ok": "0/6",
        "nota": 0.00,
        "fuera_de_plazo": "NO",
        "detalle_fuera_de_plazo": "",
        "ultimo_commit_repo": "",
        "error_api": "",
    }

    if not user:
        resultado["error_api"] = "Alumno sin usuario GitHub en el JSON"
        return resultado

    existe, err_repo = repo_existe(user)
    if not existe:
        resultado["error_api"] = err_repo
        return resultado

    resultado["repo"] = "SI"

    ramas, err_ramas = obtener_ramas(user)
    if err_ramas:
        resultado["error_api"] = err_ramas
        return resultado

    ok = sum(1 for rama in RAMAS_REQUERIDAS if rama in ramas)
    resultado["ramas_ok"] = f"{ok}/6"
    resultado["nota"] = round((ok / 6) * 10, 2)

    ramas_existentes = [rama for rama in RAMAS_REQUERIDAS if rama in ramas]
    ramas_fuera, ultima_fecha, err_commits = comprobar_fuera_de_plazo(user, ramas_existentes)

    if ramas_fuera:
        resultado["fuera_de_plazo"] = "SI"
        resultado["detalle_fuera_de_plazo"] = " | ".join(ramas_fuera)

    if ultima_fecha:
        resultado["ultimo_commit_repo"] = formatear_fecha(ultima_fecha)

    errores = []
    if err_ramas:
        errores.append(err_ramas)
    if err_commits:
        errores.append(err_commits)
    resultado["error_api"] = " | ".join([e for e in errores if e])

    return resultado


def guardar_csv(resultados, ruta):
    campos = [
        "info",
        "usuario",
        "repo",
        "ramas_ok",
        "nota",
        "fuera_de_plazo",
        "detalle_fuera_de_plazo",
        "ultimo_commit_repo",
        "error_api",
    ]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)


def main():
    resultados = []

    print(f"Token cargado: {'SI' if GITHUB_TOKEN else 'NO'}")
    print(f"Fecha de cierre UTC: {formatear_fecha(FECHA_CIERRE)}\n")

    for i, alumno in enumerate(alumnos, start=1):
        user = alumno["github_user"].strip()
        info = alumno["info"]
        print(f"[{i:02d}/{len(alumnos)}] Corrigiendo {info} ({user if user else 'SIN_USUARIO'})...")

        res = evaluar(alumno)
        resultados.append(res)

        # baja un poco la frecuencia para evitar rate limits
        time.sleep(0.25)

    guardar_csv(resultados, CSV_SALIDA)

    print("\n✅ Corrección terminada")
    print(f"📄 Archivo generado: {CSV_SALIDA}")


if __name__ == "__main__":
    main()
