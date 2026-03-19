#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import html
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import requests

# ==============================
# CONFIG
# ==============================
REPOS = ["cloud_edge_daw", "ia_daw"]
CSV_SALIDA = "correccion_cloud_ia.csv"
DIR_ENTREGAS = Path("entregas")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Correccion-Cloud-IA"
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

# ==============================
# RAMAS
# ==============================
RAMAS_REQUERIDAS = [
    "tarea/cloud-a-b",
    "tarea/cloud-c-d-e",
    "tarea/ia-a",
    "tarea/ia-bc",
]

# ==============================
# ARCHIVOS OBJETIVO
# ==============================
OBJETIVOS_POR_RAMA = {
    "tarea/cloud-a-b": "tareas/tarea_a_b_cloud_niveles_funciones.md",
    "tarea/cloud-c-d-e": "tareas/tarea_c_d_e_edge_fog_mist_cloud.md",
    "tarea/ia-a": "tareas/tarea_ra4_a_ia_automatizacion.md",
    "tarea/ia-bc": "tareas/tarea_ra4_b_c_ia_bigdata_rentabilidad_valor.md",
}

# ==============================
# UTILIDADES
# ==============================
def sanitizar(texto):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", texto.strip())

def gh_get(url):
    try:
        return SESSION.get(url, timeout=20)
    except Exception as e:
        return e

def escribir(path: Path, txt: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(txt, encoding="utf-8")

def leer(path: Path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except:
        return ""

# ==============================
# GITHUB
# ==============================
def repo_existe(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}"
    r = gh_get(url)
    return not isinstance(r, Exception) and r.status_code == 200

def obtener_ramas(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/branches"
    r = gh_get(url)
    if isinstance(r, Exception) or r.status_code != 200:
        return []
    return [b["name"] for b in r.json()]

# ==============================
# GIT
# ==============================
def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

def git_url(user, repo):
    return f"https://github.com/{user}/{repo}.git"

def clonar(user, repo, destino):
    if destino.exists():
        return True
    destino.parent.mkdir(parents=True, exist_ok=True)
    r = run(["git", "clone", "--depth", "1", git_url(user, repo), str(destino)])
    return r.returncode == 0

def exportar_rama(repo_dir, rama, destino):
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)

    r = run(["git", "archive", rama], cwd=repo_dir)
    if r.returncode != 0:
        return False

    p = subprocess.Popen(["tar", "-x", "-C", str(destino)], stdin=subprocess.PIPE)
    p.communicate(input=r.stdout.encode())
    return True

# ==============================
# EVALUACIÓN
# ==============================
def evaluar_archivo(path: Path):
    if not path.exists():
        return 0, "NO EXISTE"

    contenido = leer(path).strip()
    if len(contenido) < 20:
        return 0.5, "VACÍO / MUY CORTO"

    return 1, "OK"

def evaluar_repo(user, repo, carpeta_base):
    resultado = {}
    ramas = obtener_ramas(user, repo)

    if not ramas:
        return None

    repo_dir = carpeta_base / repo
    if not clonar(user, repo, repo_dir):
        return None

    puntos = 0

    for rama in RAMAS_REQUERIDAS:
        if rama not in ramas:
            resultado[rama] = "NO EXISTE"
            continue

        destino = repo_dir / sanitizar(rama)
        exportar_rama(repo_dir, rama, destino)

        ruta = destino / OBJETIVOS_POR_RAMA[rama]
        nota, estado = evaluar_archivo(ruta)

        puntos += nota
        resultado[rama] = estado

    return puntos, resultado

# ==============================
# HTML
# ==============================
def generar_html(carpeta, info, resultados):
    bloques = []

    for repo, data in resultados.items():
        bloques.append(f"<h2>{repo}</h2><pre>{html.escape(str(data))}</pre>")

    html_final = f"""
    <html>
    <body>
    <h1>{info}</h1>
    {''.join(bloques)}
    </body>
    </html>
    """

    escribir(carpeta / "resultado.html", html_final)

# ==============================
# MAIN
# ==============================
def main():
    resultados_csv = []

    for alumno in alumnos:
        user = alumno["github_user"]
        info = alumno["info"]

        carpeta = DIR_ENTREGAS / sanitizar(info)
        resultados = {}

        total = 0

        for repo in REPOS:
            if not repo_existe(user, repo):
                resultados[repo] = "NO EXISTE"
                continue

            res = evaluar_repo(user, repo, carpeta)
            if res:
                puntos, detalle = res
                total += puntos
                resultados[repo] = detalle

        generar_html(carpeta, info, resultados)

        resultados_csv.append({
            "alumno": info,
            "usuario": user,
            "nota": total
        })

        print(f"✔ {info} -> {total}")

        time.sleep(0.2)

    with open(CSV_SALIDA, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["alumno", "usuario", "nota"])
        writer.writeheader()
        writer.writerows(resultados_csv)

    print("\n✅ Corrección terminada")

if __name__ == "__main__":
    main()
