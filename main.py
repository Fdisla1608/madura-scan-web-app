from flask import Flask, render_template, request, redirect, url_for, session, jsonify,send_from_directory
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import os
from flask_session import Session
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from ultralytics import YOLO
import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
socketio = SocketIO(app)

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar el modelo YOLOv5
model = YOLO("./best.pt")

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host='maptest.ddns.net',
            database='Madura_Scan_DB',
            user='santia_go',
            password='Root1234@'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL database: {e}")
        return None

def close_db_connection(connection):
    if connection.is_connected():
        connection.close()

def obtener_id_fruta(cursor, fruta):
    query = "SELECT id FROM fruta WHERE descripcion = %s"
    cursor.execute(query, (fruta,))
    result = cursor.fetchone()
    if result:
        return result['id']
    else:
        raise Exception(f"No se encontró la fruta: {fruta}")

def obtener_id_estado_fruta(cursor, estado):
    query = "SELECT id FROM estado_fruta WHERE descripcion = %s"
    cursor.execute(query, (estado,))
    result = cursor.fetchone()
    if result:
        return result['id']
    else:
        raise Exception(f"No se encontró el estado de fruta: {estado}")

@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        userId = session.get('user_id', 'Unknown ID')
        userType = session.get('user_type', 'Unknown Type')
        return render_template('index.html', username=username, user_id=userId, user_type=userType)
        
    return redirect(url_for('login'))

@app.route('/scan')
def scan():
    if 'username' in session:
        username = session['username']
        userId = session.get('user_id', 'Unknown ID')
        userType = session.get('user_type', 'Unknown Type')
        return render_template('scan.html',username=username, user_id=userId,user_type=userType)
    return redirect(url_for('login'))

@app.route('/users')
def users():
    if 'username' in session:
        username = session['username']
        userId = session.get('user_id', 'Unknown ID')
        userType = session.get('user_type', 'Unknown Type')
        if userType == 1:
            return render_template('users.html',username=username, user_id=userId,user_type=userType)
        return redirect(url_for('scan'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuario WHERE usuario = %s", (username,))
            user = cursor.fetchone()
            close_db_connection(connection)
            
            if user and check_password_hash(user['pwd'], password):
                session['username'] = username
                session['user_id'] = user['id']
                session['user_type'] = user['fk_tipo_usuario']  # Asumiendo que 'fk_tipo_usuario' es el campo correspondiente
                return redirect(url_for('index'))
            else:
                return "Invalid username or password", 401
        else:
            return "Database connection error", 500

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Ruta para obtener todos los usuarios
@app.route('/api/usuarios', methods=['GET'])
def obtener_usuarios():
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuario")
            usuarios = cursor.fetchall()
            cursor.close()
            return jsonify(usuarios), 200
        except Error as e:
            print(f"Error retrieving users from database: {e}")
            return jsonify({"error": "Database error"}), 500
        finally:
            connection.close()
    else:
        return jsonify({"error": "Database connection error"}), 500

# Ruta para obtener un usuario por ID
@app.route('/api/usuarios/<int:id>', methods=['GET'])
def obtener_usuario_por_id(id):
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuario WHERE id = %s", (id,))
            usuario = cursor.fetchone()
            cursor.close()
            if usuario:
                return jsonify(usuario), 200
            else:
                return jsonify({"error": "Usuario no encontrado"}), 404
        except Error as e:
            print(f"Error retrieving user from database: {e}")
            return jsonify({"error": "Database error"}), 500
        finally:
            connection.close()
    else:
        return jsonify({"error": "Database connection error"}), 500

# Ruta para crear un nuevo usuario
@app.route('/api/usuarios', methods=['POST'])
def crear_usuario():
    data = request.json
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    telefono = data.get('telefono')
    correo = data.get('correo_electronico')
    usuario = data.get('usuario')
    pwd = generate_password_hash(data.get('pwd'))
    fecha_nacimiento = data.get('fecha_nacimiento')
    fecha_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    fk_tipo_usuario = data.get('fk_tipo_usuario', 1)  # Ajustar según tu lógica de asignación de tipo de usuario

    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            insert_query = """
                INSERT INTO usuario (nombre, apellido, telefono, correo_electronico, usuario, pwd, fecha_nacimiento, fecha_registro, fk_tipo_usuario)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (nombre, apellido, telefono, correo, usuario, pwd, fecha_nacimiento, fecha_registro, fk_tipo_usuario))
            connection.commit()
            cursor.close()
            return jsonify({"message": "Usuario creado exitosamente"}), 201
        except Error as e:
            print(f"Error creating user in database: {e}")
            return jsonify({"error": "Database error"}), 500
        finally:
            connection.close()
    else:
        return jsonify({"error": "Database connection error"}), 500

# Ruta para actualizar un usuario por ID
@app.route('/api/usuarios/<int:id>', methods=['PUT'])
def actualizar_usuario(id):
    data = request.json
    id = data.get("id")
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    telefono = data.get('telefono')
    correo = data.get('correo_electronico')
    usuario = data.get('usuario')
    pwd = generate_password_hash(data.get('pwd'))
    fecha_nacimiento = data.get('fecha_nacimiento')

    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            update_query = """
                UPDATE usuario
                SET nombre = %s, 
                    apellido = %s, 
                    telefono = %s, 
                    correo_electronico = %s, 
                    usuario = %s, 
                    pwd = %s,
                    fecha_nacimiento = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (nombre, apellido, telefono, correo, usuario, pwd, fecha_nacimiento, id))
            connection.commit()
            cursor.close()
            return jsonify({"message": "Usuario actualizado exitosamente"}), 200
        except Error as e:
            print(f"Error updating user in database: {e}")
            return jsonify({"error": "Database error"}), 500
        finally:
            connection.close()
    else:
        return jsonify({"error": "Database connection error"}), 500

# Ruta para eliminar un usuario por ID
@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
def eliminar_usuario(id):
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            delete_query = "DELETE FROM usuario WHERE id = %s"
            cursor.execute(delete_query, (id,))
            connection.commit()
            cursor.close()
            return jsonify({"message": "Usuario eliminado exitosamente"}), 200
        except Error as e:
            print(f"Error deleting user from database: {e}")
            return jsonify({"error": "Database error"}), 500
        finally:
            connection.close()
    else:
        return jsonify({"error": "Database connection error"}), 500



@app.route('/guardar_transacciones', methods=['POST'])
def guardar_transacciones():
    try:
        data = request.json  # Recibir datos JSON del cuerpo del POST
        fruit_states = data.get('fruitStates', {})
        image_data = data.get('image', '')

        user_id = 1  # ID del usuario que realiza la transacción (ajustar según tu aplicación)
        logger.info(f"Datos recibidos para guardar transacciones: {fruit_states}")

        # Decodificar la imagen base64 si existe
        filename = None
        if image_data:
            try:
                header, encoded = image_data.split(',', 1)
                file_data = base64.b64decode(encoded)
                filename = f"image_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                with open(filepath, 'wb') as f:
                    f.write(file_data)
                
                logger.info(f"Imagen guardada como {filepath}")
            except Exception as e:
                logger.error(f"Error al procesar la imagen: {e}")
                return jsonify({'error': f'Error al procesar la imagen: {e}'}), 500

        # Iniciar cursor para ejecutar consultas SQL
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            # Crear un nuevo ticket
            insert_ticket_query = """
                INSERT INTO ticket (fk_usuario, img_name, fecha_registro)
                VALUES (%s, %s, %s)
            """
            fecha_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(insert_ticket_query, (user_id, filename, fecha_registro))
            ticket_id = cursor.lastrowid
            logger.info(f"Nuevo ticket creado con ID: {ticket_id}")

            # Iterar sobre las frutas y estados recibidos
            for fruta, estados in fruit_states.items():
                logger.info(f"Procesando fruta: {fruta} con estados: {estados}")
                for estado, cantidad in estados.items():
                    if cantidad > 0:
                        logger.info(f"Procesando estado: {estado} con cantidad: {cantidad}")
                        try:
                            # Obtener IDs de fruta y estado_fruta desde la base de datos
                            fruta_id = obtener_id_fruta(cursor, fruta)
                            estado_fruta_id = obtener_id_estado_fruta(cursor, estado)
                            logger.info(f"Obtenidos IDs - Fruta: {fruta_id}, Estado: {estado_fruta_id}, Cantidad: {cantidad}")

                            # Insertar transacción en la base de datos
                            insert_query = """
                                INSERT INTO transaccion (fk_ticket, fk_fruta, fk_estado_fruta, cantidad)
                                VALUES (%s, %s, %s, %s)
                            """
                            cursor.execute(insert_query, (ticket_id, fruta_id, estado_fruta_id, cantidad))
                            connection.commit()
                            logger.info(f"Transacción insertada para fruta {fruta_id} y estado {estado_fruta_id}")
                        except Exception as e:
                            logger.error(f"Error procesando fruta {fruta} y estado {estado}: {e}")
            cursor.close()
            return jsonify({"message": "Transacciones guardadas exitosamente", "image_url": f"/uploads/{filename}"}), 200
        else:
            return "Database connection error", 500
    except Exception as e:
        logger.error(f"Error en guardar_transacciones: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/data', methods=['POST'])
def receive_data():
    if not request.is_json:
        return jsonify({"error": "Invalid JSON"}), 400

    data = request.get_json()
    logger.info(f"Datos recibidos: {data}")

    # Conectar a la base de datos
    connection = create_db_connection()
    if connection:
        # Obtener datos de frutas y registros de transacciones
        user, fruit_data, records = get_fruit_data(connection)
        connection.close()

        # Formatear los datos en la estructura requerida
        result = format_data(user, fruit_data, records)

        # Emitir datos actualizados al dashboard
        socketio.emit('dashboard_update', result)

        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Database connection error"}), 500

@socketio.on('video_frame')
def handle_video_frame(data):
    try:
        if ',' in data:
            header, frame_data = data.split(',', 1)
        else:
            frame_data = data

        frame_data = base64.b64decode(frame_data)
        np_data = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

        if frame is None or frame.size == 0:
            raise ValueError("El frame está vacío o no se ha decodificado correctamente")

        # Aquí agregar el código para las anotaciones con YOLO
        processed_frame = predict_and_detect(model, frame, classes=[], conf=0.5)

        _, buffer = cv2.imencode('.jpg', processed_frame)
        frame_encoded = base64.b64encode(buffer).decode('utf-8')

        emit('processed_frame', 'data:image/jpeg;base64,' + frame_encoded)

    except Exception as e:
        logger.error(f"Error procesando el frame: {e}")

def predict(chosen_model, img, classes=[], conf=0.5):
    if classes:
        results = chosen_model.predict(img, classes=classes, conf=conf)
    else:
        results = chosen_model.predict(img, conf=conf)
    return results

def predict_and_detect(chosen_model, img, classes=None, conf=0.5):
    results = predict(chosen_model, img, classes, conf)

    fruit_states = {
        "banana": {"verde": 0, "madura": 0, "descompuesto": 0},
        "limon": {"verde": 0, "madura": 0, "descompuesto": 0},
        "mango": {"verde": 0, "madura": 0, "descompuesto": 0}
    }

    for result in results:
        for box in result.boxes:
            cv2.rectangle(img, (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
                          (int(box.xyxy[0][2]), int(box.xyxy[0][3])), (255, 0, 0), 2)
            class_name = result.names[int(box.cls[0])]
            cv2.putText(img, class_name,
                        (int(box.xyxy[0][0]), int(box.xyxy[0][1]) - 10),
                        cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)
            
            print(class_name)
            
            if "banano" in class_name:
                if "verde" in class_name:
                    fruit_states["banana"]["verde"] += 1
                elif "madura" in class_name:
                    fruit_states["banana"]["madura"] += 1
                elif "descompuesto" in class_name:
                    fruit_states["banana"]["descompuesto"] += 1
            elif "Limon" in class_name:
                if "Verde" in class_name:
                    fruit_states["limon"]["verde"] += 1
                elif "maduro" in class_name:
                    fruit_states["limon"]["madura"] += 1
                elif "descompuesto" in class_name:
                    fruit_states["limon"]["descompuesto"] += 1
            elif "mango" in class_name:
                if "verde" in class_name:
                    fruit_states["mango"]["verde"] += 1
                elif "maduro" in class_name:
                    fruit_states["mango"]["madura"] += 1
                elif "descompuesto" in class_name:
                    fruit_states["mango"]["descompuesto"] += 1

    json_array = json.dumps(fruit_states, indent=4)
    emit('processed_data', json_array)
    return img

def get_fruit_data(connection):
    cursor = connection.cursor(dictionary=True)
    userId = session.get('user_id', '0')
    print(userId)
    cursor.execute("SELECT nombre, apellido FROM usuario WHERE id = %s", (userId,))
    user = cursor.fetchone()

    cursor.execute("""
    SELECT 
        f.descripcion AS fruta, 
        ef.descripcion AS estado, 
        CAST(SUM(t.cantidad) AS UNSIGNED) as cantidad
    FROM transaccion t
    JOIN fruta f ON t.fk_fruta = f.id
    JOIN estado_fruta ef ON t.fk_estado_fruta = ef.id
    JOIN ticket ti ON t.fk_ticket = ti.id
    GROUP BY f.descripcion, ef.descripcion;
    """)
    
    fruit_data = cursor.fetchall()

    cursor.execute("""
    SELECT 
        img_name AS cod,
        CONCAT(fruta.descripcion, ' ', estado_fruta.descripcion, ' -> ', cantidad) as Descripcion,
        usuario.usuario as usuario,
        ticket.fecha_registro AS fecha
        FROM transaccion
        INNER JOIN fruta ON transaccion.fk_fruta = fruta.id
        INNER JOIN estado_fruta ON transaccion.fk_estado_fruta = estado_fruta.id
        INNER JOIN ticket ON transaccion.fk_ticket = ticket.id
        INNER JOIN usuario ON ticket.fk_usuario = usuario.id;
    """)
    records = cursor.fetchall()

    return user, fruit_data, records

def format_data(user, fruit_data, records):
    fruit_states = {
        "limon": {"verde": 0, "maduro": 0, "descompuesto": 0},
        "banana": {"verde": 0, "maduro": 0, "descompuesto": 0},
        "mango": {"verde": 0, "maduro": 0, "descompuesto": 0}
    }

    for item in fruit_data:
        fruta = item['fruta'].lower()
        estado = item['estado'].lower()
        cantidad = item['cantidad']

        if fruta in fruit_states:
            if estado in fruit_states[fruta]:
                fruit_states[fruta][estado] = cantidad

    nombre_completo = f"{user['nombre']} {user['apellido']}"

    transacciones = []
    for record in records:
        transacciones.append({
            "cod": f"{record['cod']}",
            "Descripcion": f"[{record['Descripcion']}]",
            "user":f"[{record['usuario']}]",
            "fecha": record['fecha'].strftime('%Y-%m-%d')
        })

    result = {
        "nombre": nombre_completo,
        "frutas": fruit_states,
        "registros": transacciones
    }

    return result

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4000)
    #socketio.run(app, debug=True)
