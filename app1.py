from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
import uuid
import os
import time

app = Flask(__name__)

# -----------------------------
# CONFIG
# -----------------------------
MONGO_URI = os.getenv("MONGO_URI")

client = None
db = None
invitados_col = None

# -----------------------------
# CONEXIÓN SEGURA A MONGO
# -----------------------------
def conectar_mongo():
    global client, db, invitados_col

    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )

        client.server_info()  # fuerza conexión

        db = client["InvitacionRosarioDB"]

        # 👇 IMPORTANTE: colección de prueba
        invitados_col = db["invitados"]

        print("✅ Conectado a Mongo")
        return True

    except Exception as e:
        print("❌ Error conectando Mongo:", e)
        return False


# conectar al iniciar
conectar_mongo()

# -----------------------------
# FUNCIÓN SEGURA (REINTENTOS)
# -----------------------------
def obtener_datos():
    global invitados_col

    for intento in range(3):
        try:
            return list(invitados_col.find({}, {"_id":0}))
        except Exception as e:
            print(f"⚠️ Error intento {intento+1}:", e)

            # intentar reconectar
            if conectar_mongo():
                continue

            time.sleep(1)

    return None


# -----------------------------
# INICIO
# -----------------------------
@app.route("/")
def inicio():
    return redirect("/admin")


# -----------------------------
# ADMIN
# -----------------------------
@app.route("/admin")
def admin():
    datos = obtener_datos()

    error = None

    if datos is None:
        datos = []
        error = "⚠️ Problema de conexión con la base de datos"

    try:
        mayores = sum(d.get("confirmado",0) for d in datos if d.get("tipo_persona")=="mayor" and d.get("confirmado",0)>0)
        menores = sum(d.get("confirmado",0) for d in datos if d.get("tipo_persona")=="menor" and d.get("confirmado",0)>0)
        familias = sum(d.get("confirmado",0) for d in datos if d.get("tipo_persona")=="familia" and d.get("confirmado",0)>0)
        no_asisten = sum(1 for d in datos if d.get("confirmado",-1)==-1)

    except Exception as e:
        print("Error procesando datos:", e)
        mayores = menores = familias = no_asisten = 0
        error = "Error procesando datos"

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
    try:
        nombre = request.form.get("nombre")
        tipo = request.form.get("tipo")
        max_personas = request.form.get("max_personas")

        if not nombre or not tipo or not max_personas:
            return "Faltan datos", 400

        codigo = str(uuid.uuid4())[:8]

        invitados_col.insert_one({
            "nombre": nombre,
            "codigo": codigo,
            "max_personas": int(max_personas),
            "tipo_persona": tipo,
            "confirmado": 0
        })

        return redirect("/admin")

    except Exception as e:
        return f"❌ Error creando invitado: {e}"


# -----------------------------
# INVITACIÓN
# -----------------------------
@app.route("/inv/<codigo>")
def invitacion(codigo):
    try:
        invitado = invitados_col.find_one({"codigo": codigo})

        if not invitado:
            return "Invitación no válida"

        return render_template(
            "invitacion.html",
            nombre=invitado["nombre"],
            max_personas=invitado["max_personas"],
            codigo=codigo
        )

    except Exception as e:
        return f"❌ Error cargando invitación: {e}"


# -----------------------------
# CONFIRMAR
# -----------------------------
@app.route("/confirmar", methods=["POST"])
def confirmar():
    try:
        codigo = request.form.get("codigo")
        personas = request.form.get("personas")

        if not codigo or not personas:
            return "Faltan datos", 400

        invitados_col.update_one(
            {"codigo": codigo},
            {"$set": {"confirmado": int(personas)}}
        )

        return "¡Gracias por confirmar!"

    except Exception as e:
        return f"❌ Error confirmando: {e}"


# -----------------------------
# NO ASISTIR
# -----------------------------
@app.route("/no_asistire", methods=["POST"])
def no_asistire():
    try:
        codigo = request.form.get("codigo")

        if not codigo:
            return "Faltan datos", 400

        invitados_col.update_one(
            {"codigo": codigo},
            {"$set": {"confirmado": -1}}
        )

        return "Gracias por avisar"

    except Exception as e:
        return f"❌ Error: {e}"


# -----------------------------
# ELIMINAR
# -----------------------------
@app.route("/eliminar/<codigo>")
def eliminar(codigo):
    try:
        invitados_col.delete_one({"codigo": codigo})
        return redirect("/admin")

    except Exception as e:
        return f"❌ Error eliminando: {e}"


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
