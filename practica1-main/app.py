from flask import Flask, flash, redirect, render_template, request,flash, session, url_for
import smtplib
from email.mime.text import MIMEText

from gestor_labiales import GestorLabiales

app = Flask(__name__)
app.secret_key = "mimecita2.0"  # La puse para proteger la sesión

gestor = GestorLabiales()

# Asegura que exista gestor.usuarios.find_one aunque Mongo falle



@app.route("/")
def index():
    if session.get("usuario_id"):
        return redirect(url_for("dashboard"))
    return render_template("registro.html")



@app.route("/registrar", methods=["GET", "POST"])
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

        if usuario["password"] == password:
            session["usuario_id"] = str(usuario["_id"])
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Contraseña incorrecta")

    return render_template("login.html")


@app.route("/cerrarsesion")
def cerrarsesion():
    session.clear()
    flash("Haz cerrado sesión", "success")
    return redirect(url_for("login"))


@app.route('/paswoord', methods=['GET', 'POST'])
def password():

    if request.method == 'POST':

        email = request.form['email']

        usuario = gestor.usuarios.find_one({"email": email})

        if usuario:

            # Link para cambiar contraseña
            link = url_for('nueva_password', email=email, _external=True)

            # Mensaje del correo
            mensaje = MIMEText(f"""
Hola.

Da clic en el siguiente enlace para cambiar tu contraseña:

{link}
""")

            mensaje['Subject'] = 'Recuperar contraseña'
            mensaje['From'] = 'tucorreo@gmail.com'
            mensaje['To'] = email

            # Enviar correo
            servidor = smtplib.SMTP('smtp.gmail.com', 587)
            servidor.starttls()

            servidor.login(
                'tucorreo@gmail.com',
                'TU_CONTRASEÑA_DE_APLICACION'
            )

            servidor.send_message(mensaje)
            servidor.quit()

            flash("Se envió un correo para recuperar tu contraseña")

        else:
            flash("Ese correo no está registrado")

    return render_template('paswoord.html')


@app.route('/nueva_password/<email>', methods=['GET', 'POST'])
def nueva_password(email):

    if request.method == 'POST':

        nueva = request.form['password']

        gestor.usuarios.update_one(
            {"email": email},
            {"$set": {"password": nueva}}
        )

        flash("Contraseña actualizada")
        return redirect(url_for('login'))

    return render_template('nueva_password.html')




if __name__ == "__main__":
    app.run(debug=True)