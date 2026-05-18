from flask import Flask, render_template, redirect, url_for, flash, request
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_super_segura'

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tu_correo@gmail.com'
app.config['MAIL_PASSWORD'] = 'tu_contraseña_de_aplicacion' # No es tu contraseña real, es una de aplicación de Google
app.config['MAIL_DEFAULT_SENDER'] = 'tu_correo@gmail.com'

mail = Mail(app)

# Serializador para crear tokens seguros temporales
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Base de datos simulada (En producción usarías SQLAlchemy, etc.)
USUARIOS = {
    "usuario@example.com": generate_password_hash("password123")
}

def generar_token_recuperacion(email):
    # El token expira y está firmado con la SECRET_KEY
    return s.dumps(email, salt='recuperar-password-salt')

def verificar_token_recuperacion(token, expiration=1800): # 1800 segundos = 30 minutos
    try:
        email = s.loads(token, salt='recuperar-password-salt', max_age=expiration)
        return email
    except:
        return None

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Verificar si el usuario existe
        if email in USUARIOS:
            token = generar_token_recuperacion(email)
            # Creamos la URL absoluta que se enviará al correo
            enlace_recuperacion = url_for('reset_token', token=token, _external=True)
            
            # Enviar el correo
            msg = Message('Restablecer Contraseña', recipients=[email])
            msg.body = f'''Para restablecer tu contraseña, visita el siguiente enlace:
{enlace_recuperacion}

Si tú no solicitaste este cambio, ignora este correo.
'''
            mail.send(msg)
            flash('Se ha enviado un correo con instrucciones para restablecer tu contraseña.', 'info')
            return redirect(url_for('reset_request'))
        else:
            flash('Ese correo electrónico no está registrado.', 'warning')
            
    return '''
        <form method="POST">
            <h2>Recuperar Contraseña</h2>
            <input type="email" name="email" placeholder="Tu correo electrónico" required>
            <button type="submit">Enviar enlace de recuperación</button>
        </form>
    '''
    
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    # Verificar si el token es válido y no ha expirado
    email = verificar_token_recuperacion(token)
    
    if email is None:
        flash('El enlace de recuperación es inválido o ha expirado.', 'warning')
        return redirect(url_for('reset_request'))
    
    if request.method == 'POST':
        nueva_password = request.form.get('password')
        confirmar_password = request.form.get('confirm_password')
        
        if nueva_password != confirmar_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(request.url)
        
        # Actualizar la contraseña en la base de datos (aquí simulada)
        USUARIOS[email] = generate_password_hash(nueva_password)
        
        flash('Tu contraseña ha sido actualizada con éxito. Ya puedes iniciar sesión.', 'success')
        # Aquí redirigirías a la vista de login
        return "¡Contraseña cambiada con éxito!" 
        
    return '''
        <form method="POST">
            <h2>Introduce tu nueva contraseña</h2>
            <input type="password" name="password" placeholder="Nueva contraseña" required>
            <input type="password" name="confirm_password" placeholder="Confirmar contraseña" required>
            <button type="submit">Restablecer Contraseña</button>
        </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)