from flask import Flask, request, jsonify
from flask.helpers import make_response
from flask_mysqldb import MySQL
from flask_cors import CORS, cross_origin


# para subir archivos
import os
#from werkzeug.utils import secure_filename


app = Flask(__name__)

import os

app.config["MYSQL_HOST"] = os.environ.get("DB_HOST")
app.config["MYSQL_USER"] = os.environ.get("DB_USER")
app.config["MYSQL_PASSWORD"] = os.environ.get("DB_PASSWORD")
app.config["MYSQL_DB"] = os.environ.get("DB_NAME")

mysql = MySQL(app)

CORS(app)

'''
@app.route("/nuevo_usuario", methods=["POST"])
@cross_origin()
def insertar_usuario():
    nombre = request.json["nombre"]
    apellido = request.json["apellido"]
    provincia = request.json["provincia"]

    cursor = mysql.connection.cursor()

    sql = "INSERT INTO Usuarios(nombre, apellido, provincia) values(%s, %s, %s);"
    cursor.execute(sql, (nombre, apellido, provincia))


    mysql.connection.commit()

    cursor.close()
    response = make_response()

    response = jsonify({"resultado":"Agregado nuevo usuario"})
    return response

@app.route("/traer_usuarios", methods=["GET"])
@cross_origin()
def listar_jugadores():
    #consulta SQL
    sql = "SELECT idUsuarios, nombre, apellido, provincia FROM Usuarios"

    #crear el cursor
    cursor = mysql.connection.cursor()#mysql.connect.cursor()
    cursor.execute(sql)

    resultado = cursor.fetchall()

    #cerrar la conexión
    cursor.close()
    response = make_response()

    if resultado == None:
        response = jsonify({"mensaje":None})
        return response
    else:
        usuarios = []

        for i in resultado:

            p = {"id":i[0], "nombre":i[1], "apellido":i[2], "provincia":i[3]}
            usuarios.append(p)

        return jsonify(usuarios)


@cross_origin
@app.route("/eliminar_usuario/<id>", methods=["DELETE"])
def eliminar_usuario(id):

    sql = "DELETE FROM Usuarios WHERE idUsuarios=%s"

    #crear el cursor
    cursor = mysql.connection.cursor()
    cursor.execute(sql, (id,))

    mysql.connection.commit()

    #cerrar la conexión
    cursor.close()
    response = make_response()


    response = jsonify({"resultado":"Usuario eliminado"})
    return response


@cross_origin
@app.route("/actualizar_usuario/<id>", methods=["PUT"])
def actualizar_usuario(id):
    nombre = request.json["nom"]

    sql = "UPDATE Usuarios SET nombre=%s WHERE idUsuarios=%s"

    #crear el cursor
    cursor = mysql.connection.cursor()
    cursor.execute(sql, (nombre, id))
    mysql.connection.commit()


    #cerrar la conexión
    cursor.close()
    response = make_response()

    response = jsonify({"resultado":"Usuario no activo"})
    return response

'''
#####################################################################################

#PROYECTO

@app.route("/nuevo_usuario", methods=["POST"])
@cross_origin()
def insertar_usuario():
    nombre = request.json["nombre"]
    apellido = request.json["apellido"]
    provincia = request.json["provincia"]

    cursor = mysql.connection.cursor()

    sql = "INSERT INTO Usuarios(nombre, apellido, provincia) values(%s, %s, %s);"
    cursor.execute(sql, (nombre, apellido, provincia))


    mysql.connection.commit()

    cursor.close()
    response = make_response()

    response = jsonify({"resultado":"Agregado nuevo usuario"})
    return response

@app.route("/traer_usuarios", methods=["GET"])
@cross_origin()
def listar_jugadores():
    #consulta SQL
    sql = "SELECT idUsuarios, nombre, apellido, provincia FROM Usuarios"

    #crear el cursor
    cursor = mysql.connection.cursor()#mysql.connect.cursor()
    cursor.execute(sql)

    resultado = cursor.fetchall()

    #cerrar la conexión
    cursor.close()
    response = make_response()

    if resultado == None:
        response = jsonify({"mensaje":None})
        return response
    else:
        usuarios = []

        for i in resultado:

            p = {"id":i[0], "nombre":i[1], "apellido":i[2], "provincia":i[3]}
            usuarios.append(p)

        return jsonify(usuarios)


@cross_origin
@app.route("/eliminar_usuario/<id>", methods=["DELETE"])
def eliminar_usuario(id):

    sql = "DELETE FROM Usuarios WHERE idUsuarios=%s"

    #crear el cursor
    cursor = mysql.connection.cursor()
    cursor.execute(sql, (id,))

    mysql.connection.commit()

    #cerrar la conexión
    cursor.close()
    response = make_response()


    response = jsonify({"resultado":"Usuario eliminado"})
    return response


@cross_origin
@app.route("/actualizar_usuario/<id>", methods=["PUT"])
def actualizar_usuario(id):
    nombre = request.json["nom"]

    sql = "UPDATE Usuarios SET nombre=%s WHERE idUsuarios=%s"

    #crear el cursor
    cursor = mysql.connection.cursor()
    cursor.execute(sql, (nombre, id))
    mysql.connection.commit()


    #cerrar la conexión
    cursor.close()
    response = make_response()

    response = jsonify({"resultado":"Usuario no activo"})
    return response



#########################################################################

# Proyecto

# ================================
# SECCIÓN: REGISTRO DE ASISTENCIA

# ----------------------------------------------------------------
# ENDPOINTS
# ----------------------------------------------------------------
@app.route("/modalidad", methods=["POST"])
@cross_origin()
def insertar_modalidad():
    try:
        datos = request.get_json(force=True)
        nombre_modalidad = datos["nombre_modalidad"] # Ejemplo: "Técnica", "Bachiller"

        cursor = mysql.connection.cursor()
        sql = "INSERT INTO Modalidad(nombre_modalidad) VALUES (%s);" # Ajusta 'nombre_modalidad' al nombre real de tu columna
        cursor.execute(sql, (nombre_modalidad,))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"resultado": "Modalidad agregada correctamente"}), 201
    except Exception as e:
        return jsonify({"error": f"Error al guardar modalidad: {str(e)}"}), 500
    
@app.route("/nueva_asistencia", methods=["POST"])
@cross_origin()
def insertar_asistencia():

    try:
        datos = request.get_json(force=True)
        fecha = datos.get("fecha")
        #hora = datos["hora"]
        #id_preceptor = datos["id_preceptor"]
        legajo_alumno = datos.get("id_alumno")
        tipo_asistencia = datos.get("opcionSeleccionada")

        cursor = mysql.connection.cursor()
        sql0= "Select idAlumno from alumno where legajo = %s"
        cursor.execute(sql0, (legajo_alumno,))
        resultado = cursor.fetchone()
        id_alumno = resultado[0]

        print("fecha: ", fecha, flush=True)
        print("legajo: ", legajo_alumno, flush=True)
        print("tipo: ", tipo_asistencia, flush=True)
        print("idalumno: ", id_alumno, flush=True)


        RUTA_VOLUME = "/data"
        NOMBRE_ARCHIVO = "debug_asistencia.txt"
        ruta_completa = os.path.join(RUTA_VOLUME, NOMBRE_ARCHIVO)

        os.makedirs(RUTA_VOLUME, exist_ok=True)

        texto = (
        f"Fecha: {fecha}, "
        f"Datos recibidos: {datos}, "
        f"Legajo: {legajo_alumno}, "
        f"Legajo limpio: {id_alumno}, "
        f"tipo asistencia: {tipo_asistencia}\n"   # ← \n importante
    )
        
        with open(ruta_completa, "a", encoding="utf-8") as f:
            f.write(texto)


        sql = "INSERT INTO asistencia(fecha, Alumno_idAlumno, tipo_asistencia_idtipo_asistencia) VALUES (%s, %s, %s)"
        cursor.execute(sql, (fecha, id_alumno, tipo_asistencia))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"resultado": "Asistencia registrada correctamente"}), 201
    except Exception as e:
        return jsonify({"error": f"Error en el registro de asistencia: {str(e)}"}), 500


@app.route("/traer_asistencias", methods=["GET"])
@cross_origin()
def listar_asistencias():
    try:
        sql = "SELECT idasistencia, fecha, estado, preceptor_idpreceptor, Alumno_idAlumno FROM Asistencia"
        cursor = mysql.connection.cursor()
        cursor.execute(sql)
        resultado = cursor.fetchall()
        cursor.close()

        if not resultado:
            return jsonify([])
        
        asistencias = []
        for i in resultado:
            fecha_str = i[1].strftime('%Y-%m-%d %H:%M:%S') if hasattr(i[1], 'strftime') else str(i[1])
            asistencias.append({
                "id_asistencia": i[0],
                "fecha": fecha_str,
                "estado": i[2],
                "id_preceptor": i[3],
                "id_alumno": i[4]
            })
            
        return jsonify(asistencias), 200
    except Exception as e:
        return jsonify({"error": f"Error al listar: {str(e)}"}), 500


@app.route("/preceptor", methods=["POST"])
@cross_origin()
def insertar_preceptor():
    try:
        datos = request.get_json(force=True)
        nombre_usuario = datos["nombre_usuario"]
        email = datos["email"]
        # Cambiado a 'contrasena' para evitar conflictos con la 'ñ' en variables de Python
        contrasena = datos["contraseña"] 

        cursor = mysql.connection.cursor()
        sql = "INSERT INTO Preceptor(nombre_usuario, email, contraseña) VALUES (%s, %s, %s);"
        cursor.execute(sql, (nombre_usuario, email, contrasena))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"resultado": "Preceptor registrado correctamente"}), 201
    except Exception as e:
        return jsonify({"error": f"Error al guardar preceptor: {str(e)}"}), 500


@app.route("/alumno", methods=["POST"])
@cross_origin()
def insertar_alumno():
    try:
        datos = request.get_json(force=True)
        nombre = datos["nombre"]
        apellido = datos["apellido"]
        Cursos_idCursos = datos["Cursos_idCursos"]

        cursor = mysql.connection.cursor()
        sql = "INSERT INTO Alumno(nombre, apellido, Cursos_idCursos) VALUES (%s, %s, %s);"
        cursor.execute(sql, (nombre, apellido, Cursos_idCursos))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"resultado": "Alumno registrado correctamente"}), 201
    except Exception as e:
        return jsonify({"error": f"Error al guardar alumno: {str(e)}"}), 500


@app.route('/nueva_notificacion', methods=['POST'])
def nueva_notificacion():
    data = request.get_json()
    
    # Extraemos los datos del JSON
    titulo = data.get('titulo')
    mensaje = data.get('mensaje')
    fecha = data.get('fecha')
    Alumno_idAlumno = data.get('Alumno_idAlumno')
    
    # Validamos que el ID del alumno esté presente (ya que es NOT NULL)
    if not Alumno_idAlumno:
        return jsonify({"error": "El campo 'Alumno_idAlumno' es obligatorio."}), 400

    try:
        # Creamos el cursor y ejecutamos la consulta igual que con tus Cursos
        cursor = mysql.connection.cursor()
        sql = "INSERT INTO Notificacion(titulo, mensaje, fecha, Alumno_idAlumno) VALUES (%s, %s, %s, %s);"
        cursor.execute(sql, (titulo, mensaje, fecha, Alumno_idAlumno))
        mysql.connection.commit()
        cursor.close()

        return jsonify({
            "status": "Exito",
            "mensaje": "Notificación guardada en la base de datos correctamente."
        }), 201

    except Exception as e:
        return jsonify({
            "error": f"Error al registrar la notificación: {str(e)}"
        }), 500


@app.route("/probar_conexion_db", methods=["GET"])
def probar_conexion_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        resultado = cursor.fetchone()
        cursor.close()

        return jsonify({
            "conexion": "exitosa",
            "mensaje": "El backend pudo conectarse a MySQL correctamente"
        }), 200

    except Exception as e:
        print("ERROR DE CONEXION MYSQL:", str(e), flush=True)

        return jsonify({
            "conexion": "fallida",
            "mensaje": "No se pudo conectar con la base de datos"
        }), 500


# ==========================================
# AUTENTICACIÓN INSTITUCIONAL
# ==========================================

import unicodedata
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
DOMINIO_INSTITUCIONAL = "@sagradoalcal.edu.ar"


def normalizar_rol(rol):
    if not rol:
        return ""

    rol = unicodedata.normalize("NFD", rol)
    rol = "".join(
        caracter for caracter in rol
        if unicodedata.category(caracter) != "Mn"
    )
    rol = rol.strip().lower().replace(" ", "_")

    equivalencias = {
        "exalumno": "ex_alumno",
        "ex_alumnos": "ex_alumno",
        "antiguo_alumno": "ex_alumno",
        "director": "conduccion",
        "coordinador": "conduccion",
        "secretaria": "secretaria"
    }
    return equivalencias.get(rol, rol)


def respuesta_usuario(resultado):
    return {
        "id": resultado[0],
        "nombre": resultado[1],
        "apellido": resultado[2],
        "email": resultado[3],
        "rol": normalizar_rol(resultado[4])
    }


# Login manual: únicamente Secretaría y Conducción
@app.route("/login", methods=["POST"])
@cross_origin()
def iniciar_sesion():
    cursor = None
    try:
        datos = request.get_json(force=True) or {}
        email = datos.get("email", "").strip().lower()
        contrasena = datos.get("password", "")

        if not email or not contrasena:
            return jsonify({"error": "Tenés que ingresar correo y contraseña."}), 400

        if not email.endswith(DOMINIO_INSTITUCIONAL):
            return jsonify({"error": "Solo se permiten correos institucionales."}), 403

        cursor = mysql.connection.cursor()
        sql = """
            SELECT u.id, u.nombre, u.apellido, u.email, r.nombre_rol, u.contrasenia
            FROM usuario u
            LEFT JOIN roles r ON u.rol_id = r.idINT
            WHERE LOWER(u.email) = %s
            LIMIT 1
        """
        cursor.execute(sql, (email,))
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({"error": "Correo o contraseña incorrectos."}), 401

        rol = normalizar_rol(resultado[4])
        contrasena_guardada = resultado[5] or ""

        if rol not in ["secretaria", "conduccion"]:
            return jsonify({"error": "Este perfil debe ingresar con Google."}), 403

        contraseña_valida = False
        if contrasena_guardada.startswith(("scrypt:", "pbkdf2:")):
            contraseña_valida = check_password_hash(contrasena_guardada, contrasena)
        elif contrasena_guardada:
            # Compatibilidad temporal con contraseñas antiguas en texto plano.
            contraseña_valida = contrasena_guardada == contrasena
            if contraseña_valida:
                nuevo_hash = generate_password_hash(contrasena)
                cursor.execute(
                    "UPDATE usuario SET contrasenia = %s WHERE id = %s",
                    (nuevo_hash, resultado[0])
                )
                mysql.connection.commit()

        if not contraseña_valida:
            return jsonify({"error": "Correo o contraseña incorrectos."}), 401

        return jsonify({
            "mensaje": "Inicio de sesión exitoso.",
            "usuario": respuesta_usuario(resultado)
        }), 200

    except Exception as e:
        print("ERROR LOGIN:", str(e), flush=True)
        return jsonify({"error": "Ocurrió un error al iniciar sesión."}), 500
    finally:
        if cursor is not None:
            cursor.close()


# Login con Google: Exalumnos, Secretaría y Conducción
@app.route("/login/google", methods=["POST"])
@cross_origin()
def iniciar_sesion_google():
    cursor = None
    try:
        datos = request.get_json(force=True) or {}
        token = datos.get("credential")

        if not token:
            return jsonify({"error": "No se recibió la credencial de Google."}), 400

        if not GOOGLE_CLIENT_ID:
            return jsonify({"error": "Falta configurar GOOGLE_CLIENT_ID en Railway."}), 500

        informacion_google = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        email_google = informacion_google.get("email", "").lower()

        if not informacion_google.get("email_verified", False):
            return jsonify({"error": "Google no confirmó el correo electrónico."}), 403

        if not email_google.endswith(DOMINIO_INSTITUCIONAL):
            return jsonify({"error": "Tenés que ingresar con tu correo institucional."}), 403

        cursor = mysql.connection.cursor()
        sql = """
            SELECT u.id, u.nombre, u.apellido, u.email, r.nombre_rol
            FROM usuario u
            LEFT JOIN roles r ON u.rol_id = r.idINT
            WHERE LOWER(COALESCE(NULLIF(u.google_email, ''), u.email)) = %s
            LIMIT 1
        """
        cursor.execute(sql, (email_google,))
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({"error": "Tu correo no está habilitado en el sistema."}), 403

        rol = normalizar_rol(resultado[4])
        if rol not in ["ex_alumno", "secretaria", "conduccion"]:
            return jsonify({"error": "Tu perfil no tiene permiso para ingresar."}), 403

        usuario = respuesta_usuario(resultado)
        print("LOGIN GOOGLE EXITOSO:", usuario, flush=True)

        return jsonify ({
            "mensaje": "Inicio de Google exitoso.",
            "usuario": usuario
        }), 200 

    except ValueError:
        return jsonify({"error": "La credencial de Google no es válida."}), 401
    except Exception as e:
        print("ERROR LOGIN GOOGLE:", str(e), flush=True)
        return jsonify({"error": "No se pudo iniciar sesión con Google."}), 500
    finally:
        if cursor is not None:
            cursor.close()

    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)