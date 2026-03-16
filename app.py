from flask import Flask, render_template, request
from pymongo import MongoClient
import uuid
import os

app = Flask(__name__)

# -----------------------------
# CONEXIÓN A MONGODB ATLAS
# -----------------------------
MONGO_URI = os.getenv(
    "MONGO_URI"
)
client = MongoClient(MONGO_URI)
db = client["InvitacionRosarioDB"]
invitados_col = db["invitados"]

# -----------------------------
# PAGINA INICIAL
# -----------------------------
@app.route("/")
def inicio():
    return "Sistema de invitaciones funcionando"

# -----------------------------
# CREAR INVITADO
# -----------------------------
@app.route("/crear_invitado", methods=["POST"])
def crear_invitado():
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
        "confirmado": 0   # por defecto
    })

    return "<script>window.location='/admin'</script>"

# -----------------------------
# ABRIR INVITACIÓN
# -----------------------------
@app.route("/inv/<codigo>")
def invitacion(codigo):
    invitado = invitados_col.find_one({"codigo": codigo})
    if invitado:
        return render_template(
            "invitacion.html",
            nombre=invitado["nombre"],
            max_personas=invitado["max_personas"],
            codigo=codigo
        )
    else:
        return "Invitación no válida"

# -----------------------------
# CONFIRMAR ASISTENCIA
# -----------------------------
@app.route("/confirmar", methods=["POST"])
def confirmar():
    codigo = request.form.get("codigo")
    personas = request.form.get("personas")

    if not codigo or not personas:
        return "Faltan datos", 400

    invitados_col.update_one(
        {"codigo": codigo},
        {"$set": {"confirmado": int(personas)}}
    )
    return "¡Gracias por confirmar!"

# -----------------------------
# NO ASISTIRÉ
# -----------------------------
@app.route("/no_asistire", methods=["POST"])
def no_asistire():
    codigo = request.form.get("codigo")

    if not codigo:
        return "Faltan datos", 400

    invitados_col.update_one(
        {"codigo": codigo},
        {"$set": {"confirmado": -1}}
    )
    return "Lamentamos que no puedas asistir, gracias por avisar."

# -----------------------------
# ELIMINAR INVITADO
# -----------------------------
@app.route("/eliminar/<codigo>")
def eliminar(codigo):
    resultado = invitados_col.delete_one({"codigo": codigo})
    if resultado.deleted_count == 0:
        return "Invitado no encontrado", 404
    return "<script>window.location='/admin'</script>"

# -----------------------------
# PANEL SIMPLE
# -----------------------------
@app.route("/panel")
def panel():
    datos = list(invitados_col.find({}, {"_id":0, "nombre":1, "confirmado":1, "tipo_persona":1}))
    return render_template("panel.html", datos=datos)

# -----------------------------
# ADMIN
# -----------------------------
@app.route("/admin")
def admin():
    datos = list(invitados_col.find({}, {"_id":0, "nombre":1, "tipo_persona":1, "max_personas":1, "confirmado":1, "codigo":1}))

    # Contadores por tipo
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
        no_asisten=no_asisten
    )

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)