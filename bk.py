from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
from flask_session import Session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
socketio = SocketIO(app)

# Datos de usuarios de ejemplo
USERS = {
    'root': '1234',
}

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "Invalid username or password", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('video_frame')
def handle_video_frame(data):
    try:
        # Decodificar la imagen desde base64
        if ',' in data:
            header, frame_data = data.split(',', 1)
        else:
            frame_data = data

        # Depuración: Imprimir los primeros caracteres del frame_data
        frame_data = base64.b64decode(frame_data)
        np_data = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

        # Verificar si el frame es válido
        if frame is None or frame.size == 0:
            raise ValueError("El frame está vacío o no se ha decodificado correctamente")

        # Procesar el frame (aquí puedes aplicar cualquier procesamiento adicional si lo deseas)
        # Ejemplo: convertir el frame a escala de grises
        #processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Codificar el frame en formato JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_encoded = base64.b64encode(buffer).decode('utf-8')

        # Enviar el frame procesado de vuelta al cliente
        emit('processed_frame', 'data:image/jpeg;base64,' + frame_encoded)

    except Exception as e:
        print(f"Error procesando el frame: {e}")

if __name__ == "__main__":
    socketio.run(app, debug=True)


# Importamos las librerias
from ultralytics import YOLO
import cv2

# Leer nuestro modelo
model = YOLO("best.pt")

# Realizar VideoCaptura
cap = cv2.VideoCapture(1)

# Bucle
while True:
    # Leer nuestros fotogramas
    ret, frame = cap.read()

    # Leemos resultados
    resultados = model.predict(frame, imgsz = 640, conf = 0.50)

    # Mostramos resultados
    anotaciones = resultados[0].plot()

    # Mostramos nuestros fotogramas
    cv2.imshow("DETECCION Y SEGMENTACION", anotaciones)

    # Cerrar nuestro programa
    if cv2.waitKey(1) == 27:
        break

        

cap.release()
cv2.destroyAllWindows()
