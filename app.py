"""Servidor Flask de Cumbre Digital MX 2026: registro de asistentes con SQLite."""

import os
import re
import sqlite3

from flask import Flask, g, redirect, render_template, request, url_for

app = Flask(__name__)

# La base de datos vive en la raíz del proyecto (junto a app.py)
RUTA_BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evento.db")

AREAS = ["Tecnología", "Marketing", "Negocios", "Emprendimiento"]

# Longitudes máximas para evitar datos absurdamente largos
MAX_NOMBRE = 120
MAX_EMAIL = 254
MAX_EMPRESA = 120

PATRON_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")


# ==========================================================
# BASE DE DATOS
# ==========================================================

def obtener_bd():
    """Devuelve la conexión a SQLite de la petición actual (se crea una vez por petición)."""
    if "bd" not in g:
        g.bd = sqlite3.connect(RUTA_BD)
        g.bd.row_factory = sqlite3.Row
    return g.bd


@app.teardown_appcontext
def cerrar_bd(_error):
    bd = g.pop("bd", None)
    if bd is not None:
        bd.close()


def iniciar_bd():
    """Crea la tabla de asistentes si todavía no existe."""
    areas_sql = ", ".join(f"'{a}'" for a in AREAS)
    with sqlite3.connect(RUTA_BD) as bd:
        bd.execute(
            f"""
            CREATE TABLE IF NOT EXISTS asistentes (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre         TEXT NOT NULL,
                email          TEXT NOT NULL UNIQUE,
                empresa        TEXT NOT NULL,
                area_interes   TEXT NOT NULL CHECK (area_interes IN ({areas_sql})),
                fecha_registro TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


# Se ejecuta al importar el módulo, así funciona también con gunicorn en Render
iniciar_bd()


# ==========================================================
# UTILIDADES
# ==========================================================

@app.template_filter("numero_registro")
def numero_registro(id_asistente):
    """Convierte el id en el número de registro visible: 7 -> REG-0007."""
    return f"REG-{id_asistente:04d}"


def validar_formulario(datos):
    """Valida los datos del formulario. Devuelve un diccionario {campo: mensaje de error}."""
    errores = {}

    if not datos["nombre"]:
        errores["nombre"] = "Por favor ingresa tu nombre completo."
    elif len(datos["nombre"]) > MAX_NOMBRE:
        errores["nombre"] = f"El nombre no puede superar los {MAX_NOMBRE} caracteres."

    if not PATRON_EMAIL.match(datos["email"]):
        errores["email"] = "Ingresa un correo electrónico válido (ej. nombre@dominio.com)."
    elif len(datos["email"]) > MAX_EMAIL:
        errores["email"] = f"El correo no puede superar los {MAX_EMAIL} caracteres."

    if not datos["empresa"]:
        errores["empresa"] = "Por favor ingresa el nombre de tu empresa u organización."
    elif len(datos["empresa"]) > MAX_EMPRESA:
        errores["empresa"] = f"La empresa no puede superar los {MAX_EMPRESA} caracteres."

    if datos["area"] not in AREAS:
        errores["area"] = "Selecciona un área de interés."

    return errores


def mostrar_formulario(datos, errores, codigo=200):
    return render_template("index.html", areas=AREAS, datos=datos, errores=errores), codigo


# ==========================================================
# RUTAS
# ==========================================================

@app.get("/")
def inicio():
    datos = {"nombre": "", "email": "", "empresa": "", "area": ""}
    return mostrar_formulario(datos, {})


@app.post("/registro")
def registro():
    datos = {
        "nombre": request.form.get("nombre", "").strip(),
        # El correo se guarda en minúsculas para detectar duplicados sin importar mayúsculas
        "email": request.form.get("email", "").strip().lower(),
        "empresa": request.form.get("empresa", "").strip(),
        "area": request.form.get("area", "").strip(),
    }

    errores = validar_formulario(datos)
    if errores:
        return mostrar_formulario(datos, errores, 400)

    bd = obtener_bd()
    try:
        cursor = bd.execute(
            "INSERT INTO asistentes (nombre, email, empresa, area_interes) VALUES (?, ?, ?, ?)",
            (datos["nombre"], datos["email"], datos["empresa"], datos["area"]),
        )
        bd.commit()
    except sqlite3.IntegrityError:
        # La restricción UNIQUE de email también cubre registros simultáneos
        errores["email"] = "Este correo ya está registrado."
        return mostrar_formulario(datos, errores, 409)

    # Patrón POST-Redirect-GET: al recargar la confirmación no se duplica el registro
    return redirect(url_for("confirmacion", id_asistente=cursor.lastrowid))


@app.get("/confirmacion/<int:id_asistente>")
def confirmacion(id_asistente):
    asistente = obtener_bd().execute(
        "SELECT id, nombre FROM asistentes WHERE id = ?", (id_asistente,)
    ).fetchone()
    if asistente is None:
        return pagina_error(404), 404
    return render_template("confirmacion.html", asistente=asistente)


@app.get("/favicon.ico")
def favicon():
    # Aún no hay ícono: se responde vacío para no llenar la consola con errores 404
    return "", 204


@app.get("/admin")
def admin():
    bd = obtener_bd()
    asistentes = bd.execute(
        "SELECT id, nombre, email, empresa, area_interes, fecha_registro "
        "FROM asistentes ORDER BY id DESC"
    ).fetchall()

    # Conteo por área (incluye las áreas sin asistentes, con 0)
    conteo = {area: 0 for area in AREAS}
    for fila in bd.execute("SELECT area_interes, COUNT(*) AS total FROM asistentes GROUP BY area_interes"):
        conteo[fila["area_interes"]] = fila["total"]

    return render_template("admin.html", asistentes=asistentes, conteo=conteo)


# ==========================================================
# MANEJO DE ERRORES (en español, con el mismo diseño)
# ==========================================================

MENSAJES_ERROR = {
    404: ("Página no encontrada", "La página que buscas no existe o el registro fue eliminado."),
    405: ("Método no permitido", "Esta dirección no admite esa acción. Vuelve al formulario de registro."),
    500: ("Algo salió mal", "Ocurrió un error inesperado en el servidor. Inténtalo de nuevo en unos minutos."),
}


def pagina_error(codigo):
    titulo, mensaje = MENSAJES_ERROR[codigo]
    return render_template("error.html", codigo=codigo, titulo=titulo, mensaje=mensaje)


@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def manejar_error(error):
    return pagina_error(error.code), error.code


if __name__ == "__main__":
    # Desarrollo local; en Render se usa gunicorn (ver Procfile)
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
