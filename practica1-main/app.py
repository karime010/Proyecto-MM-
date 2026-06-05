from flask import Flask, flash, redirect, render_template, request,flash, session, url_for
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import smtplib
import bcrypt
from email.message import EmailMessage

from gestor_labiales import GestorLabiales

app = Flask(__name__)
app.secret_key = "mimecita2.0" 
serializer = URLSafeTimedSerializer(app.secret_key)

def enviar_correo_recuperacion(destinatario, enlace):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Recuperar contraseña"
        msg["From"] = "karimearisbelcruzsilva2@gmail.com"
        msg["To"] = destinatario

        msg.set_content(f"Link:\n{enlace}")

        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()
            servidor.login("karimearisbelcruzsilva2@gmail.com", "cfhiwormgacgokuv")
            servidor.send_message(msg)

        print("Correo enviado")

    except Exception as e:
        print("Error enviando correo:", e)



gestor = GestorLabiales()

@app.route("/")
def index():
    if session.get("usuario_id"):
        return redirect(url_for("registro"))
    return render_template("registro.html")



@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template("registro.html", error="Las contraseñas no coinciden!")

        gestor.crear_usuario(nombre, email, password)
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        usuario = gestor.usuarios.find_one({"email": email})

        if not usuario:
            return render_template("login.html", error="Usuario no encontrado")

        if "password" not in usuario:
            return render_template("login.html", error="Usuario no tiene contraseña")

        if bcrypt.checkpw(
            password.encode("utf-8"),
            usuario["password"].encode("utf-8")
        ):
            session["usuario_id"] = str(usuario["_id"])
            return redirect(url_for("labiales"))

        return render_template("login.html", error="Contraseña incorrecta")
    return render_template("login.html")


@app.route("/cerrarsesion")
def cerrarsesion():
    session.clear()
    flash("Haz cerrado sesión", "success")
    return redirect(url_for("login"))



@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        usuario = gestor.usuarios.find_one({"email": email})

        if not usuario:
            flash("Ese correo no está registrado")
            return render_template("recuperar.html")

        token = serializer.dumps(
            email,
            salt="recuperar-password"
        )

        enlace = url_for(
            "nueva_password",
            token=token,
            _external=True
        )

        enviar_correo_recuperacion(email, enlace)

        flash("Revisa tu correo")
        return redirect("/recuperar")

    return render_template("recuperar.html")


@app.route("/nueva_password/<token>", methods=["GET", "POST"])
def nueva_password(token):
    try:
        email = serializer.loads(
            token,
            salt="recuperar-password",
            max_age=1800,
        )
    except SignatureExpired:
        flash("El enlace de recuperación expiró")
        return redirect("/recuperar")
    except BadSignature:
        flash("El enlace de recuperación no es válido")
        return redirect("/recuperar")

    usuario = gestor.usuarios.find_one({"email": email})
    if not usuario:
        flash("El correo ya no está registrado")
        return redirect("/recuperar")

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirmPassword", "")

        if password != confirm_password:
            flash("Las contraseñas no coinciden")
            return render_template("nueva_contraseña.html")

        nuevo_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        gestor.usuarios.update_one(
            {"email": email},
            {"$set": {"password": nuevo_hash}},
        )

        flash("Contraseña actualizada. Ya puedes iniciar sesión")
        return redirect("/recuperar")

    return render_template("nueva_contraseña.html")


@app.route("/labiales")
def labiales():
    labiales = list(gestor.labiales.find())
    print("LABIALES:", labiales)
    return render_template("labiales.html", labiales=labiales)

@app.route("/agregar_labiales", methods=["GET", "POST"])
def agregar_labiales():
    if request.method == "POST":
        usuario_id = session.get("usuario_id")
        nombre = request.form["nombre"]
        marca = request.form["marca"]
        precio = float(request.form["precio"])

        imagen = request.files["imagen"] 
        nombre_archivo = imagen.filename

        imagen.save(f"practica1-main/static/{nombre_archivo}")

        gestor.agregar_labial(usuario_id,nombre, marca, precio, imagen=f"static/{nombre_archivo}")

        return redirect(url_for("labiales"))
    
    return render_template("agregar_labiales.html")

@app.route("/editar_labial/<id>", methods=["GET", "POST"])
def editar_labial(id):

    if request.method == "POST":
        nombre = request.form["nombre"]
        marca = request.form["marca"]
        precio = float(request.form["precio"])

        imagen = request.files["imagen"]

        nombre_archivo = imagen.filename
        imagen.save(f"practica1-main/static/{nombre_archivo}")

        ruta = f"/static/{nombre_archivo}"

        gestor.actualizar_labial(id, nombre, marca, precio, ruta)

        return redirect(url_for("labiales"))

    return render_template("editar.html", id=id)


@app.route("/eliminar_labial/<id>")
def eliminar_labial(id):
    gestor.eliminar_labial(id)
    return redirect(url_for("labiales"))


@app.route("/contactos")
def contactos():
    return render_template("contactos.html")


@app.route("/labialesyaechos")
def labialesyaechos():
    return render_template("labialesyaechos.html")

if __name__ == "__main__":
    app.run(debug=True)