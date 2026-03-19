#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

# ==============================
# CONFIG
# ==============================
REPO = "plantilla_endes"
CSV_SALIDA = "correccion_endes.csv"
DIR_ENTREGAS = Path("entregas")

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
# UTILIDADES
# ==============================
def parse_github_date(date_str: str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def formatear_fecha(dt):
    if not dt:
        return ""
    madrid = dt.astimezone(ZoneInfo("Europe/Madrid"))
    return madrid.strftime("%Y-%m-%d %H:%M:%S Europe/Madrid")


def sanitizar_nombre(texto: str) -> str:
    texto = texto.strip().replace(" ", "_")
    texto = texto.replace(",", "")
    texto = texto.replace("/", "__")
    texto = re.sub(r"[^A-Za-z0-9._-]+", "_", texto)
    return texto.strip("_")


def gh_get(url: str, params=None):
    try:
        return SESSION.get(url, params=params, timeout=20)
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

        fecha_madrid = fecha.astimezone(ZoneInfo("Europe/Madrid"))

        if ultima_fecha is None or fecha_madrid > ultima_fecha:
            ultima_fecha = fecha_madrid

        if fecha_madrid > FECHA_CIERRE:
            ramas_fuera.append(f"{rama} ({formatear_fecha(fecha)})")

    return ramas_fuera, ultima_fecha, " | ".join(errores)


# ==============================
# GIT LOCAL
# ==============================
def run_cmd(cmd, cwd=None):
    try:
        res = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def git_url(user: str) -> str:
    return f"https://github.com/{user}/{REPO}.git"


def clonar_mirror_si_no_existe(user: str, ruta_mirror: Path):
    if ruta_mirror.exists():
        code, out, err = run_cmd(["git", "remote", "update", "--prune"], cwd=ruta_mirror)
        return code == 0, err or out

    ruta_mirror.parent.mkdir(parents=True, exist_ok=True)
    code, out, err = run_cmd(["git", "clone", "--mirror", git_url(user), str(ruta_mirror)])
    return code == 0, err or out


def exportar_rama_desde_mirror(ruta_mirror: Path, rama: str, destino: Path):
    """
    Exporta una rama a una carpeta sin necesidad de checkout persistente.
    Usa git archive para dejar el contenido limpio.
    """
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)

    archive_cmd = ["git", "archive", rama]
    tar_cmd = ["tar", "-x", "-C", str(destino)]

    try:
        p1 = subprocess.Popen(
            archive_cmd,
            cwd=ruta_mirror,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        p2 = subprocess.Popen(
            tar_cmd,
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        p1.stdout.close()
        _, err2 = p2.communicate()
        _, err1 = p1.communicate()

        if p1.returncode != 0:
            return False, err1.decode("utf-8", errors="ignore").strip()
        if p2.returncode != 0:
            return False, err2.decode("utf-8", errors="ignore").strip()

        return True, ""
    except Exception as e:
        return False, str(e)


def organizar_entrega_alumno(user: str, info: str, ramas_existentes):
    """
    Crea:
      entregas/<info>__<user>/repo.git
      entregas/<info>__<user>/<rama_exportada>
    """
    carpeta_alumno = DIR_ENTREGAS / f"{sanitizar_nombre(info)}__{sanitizar_nombre(user)}"
    ruta_mirror = carpeta_alumno / "repo.git"
    errores = []

    ok_clone, msg_clone = clonar_mirror_si_no_existe(user, ruta_mirror)
    if not ok_clone:
        return str(carpeta_alumno), f"Error clonando/actualizando: {msg_clone}"

    for rama in ramas_existentes:
        nombre_rama_dir = sanitizar_nombre(rama)
        destino = carpeta_alumno / nombre_rama_dir
        ok_exp, msg_exp = exportar_rama_desde_mirror(ruta_mirror, rama, destino)
        if not ok_exp:
            errores.append(f"{rama}: {msg_exp}")

    return str(carpeta_alumno), " | ".join(errores)


# ==============================
# EVALUACIÓN
# ==============================
def evaluar(alumno, clonar=False):
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
        "ruta_local": "",
        "error_api": "",
        "error_git": "",
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
        resultado["ultimo_commit_repo"] = ultima_fecha.strftime("%Y-%m-%d %H:%M:%S Europe/Madrid")

    errores = []
    if err_ramas:
        errores.append(err_ramas)
    if err_commits:
        errores.append(err_commits)
    resultado["error_api"] = " | ".join([e for e in errores if e])

    if clonar and ramas_existentes:
        ruta_local, err_git = organizar_entrega_alumno(user, info, ramas_existentes)
        resultado["ruta_local"] = ruta_local
        resultado["error_git"] = err_git

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
        "ruta_local",
        "error_api",
        "error_git",
    ]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)


def main():
    resultados = []
    CLONAR_ENTREGAS = True

    print(f"Token cargado: {'SI' if GITHUB_TOKEN else 'NO'}")
    print(f"Fecha de cierre: {FECHA_CIERRE.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Clonado de entregas: {'SI' if CLONAR_ENTREGAS else 'NO'}\n")

    DIR_ENTREGAS.mkdir(parents=True, exist_ok=True)

    for i, alumno in enumerate(alumnos, start=1):
        user = alumno["github_user"].strip()
        info = alumno["info"]
        print(f"[{i:02d}/{len(alumnos)}] Corrigiendo {info} ({user if user else 'SIN_USUARIO'})...")

        res = evaluar(alumno, clonar=CLONAR_ENTREGAS)
        resultados.append(res)

        time.sleep(0.25)

    guardar_csv(resultados, CSV_SALIDA)

    print("\n✅ Corrección terminada")
    print(f"📄 CSV generado: {CSV_SALIDA}")
    print(f"📁 Entregas exportadas en: {DIR_ENTREGAS.resolve()}")


if __name__ == "__main__":
    main()
