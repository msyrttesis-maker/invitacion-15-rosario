from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
import uuid
import os
import time

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")


# -----------------------------
# CONEXIÓN + REINTENTO
# -----------------------------
def get_collection():
    for intento in range(3):
        try:
            client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=3000
            )

            client.admin.command('ping')

            db = client["InvitacionRosarioDB"]
            return db["invitados"]

        except Exception as e:
            print(f"❌ Mongo intento {intento+1}:", e)
            time.sleep(1)

    return None


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def inicio():
    return redirect("/admin")


# -----------------------------
# ADMIN
# -----------------------------
@app.route("/admin")
def admin():
    col = get_collection()

    error = None

    if col is None:
        datos = []
        error = "⚠️ No se pudo conectar a la base de datos"
    else:
        try:
            datos = list(col.find({}, {
                "_id": 0,
                "nombre": 1,
                "tipo_persona": 1,
                "max_personas": 1,
                "confirmado": 1,
                "codigo": 1
            }))
        except Exception as e:
            print("Error Mongo:", e)
            datos = []
            error = "Error consultando datos"

    mayores = sum(d.get("confirmado",0) for d in datos if d.get("tipo_persona")=="mayor" and d.get("confirmado",0)>0)
    menores = sum(d.get("confirmado",0) for d in datos if d.get("tipo_persona")=="menor" and d.get("confirmado",0)>0)
    familias = sum(d.get("confirmado",0) for d in datos if d.get("tipo_persona")=="familia" and d.get("confirmado",0)>0)
    no_asisten = sum(1 for d in datos if d.get("confirmado",-1)==-1)

    return render_template(
        "admin.html",
        datos=datos,
        mayores=mayores,
        menores=menores,
        familias=familias,
        no_asisten=no_asisten,
        error=error
    )


# -----------------------------
# CREAR INVITADO
# -----------------------------
@app.route("/crear_invitado", methods=["POST"])
def crear_invitado():
    col = get_collection()

    if col is None:
        return "Error de conexión. Intentá nuevamente."

    try:
        nombre = request.form.get("nombre")
        tipo = request.form.get("tipo")
        max_personas = request.form.get("max_personas")

        if not nombre or not tipo or not max_personas:
            return "Faltan datos", 400

        codigo = str(uuid.uuid4())[:8]

        col.insert_one({
            "nombre": nombre,
            "codigo": codigo,
            "max_personas": int(max_personas),
            "tipo_persona": tipo,
            "confirmado": 0
        })

        return redirect("/admin")

    except Exception as e:
        print("Error creando invitado:", e)
        return "Error al guardar"


# -----------------------------
# INVITACIÓN
# -----------------------------
@app.route("/inv/<codigo>")
def invitacion(codigo):
    col = get_collection()

    if col is None:
        return "Error de conexión"

    try:
        invitado = col.find_one({"codigo": codigo})

        if not invitado:
            return "Invitación no válida"

        return render_template(
            "invitacion.html",
            nombre=invitado["nombre"],
            max_personas=invitado["max_personas"],
            codigo=codigo
        )

    except Exception as e:
        print("Error invitación:", e)
        return "Error cargando invitación"


# -----------------------------
# CONFIRMAR
# -----------------------------
@app.route("/confirmar", methods=["POST"])
def confirmar():
    col = get_collection()

    if col is None:
        return "Error de conexión"

    try:
        codigo = request.form.get("codigo")
        personas = request.form.get("personas")

        if not codigo or not personas:
            return "Faltan datos", 400

        col.update_one(
            {"codigo": codigo},
            {"$set": {"confirmado": int(personas)}}
        )

        return "¡Gracias por confirmar!"

    except Exception as e:
        print("Error confirmar:", e)
        return "Error"


# -----------------------------
# NO ASISTIR
# -----------------------------
@app.route("/no_asistire", methods=["POST"])
def no_asistire():
    col = get_collection()

    if col is None:
        return "Error de conexión"

    try:
        codigo = request.form.get("codigo")

        if not codigo:
            return "Faltan datos", 400

        col.update_one(
            {"codigo": codigo},
            {"$set": {"confirmado": -1}}
        )

        return "Gracias por avisar"

    except Exception as e:
        print("Error no asistir:", e)
        return "Error"


# -----------------------------
# ELIMINAR
# -----------------------------
@app.route("/eliminar/<codigo>")
def eliminar(codigo):
    col = get_collection()

    if col is None:
        return "Error de conexión"

    try:
        col.delete_one({"codigo": codigo})
        return redirect("/admin")

    except Exception as e:
        print("Error eliminar:", e)
        return "Error"


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
