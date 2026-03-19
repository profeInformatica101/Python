#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import html
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
# ARCHIVOS OBJETIVO POR RAMA
# ==============================
OBJETIVOS_POR_RAMA = {
    "prueba/comercial": {
        "nombre_contiene": "ComercialTest",
        "extensiones": {".java"},
        "modo": "codigo",
    },
    "dev/contratarEmpleado": {
        "nombre_contiene": "Plantilla",
        "extensiones": {".java"},
        "modo": "codigo",
    },
    "prueba/plantilla": {
        "nombre_contiene": "PlantillaTest",
        "extensiones": {".java"},
        "modo": "codigo",
    },
    "doc/javadoc": {
        "nombre_contiene": None,
        "extensiones": {".html", ".htm"},
        "modo": "solo_html_generado",
    },
}

# ==============================
# UTILIDADES
# ==============================
def parse_github_date(date_str: str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def formatear_fecha(dt):
    if not dt:
        return ""
    return dt.astimezone(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S Europe/Madrid")


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


def escribir_archivo(path: Path, contenido: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contenido, encoding="utf-8")


def leer_texto_seguro(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[ERROR LEYENDO ARCHIVO: {e}]"


def buscar_archivos(base: Path, nombre_contiene: str, extensiones=None):
    encontrados = []
    if not base.exists():
        return encontrados

    for p in base.rglob("*"):
        if not p.is_file():
            continue
        if extensiones and p.suffix.lower() not in extensiones:
            continue
        if nombre_contiene.lower() in p.name.lower():
            encontrados.append(p)

    return sorted(encontrados)


def buscar_primero(base: Path, nombre_contiene: str, extensiones=None):
    resultados = buscar_archivos(base, nombre_contiene, extensiones)
    return resultados[0] if resultados else None


# ==============================
# API GITHUB
# ==============================
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
        return [b["name"] for b in r.json()], ""
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
        return parse_github_date(data[0]["commit"]["committer"]["date"]), ""
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
        res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
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
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)

    archive_cmd = ["git", "archive", rama]
    tar_cmd = ["tar", "-x", "-C", str(destino)]

    try:
        p1 = subprocess.Popen(archive_cmd, cwd=ruta_mirror, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2 = subprocess.Popen(tar_cmd, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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


# ==============================
# CÓDIGO RELEVANTE HTML
# ==============================
def recoger_archivos_relevantes(carpeta_alumno: Path, ramas_existentes):
    encontrados = []

    for rama in ramas_existentes:
        if rama not in OBJETIVOS_POR_RAMA:
            continue

        config = OBJETIVOS_POR_RAMA[rama]
        base = carpeta_alumno / sanitizar_nombre(rama)

        if not base.exists():
            continue

        if config["modo"] == "solo_html_generado":
            htmls = []
            for p in sorted(base.rglob("*")):
                if p.is_file() and p.suffix.lower() in config["extensiones"]:
                    htmls.append(p)

            encontrados.append({
                "rama": rama,
                "tipo": "doc_html",
                "ruta_relativa": "(documentación generada)",
                "contenido": f"Documentación HTML generada: {'SÍ' if htmls else 'NO'}\nTotal de archivos HTML detectados: {len(htmls)}",
            })
            continue

        for p in sorted(base.rglob("*")):
            if not p.is_file():
                continue
            if p.suffix.lower() not in config["extensiones"]:
                continue
            if config["nombre_contiene"].lower() in p.name.lower():
                encontrados.append({
                    "rama": rama,
                    "tipo": "codigo",
                    "ruta_relativa": str(p.relative_to(base)),
                    "contenido": leer_texto_seguro(p),
                })
                break

    return encontrados


def render_codigo_relevante_html(carpeta_alumno: Path, resultado: dict, archivos: list[dict]):
    bloques = []

    for item in archivos:
        rama = item["rama"]
        ruta_relativa = item["ruta_relativa"]
        contenido = item["contenido"]
        tipo = item.get("tipo", "codigo")

        if tipo == "doc_html":
            bloques.append(f"""
            <section class="card">
              <h2>{html.escape(rama)}</h2>
              <div class="meta">Comprobación de documentación generada</div>
              <pre><code>{html.escape(contenido)}</code></pre>
            </section>
            """)
        else:
            bloques.append(f"""
            <section class="card">
              <h2>{html.escape(rama)}</h2>
              <div class="meta">{html.escape(ruta_relativa)}</div>
              <pre><code>{html.escape(contenido)}</code></pre>
            </section>
            """)

    if not bloques:
        bloques.append("""
        <section class="card">
          <h2>Sin archivos relevantes</h2>
          <p>No se han encontrado los archivos objetivo configurados para la corrección.</p>
        </section>
        """)

    badge_class = "badge badge-danger" if resultado["fuera_de_plazo"] == "SI" else "badge"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Código relevante - {html.escape(carpeta_alumno.name)}</title>
<style>
:root {{
  --bg:#f5f7fb; --card:#fff; --border:#d8e0ea; --text:#1f2937; --muted:#6b7280;
  --code-bg:#0f172a; --code-text:#e5e7eb; --accent:#0d6efd; --danger-bg:#fff1f2; --danger-border:#fecdd3;
}}
body {{ margin:0; font-family:Arial,Helvetica,sans-serif; background:var(--bg); color:var(--text); }}
.container {{ max-width:1400px; margin:0 auto; padding:24px; }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:18px; margin-bottom:20px; }}
h1 {{ margin:0 0 12px; }}
h2 {{ margin:0 0 8px; color:var(--accent); }}
.meta {{ color:var(--muted); margin-bottom:10px; }}
.badge {{ display:inline-block; padding:6px 10px; border-radius:999px; background:#eef2ff; color:#1e3a8a; margin-right:8px; }}
.badge-danger {{ background:var(--danger-bg); border:1px solid var(--danger-border); color:#9f1239; }}
pre {{ margin:0; white-space:pre-wrap; word-break:break-word; overflow-x:auto; }}
code {{ display:block; background:var(--code-bg); color:var(--code-text); border-radius:10px; padding:14px; font-family:Consolas,monospace; font-size:.9rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>Código relevante - {html.escape(carpeta_alumno.name)}</h1>
  <p>
    <span class="badge">Alumno: {html.escape(resultado["info"])}</span>
    <span class="badge">Usuario: {html.escape(resultado["usuario"])}</span>
    <span class="badge">Ramas: {html.escape(resultado["ramas_ok"])}</span>
    <span class="{badge_class}">Fuera de plazo: {html.escape(resultado["fuera_de_plazo"])}</span>
  </p>
  {''.join(bloques)}
</div>
</body>
</html>
"""


# ==============================
# RÚBRICA AUTOMÁTICA
# ==============================
def evaluar_ejercicio_1(ramas_existentes):
    ok = "codigo_sin_pruebas" in ramas_existentes
    return (1.0 if ok else 0.0), "Rama codigo_sin_pruebas encontrada" if ok else "No existe codigo_sin_pruebas"


def evaluar_ejercicio_2(carpeta_alumno: Path, ramas_existentes):
    rama = "prueba/comercial"
    if rama not in ramas_existentes:
        return 0.0, "No existe rama prueba/comercial"

    base = carpeta_alumno / sanitizar_nombre(rama)
    test = buscar_primero(base, "ComercialTest", {".java"})
    if not test:
        return 0.5, "Existe la rama, pero no se detecta ComercialTest.java"

    contenido = leer_texto_seguro(test)
    patrones = ["getVentas", "setVentas", "calcularExtra", "getSueldo"]
    encontrados = sum(1 for p in patrones if p in contenido)

    if encontrados >= 4:
        return 2.0, "ComercialTest detectado con referencias a los 4 métodos"
    if encontrados >= 2:
        return 1.5, "ComercialTest detectado, pero incompleto"
    return 1.0, "ComercialTest existe, pero con poca evidencia de cobertura"


def evaluar_ejercicio_3(carpeta_alumno: Path, ramas_existentes):
    rama = "dev/contratarEmpleado"
    if rama not in ramas_existentes:
        return 0.0, "No existe rama dev/contratarEmpleado"

    base = carpeta_alumno / sanitizar_nombre(rama)
    plantilla = buscar_primero(base, "Plantilla", {".java"})
    if not plantilla:
        return 0.5, "Existe la rama, pero no se detecta Plantilla.java"

    texto = leer_texto_seguro(plantilla)
    patrones = ["contratarEmpleado", "IllegalArgumentException", "dni"]
    encontrados = sum(1 for p in patrones if p.lower() in texto.lower())

    if encontrados >= 3:
        return 1.0, "Plantilla.java muestra indicios claros de control de duplicados por DNI"
    return 0.5, "Plantilla.java existe, pero la evidencia automática es parcial"


def evaluar_ejercicio_4(carpeta_alumno: Path, ramas_existentes):
    rama = "prueba/plantilla"
    if rama not in ramas_existentes:
        return 0.0, "No existe rama prueba/plantilla"

    base = carpeta_alumno / sanitizar_nombre(rama)
    test = buscar_primero(base, "PlantillaTest", {".java"})
    if not test:
        return 0.5, "Existe la rama, pero no se detecta PlantillaTest.java"

    contenido = leer_texto_seguro(test)
    patrones = ["contratarEmpleado", "getEmpleadosPorNombre"]
    encontrados = sum(1 for p in patrones if p in contenido)

    if encontrados >= 2:
        return 2.0, "PlantillaTest detectado con referencias a ambos métodos"
    return 1.0, "PlantillaTest existe, pero con evidencia parcial"


def evaluar_ejercicio_5(carpeta_alumno: Path, ramas_existentes):
    rama = "doc/javadoc"
    if rama not in ramas_existentes:
        return 0.0, "No existe rama doc/javadoc"

    base = carpeta_alumno / sanitizar_nombre(rama)
    htmls = [p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in {".html", ".htm"}]

    if htmls:
        return 1.0, "Se detecta documentación HTML generada"
    return 0.5, "Existe la rama doc/javadoc, pero no se detecta documentación HTML"


def evaluar_ejercicio_6(carpeta_alumno: Path, ramas_existentes):
    if "main" not in ramas_existentes:
        return 0.0, "No existe rama main"

    base_main = carpeta_alumno / sanitizar_nombre("main")
    hallazgos = 0

    if buscar_primero(base_main, "ComercialTest", {".java"}):
        hallazgos += 1
    if buscar_primero(base_main, "Plantilla", {".java"}):
        hallazgos += 1

    doc_main = [p for p in base_main.rglob("*") if p.is_file() and p.suffix.lower() in {".html", ".htm"}]
    if doc_main:
        hallazgos += 1

    if hallazgos >= 2:
        return 1.0, "main contiene indicios de los cambios fusionados"
    return 0.5, "Existe main, pero la evidencia automática de merge es parcial"


def evaluar_rubrica(carpeta_alumno: Path, ramas_existentes):
    e1, d1 = evaluar_ejercicio_1(ramas_existentes)
    e2, d2 = evaluar_ejercicio_2(carpeta_alumno, ramas_existentes)
    e3, d3 = evaluar_ejercicio_3(carpeta_alumno, ramas_existentes)
    e4, d4 = evaluar_ejercicio_4(carpeta_alumno, ramas_existentes)
    e5, d5 = evaluar_ejercicio_5(carpeta_alumno, ramas_existentes)
    e6, d6 = evaluar_ejercicio_6(carpeta_alumno, ramas_existentes)

    total = round(e1 + e2 + e3 + e4 + e5 + e6, 2)

    return {
        "e1": e1, "e1_detalle": d1,
        "e2": e2, "e2_detalle": d2,
        "e3": e3, "e3_detalle": d3,
        "e4": e4, "e4_detalle": d4,
        "e5": e5, "e5_detalle": d5,
        "e6": e6, "e6_detalle": d6,
        "nota_total_8": total,
    }


# ==============================
# ORGANIZACIÓN LOCAL
# ==============================
def generar_resumen_alumno(carpeta_alumno: Path, resultado: dict, ramas_existentes):
    contenido = [
        f"Alumno: {resultado['info']}",
        f"Usuario GitHub: {resultado['usuario']}",
        f"Repositorio: {resultado['repo']}",
        f"Ramas encontradas: {resultado['ramas_ok']}",
        f"Fuera de plazo: {resultado['fuera_de_plazo']}",
        f"Detalle fuera de plazo: {resultado['detalle_fuera_de_plazo']}",
        f"Último commit detectado: {resultado['ultimo_commit_repo']}",
        f"Ruta local: {resultado['ruta_local']}",
        f"Error API: {resultado['error_api']}",
        f"Error GIT: {resultado['error_git']}",
        "",
        "Puntuación automática:",
        f"Ejercicio 1: {resultado['e1']} -> {resultado['e1_detalle']}",
        f"Ejercicio 2: {resultado['e2']} -> {resultado['e2_detalle']}",
        f"Ejercicio 3: {resultado['e3']} -> {resultado['e3_detalle']}",
        f"Ejercicio 4: {resultado['e4']} -> {resultado['e4_detalle']}",
        f"Ejercicio 5: {resultado['e5']} -> {resultado['e5_detalle']}",
        f"Ejercicio 6: {resultado['e6']} -> {resultado['e6_detalle']}",
        f"TOTAL / 8: {resultado['nota_total_8']}",
        "",
        "Ramas exportadas:",
    ]
    contenido.extend(f"- {r}" for r in ramas_existentes)
    contenido.extend([
        "",
        "Archivos objetivo mostrados en _codigo_relevante.html:",
        "- prueba/comercial -> ComercialTest",
        "- dev/contratarEmpleado -> Plantilla",
        "- prueba/plantilla -> PlantillaTest",
        "- doc/javadoc -> solo comprobación de HTML generado",
    ])
    escribir_archivo(carpeta_alumno / "_resumen.txt", "\n".join(contenido))


def generar_codigo_relevante_html(carpeta_alumno: Path, ramas_existentes, resultado: dict):
    archivos = recoger_archivos_relevantes(carpeta_alumno, ramas_existentes)
    html_final = render_codigo_relevante_html(carpeta_alumno, resultado, archivos)
    escribir_archivo(carpeta_alumno / "_codigo_relevante.html", html_final)


def organizar_entrega_alumno(user: str, info: str, ramas_existentes):
    carpeta_alumno = DIR_ENTREGAS / f"{sanitizar_nombre(info)}__{sanitizar_nombre(user)}"
    ruta_mirror = carpeta_alumno / "repo.git"
    errores = []

    ok_clone, msg_clone = clonar_mirror_si_no_existe(user, ruta_mirror)
    if not ok_clone:
        return carpeta_alumno, f"Error clonando/actualizando: {msg_clone}"

    for rama in ramas_existentes:
        destino = carpeta_alumno / sanitizar_nombre(rama)
        ok_exp, msg_exp = exportar_rama_desde_mirror(ruta_mirror, rama, destino)
        if not ok_exp:
            errores.append(f"{rama}: {msg_exp}")

    return carpeta_alumno, " | ".join(errores)


# ==============================
# EVALUACIÓN GLOBAL
# ==============================
def evaluar(alumno, clonar=False):
    user = alumno["github_user"].strip()
    info = alumno["info"]

    resultado = {
        "info": info,
        "usuario": user if user else "SIN_USUARIO",
        "repo": "NO",
        "ramas_ok": "0/6",
        "fuera_de_plazo": "NO",
        "detalle_fuera_de_plazo": "",
        "ultimo_commit_repo": "",
        "ruta_local": "",
        "error_api": "",
        "error_git": "",
        "e1": 0.0, "e1_detalle": "",
        "e2": 0.0, "e2_detalle": "",
        "e3": 0.0, "e3_detalle": "",
        "e4": 0.0, "e4_detalle": "",
        "e5": 0.0, "e5_detalle": "",
        "e6": 0.0, "e6_detalle": "",
        "nota_total_8": 0.0,
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

    ramas_existentes = [r for r in RAMAS_REQUERIDAS if r in ramas]
    resultado["ramas_ok"] = f"{len(ramas_existentes)}/{len(RAMAS_REQUERIDAS)}"

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
    resultado["error_api"] = " | ".join(e for e in errores if e)

    if clonar and ramas_existentes:
        carpeta_alumno, err_git = organizar_entrega_alumno(user, info, ramas_existentes)
        resultado["ruta_local"] = str(carpeta_alumno)
        resultado["error_git"] = err_git

        rubrica = evaluar_rubrica(carpeta_alumno, ramas_existentes)
        resultado.update(rubrica)

        generar_resumen_alumno(carpeta_alumno, resultado, ramas_existentes)
        generar_codigo_relevante_html(carpeta_alumno, ramas_existentes, resultado)

    return resultado


def guardar_csv(resultados, ruta):
    campos = [
        "info", "usuario", "repo", "ramas_ok",
        "fuera_de_plazo", "detalle_fuera_de_plazo", "ultimo_commit_repo",
        "e1", "e1_detalle",
        "e2", "e2_detalle",
        "e3", "e3_detalle",
        "e4", "e4_detalle",
        "e5", "e5_detalle",
        "e6", "e6_detalle",
        "nota_total_8",
        "ruta_local", "error_api", "error_git",
    ]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)


def main():
    resultados = []
    CLONAR_ENTREGAS = True

    if not GITHUB_TOKEN:
        print("⚠️ Aviso: GITHUB_TOKEN no está cargado. Puedes sufrir rate limit.")

    print(f"Token cargado: {'SI' if GITHUB_TOKEN else 'NO'}")
    print(f"Fecha de cierre: {FECHA_CIERRE.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Clonado de entregas: {'SI' if CLONAR_ENTREGAS else 'NO'}")
    print()

    DIR_ENTREGAS.mkdir(parents=True, exist_ok=True)

    for i, alumno in enumerate(alumnos, start=1):
        user = alumno["github_user"].strip()
        info = alumno["info"]
        print(f"[{i:02d}/{len(alumnos)}] Corrigiendo {info} ({user if user else 'SIN_USUARIO'})...")
        resultados.append(evaluar(alumno, clonar=CLONAR_ENTREGAS))
        time.sleep(0.25)

    guardar_csv(resultados, CSV_SALIDA)

    print("\n✅ Corrección terminada")
    print(f"📄 CSV generado: {CSV_SALIDA}")
    print(f"📁 Entregas exportadas en: {DIR_ENTREGAS.resolve()}")


if __name__ == "__main__":
    main()
