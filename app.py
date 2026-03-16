from flask import Flask, render_template, request
import sqlite3
import uuid

app = Flask(__name__)

def db():
    return sqlite3.connect("database.db")

# CREAR TABLA DE INVITADOS
def crear_tablas():
    con = db()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invitados(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        codigo TEXT UNIQUE,
        max_personas INTEGER,
        confirmado INTEGER DEFAULT 0,
        tipo_persona TEXT
    )
    """)
    con.commit()
    con.close()

crear_tablas()

# PAGINA INICIAL
@app.route("/")
def inicio():
    return "Sistema de invitaciones funcionando"

# CREAR INVITADO
@app.route("/crear_invitado", methods=["POST"])
def crear_invitado():

    nombre = request.form["nombre"]
    tipo = request.form["tipo"]
    max_personas = request.form["max_personas"]

    codigo = str(uuid.uuid4())[:8]

    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO invitados(nombre,codigo,max_personas,tipo_persona) VALUES(?,?,?,?)",
        (nombre, codigo, max_personas, tipo)
    )

    con.commit()
    con.close()

    return "<script>window.location='/admin'</script>"
# ABRIR INVITACION
@app.route("/inv/<codigo>")
def invitacion(codigo):
    con = db()
    cur = con.cursor()
    cur.execute(
        "SELECT nombre,max_personas FROM invitados WHERE codigo=?",
        (codigo,)
    )
    invitado = cur.fetchone()
    con.close()

    if invitado:
        nombre = invitado[0]
        max_personas = invitado[1]
        return render_template(
            "invitacion.html",
            nombre=nombre,
            max_personas=max_personas,
            codigo=codigo
        )
    else:
        return "Invitación no válida"

# CONFIRMAR ASISTENCIA
@app.route("/confirmar", methods=["POST"])
def confirmar():
    codigo = request.form["codigo"]
    personas = request.form["personas"]

    con = db()
    cur = con.cursor()
    cur.execute(
        "UPDATE invitados SET confirmado=? WHERE codigo=?",
        (personas, codigo)
    )
    con.commit()
    con.close()
    return "¡Gracias por confirmar!"

# NO ASISTIRÉ
@app.route("/no_asistire", methods=["POST"])
def no_asistire():
    codigo = request.form["codigo"]
    con = db()
    cur = con.cursor()
    cur.execute(
        "UPDATE invitados SET confirmado=? WHERE codigo=?",
        (-1, codigo)
    )
    con.commit()
    con.close()
    return "Lamentamos que no puedas asistir, gracias por avisar."

# ELIMINAR INVITADO
@app.route("/eliminar/<int:id>")
def eliminar(id):
    con = db()
    cur = con.cursor()
    cur.execute("DELETE FROM invitados WHERE id=?", (id,))
    con.commit()
    con.close()
    return "<script>window.location='/admin'</script>"

# PANEL SIMPLE
@app.route("/panel")
def panel():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT nombre, confirmado FROM invitados")
    datos = cur.fetchall()
    con.close()
    return render_template("panel.html", datos=datos)

# ADMIN
@app.route("/admin")
def admin():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT id,nombre,tipo_persona,max_personas,confirmado,codigo FROM invitados")
    datos = cur.fetchall()

    mayores = 0
    menores = 0
    familias = 0
    no_asisten = 0

    for d in datos:
        tipo = d[2]
        confirmados = d[4] if d[4] else 0

        if confirmados == -1:
            no_asisten += 1
        elif tipo == "mayor":
            mayores += confirmados
        elif tipo == "menor":
            menores += confirmados
        elif tipo == "familia":
            familias += confirmados

    con.close()

    return render_template(
        "admin.html",
        datos=datos,
        mayores=mayores,
        menores=menores,
        familias=familias,
        no_asisten=no_asisten
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
