from flask import Flask, request, jsonify
from flask.helpers import make_response
from flask_mysqldb import MySQL
from flask_cors import CORS, cross_origin
from werkzeug.security import check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# para subir archivos
import os
#from werkzeug.utils import secure_filename

import mysql.connector
import os

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQLHOST'),
        user=os.getenv('MYSQLUSER'),
        password=os.getenv('MYSQLPASSWORD'),
        database=os.getenv('MYSQLDATABASE'),
        port=int(os.getenv('MYSQLPORT', 3306))
    )

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False

import os

app.config["MYSQL_HOST"] = os.environ.get("DB_HOST")
app.config["MYSQL_USER"] = os.environ.get("DB_USER")
app.config["MYSQL_PASSWORD"] = os.environ.get("DB_PASSWORD")
app.config["MYSQL_DB"] = os.environ.get("DB_NAME")

mysql = MySQL(app)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "OPTIONS"]
)


DOMINIO_INSTITUCIONAL = "@sagradoalcal.edu.ar"

# ==========================================
# SESIONES DE USUARIO
# ==========================================

SECRET_KEY = os.environ.get("SECRET_KEY")

def crear_token_sesion(user_id):
    if not SECRET_KEY:
        raise RuntimeError("Falta configurar SECRET_KEY en Railway.")

    serializer = URLSafeTimedSerializer(SECRET_KEY)

    return serializer.dumps(
        {"user_id": user_id},
        salt="sesion-colegio"
    )


def obtener_usuario_del_token():
    encabezado = request.headers.get("Authorization", "")

    if not encabezado.startswith("Bearer "):
        return None

    token = encabezado.replace("Bearer ", "", 1).strip()

    if not token or not SECRET_KEY:
        return None

    try:
        serializer = URLSafeTimedSerializer(SECRET_KEY)

        datos = serializer.loads(
            token,
            salt="sesion-colegio",
            max_age=43200  # 12 horas
        )

        return datos.get("user_id")

    except (BadSignature, SignatureExpired):
        return None

def obtener_usuario_por_email(email):
    cursor = mysql.connection.cursor()

    sql = """
        SELECT
            u.id,
            u.nombre,
            u.apellido,
            u.email,
            u.contrasenia,
            u.google_email,
            r.nombre_rol
        FROM usuario u
        LEFT JOIN roles r ON u.rol_id = r.idINT
        WHERE LOWER(u.email) = LOWER(%s)
        LIMIT 1
    """

    cursor.execute(sql, (email,))
    usuario = cursor.fetchone()
    cursor.close()

    return usuario


def validar_rol(rol):
    rol = str(rol or "").strip().lower()

    equivalencias = {
        "exalumno": "ex_alumno",
        "ex-alumno": "ex_alumno",
        "ex_alumno": "ex_alumno",
        "secretaria": "secretaria",
        "secretario": "secretaria",
        "director": "conduccion",
        "coordinador": "conduccion",
        "conduccion": "conduccion"
    }

    return equivalencias.get(rol, "")


def preparar_respuesta_usuario(usuario):
    return {
        "id": usuario[0],
        "nombre": usuario[1],
        "apellido": usuario[2],
        "email": usuario[3],
        "rol": validar_rol(usuario[6])
    }

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



@app.route("/api/alumnos", methods=["GET"])
@cross_origin()
def listar_alumnos():
    try:
        # Cambiamos 'Alumno' por 'alumno' (en minúscula)
        sql = "SELECT idAlumno, nombre, apellido FROM alumno"
        cursor = mysql.connection.cursor()
        cursor.execute(sql)
        resultado = cursor.fetchall()
        cursor.close()

        if not resultado:
            return jsonify([]), 200

        alumnos = []
        for row in resultado:
            alumnos.append({
                "id": row[0],
                "nombre": row[1],
                "apellido": row[2]
            })

        return jsonify(alumnos), 200

    except Exception as e:
        return jsonify({"error": f"Error al obtener alumnos: {str(e)}"}), 500
    

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


@app.route("/login", methods=["POST", "OPTIONS"])
def iniciar_sesion():

    if request.method == "OPTIONS":
        return "", 200

    try:
        datos = request.get_json(silent=True) or {}

        email = datos.get("email", "").strip().lower()
        password = datos.get("password", "")

        if not email or not password:
            return jsonify({
                "error": "Ingresá tu correo y contraseña."
            }), 400

        if not email.endswith(DOMINIO_INSTITUCIONAL):
            return jsonify({
                "error": "Debes utilizar un correo institucional."
            }), 403

        usuario = obtener_usuario_por_email(email)

        if not usuario:
            return jsonify({
                "error": "Usuario no encontrado."
            }), 401

        contrasena_guardada = usuario[4]

        # Contraseñas cifradas con Werkzeug
        try:
            contrasena_valida = check_password_hash(
                contrasena_guardada,
                password
            )
        except (ValueError, TypeError):
            contrasena_valida = False

        # Compatibilidad temporal con contraseñas antiguas sin cifrar.
        if not contrasena_valida:
            contrasena_valida = (
                contrasena_guardada == password
            )

        if not contrasena_valida:
            return jsonify({
                "error": "Contraseña incorrecta."
            }), 401

        datos_usuario = preparar_respuesta_usuario(usuario)

        if not datos_usuario["rol"]:
            return jsonify({
                "error": "Tu cuenta no tiene un rol habilitado."
            }), 403

        token_sesion = crear_token_sesion(datos_usuario["id"])

        return jsonify({
        "mensaje": "Inicio de sesión exitoso.",
        "usuario": datos_usuario,
        "token": token_sesion
        }), 200

    except Exception as e:
        print("ERROR LOGIN:", str(e), flush=True)

        return jsonify({
            "error": "Error interno al iniciar sesión."
        }), 500


@app.route("/login/google", methods=["POST", "OPTIONS"])
def login_google():

    if request.method == "OPTIONS":
        return "", 200

    try:
        datos = request.get_json(silent=True) or {}

        credential = datos.get("credential")

        if not credential:
            return jsonify({
                "error": "No se recibió la credencial de Google."
            }), 400

        GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")

        if not GOOGLE_CLIENT_ID:
            return jsonify({
                "error": "Falta configurar GOOGLE_CLIENT_ID en Railway."
            }), 500

        # Verificar la identidad directamente con Google
        informacion_google = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        google_email = informacion_google.get("email", "").lower()
        email_verificado = informacion_google.get("email_verified", False)

        if not email_verificado:
            return jsonify({
                "error": "Google no pudo verificar tu correo."
            }), 403

        # Buscar la cuenta institucional en nuestra base de datos.
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                u.id,
                u.nombre,
                u.apellido,
                u.email,
                u.contrasenia,
                u.google_email,
                r.nombre_rol
            FROM usuario u
            LEFT JOIN roles r ON u.rol_id = r.idINT
            WHERE LOWER(u.google_email) = LOWER(%s)
               OR LOWER(u.email) = LOWER(%s)
            LIMIT 1
        """

        cursor.execute(sql, (google_email, google_email))
        usuario = cursor.fetchone()
        cursor.close()

        if not usuario:
            return jsonify({
                "error": "Tu cuenta de Google no está registrada en el sistema."
            }), 403

        # La cuenta institucional registrada debe pertenecer al colegio.
        email_institucional = usuario[3].lower()

        if not email_institucional.endswith(DOMINIO_INSTITUCIONAL):
            return jsonify({
                "error": "La cuenta institucional no está habilitada."
            }), 403

        datos_usuario = preparar_respuesta_usuario(usuario)

        if not datos_usuario["rol"]:
            return jsonify({
                "error": "Tu cuenta no tiene un rol habilitado."
            }), 403

        token_sesion = crear_token_sesion(datos_usuario["id"])

        return jsonify({
        "mensaje": "Inicio de sesión con Google exitoso.",
        "usuario": datos_usuario,
        "picture": informacion_google.get("picture"),
        "token": token_sesion
        }), 200
    
    except ValueError as e:
        print("ERROR TOKEN GOOGLE:", str(e), flush=True)

        return jsonify({
            "error": "La credencial de Google no es válida."
        }), 401

    except Exception as e:
        print("ERROR LOGIN GOOGLE:", str(e), flush=True)

        return jsonify({
            "error": "No se pudo verificar la cuenta de Google."
        }), 500


# ==========================================
# PERFIL DEL EXALUMNO
# ==========================================

@app.route("/perfil", methods=["GET", "OPTIONS"])
def obtener_perfil():

    if request.method == "OPTIONS":
        return "", 200

    user_id = obtener_usuario_del_token()

    if not user_id:
        return jsonify({"error": "La sesión no es válida o venció."}), 401

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                u.id,
                u.nombre,
                u.apellido,
                u.email,
                u.telefono,
                p.idperfil,
                p.es_exalumno,
                p.orientacion,
                r.nombre_rol
            FROM usuario u
            LEFT JOIN perfil p ON p.idperfil = u.perfil_idperfil
            LEFT JOIN roles r ON r.idINT = u.rol_id
            WHERE u.id = %s
            LIMIT 1
        """

        cursor.execute(sql, (user_id,))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({"error": "No se encontró el usuario."}), 404

        if validar_rol(usuario[8]) != "ex_alumno":
            return jsonify({"error": "Esta sección es exclusiva para exalumnos."}), 403

        if usuario[5] is None:
            return jsonify({
                "error": "El usuario todavía no tiene un perfil asociado."
            }), 409

        return jsonify({
            "usuario": {
                "id": usuario[0],
                "nombre": usuario[1],
                "apellido": usuario[2],
                "email": usuario[3],
                "telefono": usuario[4] or "",
                "es_exalumno": bool(usuario[6]),
                "orientacion": usuario[7] or ""
            }
        }), 200

    except Exception as e:
        print("ERROR AL OBTENER PERFIL:", str(e), flush=True)
        return jsonify({"error": "No se pudo cargar el perfil."}), 500

    finally:
        if cursor:
            cursor.close()


@app.route("/perfil", methods=["PUT", "OPTIONS"])
def actualizar_perfil():

    if request.method == "OPTIONS":
        return "", 200

    user_id = obtener_usuario_del_token()

    if not user_id:
        return jsonify({"error": "La sesión no es válida o venció."}), 401

    datos = request.get_json(silent=True) or {}

    telefono = str(datos.get("telefono") or "").strip()
    es_exalumno = datos.get("es_exalumno")
    orientacion = datos.get("orientacion")

    if len(telefono) > 20:
        return jsonify({
            "error": "El teléfono no puede superar los 20 caracteres."
        }), 400

    if not isinstance(es_exalumno, bool):
        return jsonify({
            "error": "Tenés que confirmar si sos exalumno."
        }), 400

    if es_exalumno:
        if orientacion not in ["Técnica", "Economía"]:
            return jsonify({
                "error": "Seleccioná Técnica o Economía como orientación."
            }), 400
    else:
        orientacion = None

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        # Comprobar que el usuario exista, sea exalumno
        # y tenga un perfil asociado.
        sql_usuario = """
            SELECT
                u.perfil_idperfil,
                r.nombre_rol
            FROM usuario u
            LEFT JOIN roles r ON r.idINT = u.rol_id
            WHERE u.id = %s
            LIMIT 1
        """

        cursor.execute(sql_usuario, (user_id,))
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({"error": "No se encontró el usuario."}), 404

        perfil_id = resultado[0]
        rol = validar_rol(resultado[1])

        if rol != "ex_alumno":
            return jsonify({
                "error": "No tenés permiso para modificar este perfil."
            }), 403

        if perfil_id is None:
            return jsonify({
                "error": "El usuario no tiene un perfil asociado."
            }), 409

        # Actualizar el teléfono en usuario y los datos
        # propios del exalumno en perfil.
        cursor.execute(
            """
            UPDATE usuario
            SET telefono = %s
            WHERE id = %s
            """,
            (telefono or None, user_id)
        )

        cursor.execute(
            """
            UPDATE perfil
            SET es_exalumno = %s,
                orientacion = %s
            WHERE idperfil = %s
            """,
            (
                1 if es_exalumno else 0,
                orientacion,
                perfil_id
            )
        )

        mysql.connection.commit()

        return jsonify({
            "mensaje": "Perfil actualizado correctamente."
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        print("ERROR AL ACTUALIZAR PERFIL:", str(e), flush=True)

        return jsonify({
            "error": "No se pudo guardar el perfil."
        }), 500

    finally:
        if cursor:
            cursor.close()

# ============================================================
# CARGA DE MATERIAS PENDIENTES - SECRETARIA Y CONDUCCION
# ============================================================

def autorizar_personal_administrativo():
    """
    Comprueba el token de sesión y verifica que el usuario
    tenga rol Secretaría o Conducción.
    """
    user_id = obtener_usuario_del_token()

    if not user_id:
        return None, None, (
            jsonify({"error": "La sesión no es válida o venció."}),
            401
        )

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT r.nombre_rol
            FROM usuario u
            LEFT JOIN roles r ON r.idINT = u.rol_id
            WHERE u.id = %s
            LIMIT 1
        """, (user_id,))

        resultado = cursor.fetchone()

        if not resultado:
            return None, None, (
                jsonify({"error": "No se encontró el usuario."}),
                401
            )

        rol = validar_rol(resultado[0])

        if rol not in ("secretaria", "conduccion"):
            return None, None, (
                jsonify({"error": "No tenés permiso para realizar esta operación."}),
                403
            )

        return user_id, rol, None

    except Exception as e:
        print("ERROR AL VALIDAR PERSONAL:", str(e), flush=True)

        return None, None, (
            jsonify({"error": "No se pudo validar el permiso de acceso."}),
            500
        )

    finally:
        if cursor:
            cursor.close()


def obtener_datos_exalumno(cursor, usuario_id):
    """
    Relaciona:
    usuario.id
       -> usuario.perfil_idperfil
       -> perfil.idperfil
       -> ex_alumno.perfil_idperfil
    """
    cursor.execute("""
        SELECT
            u.id,
            u.nombre,
            u.apellido,
            u.email,
            e.idex_alumno,
            e.alumno_idAlumno,
            p.orientacion
        FROM usuario u
        INNER JOIN perfil p
            ON p.idperfil = u.perfil_idperfil
        INNER JOIN ex_alumno e
            ON e.perfil_idperfil = p.idperfil
        LEFT JOIN roles r
            ON r.idINT = u.rol_id
        WHERE u.id = %s
          AND p.es_exalumno = 1
          AND LOWER(REPLACE(r.nombre_rol, ' ', ''))
              IN ('exalumno', 'ex_alumno')
          AND p.orientacion IN ('Técnica', 'Economía')
        LIMIT 1
    """, (usuario_id,))

    return cursor.fetchone()


# ------------------------------------------------------------
# LISTAR EXALUMNOS PARA SECRETARIA
# ------------------------------------------------------------

@app.route(
    "/api/secretaria/exalumnos",
    methods=["GET", "OPTIONS"]
)
def listar_exalumnos_secretaria():

    if request.method == "OPTIONS":
        return "", 200

    user_id, rol, error = autorizar_personal_administrativo()

    if error:
        return error

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                u.id AS usuario_id,
                u.nombre,
                u.apellido,
                u.email,
                e.idex_alumno,
                e.alumno_idAlumno,
                p.orientacion,
                COUNT(DISTINCT mp.id) AS cantidad_materias
            FROM usuario u
            INNER JOIN perfil p
                ON p.idperfil = u.perfil_idperfil
            INNER JOIN ex_alumno e
                ON e.perfil_idperfil = p.idperfil
            LEFT JOIN roles r
                ON r.idINT = u.rol_id
            LEFT JOIN materias_pendientes mp
                ON mp.ex_alumno_idex_alumno = e.idex_alumno
            WHERE p.es_exalumno = 1
              AND p.orientacion IN ('Técnica', 'Economía')
              AND LOWER(REPLACE(r.nombre_rol, ' ', ''))
                  IN ('exalumno', 'ex_alumno')
            GROUP BY
                u.id,
                u.nombre,
                u.apellido,
                u.email,
                e.idex_alumno,
                e.alumno_idAlumno,
                p.orientacion
            ORDER BY u.apellido, u.nombre
        """)

        filas = cursor.fetchall()

        exalumnos = []

        for fila in filas:
            exalumnos.append({
                "usuario_id": fila[0],
                "nombre": fila[1],
                "apellido": fila[2],
                "email": fila[3],
                "idex_alumno": fila[4],
                "alumno_idAlumno": fila[5],
                "orientacion": fila[6],
                "cantidad_materias": fila[7]
            })

        return jsonify({"exalumnos": exalumnos}), 200

    except Exception as e:
        print("ERROR LISTANDO EXALUMNOS:", str(e), flush=True)

        return jsonify({
            "error": "No se pudieron consultar los exalumnos."
        }), 500

    finally:
        if cursor:
            cursor.close()


# ------------------------------------------------------------
# OBTENER MATERIAS Y MATERIAS YA ASIGNADAS A UN EXALUMNO
# ------------------------------------------------------------

@app.route(
    "/api/secretaria/exalumnos/<int:usuario_id>/materias",
    methods=["GET", "OPTIONS"]
)
def obtener_materias_exalumno(usuario_id):

    if request.method == "OPTIONS":
        return "", 200

    user_id, rol, error = autorizar_personal_administrativo()

    if error:
        return error

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        exalumno = obtener_datos_exalumno(cursor, usuario_id)

        if not exalumno:
            return jsonify({
                "error": "No se encontró un exalumno confirmado con orientación registrada."
            }), 404

        id_exalumno = exalumno[4]
        orientacion = exalumno[6]

        # Las materias se filtran por la orientación del PERFIL.
        # No se utiliza la tabla cursos ni la tabla modalidad.
        cursor.execute("""
            SELECT
                m.idMaterias,
                m.Materiascol,
                m.curso,
                m.orientacion
            FROM materias m
            WHERE LOWER(TRIM(m.orientacion)) = LOWER(TRIM(%s))
              AND m.curso IS NOT NULL
            ORDER BY
                CAST(LEFT(m.curso, 1) AS UNSIGNED),
                m.curso,
                m.idMaterias
        """, (orientacion,))

        filas_materias = cursor.fetchall()

        materias = []

        for fila in filas_materias:
            materias.append({
                "idMaterias": fila[0],
                "nombre": fila[1],
                "curso": fila[2],
                "orientacion": fila[3]
            })

        cursor.execute("""
            SELECT mp.materias_idmaterias
            FROM materias_pendientes mp
            INNER JOIN materias m ON m.idMaterias = mp.materias_idmaterias
            WHERE mp.ex_alumno_idex_alumno = %s
              AND LOWER(TRIM(m.orientacion)) = LOWER(TRIM(%s))
        """, (id_exalumno, orientacion))

        filas_pendientes = cursor.fetchall()

        materias_pendientes = [
            {"materias_idmaterias": fila[0]}
            for fila in filas_pendientes
        ]

        return jsonify({
            "exalumno": {
                "usuario_id": exalumno[0],
                "nombre": exalumno[1],
                "apellido": exalumno[2],
                "email": exalumno[3],
                "idex_alumno": exalumno[4],
                "alumno_idAlumno": exalumno[5],
                "orientacion": exalumno[6]
            },
            "materias": materias,
            "materias_pendientes": materias_pendientes
        }), 200

    except Exception as e:
        print("ERROR OBTENIENDO MATERIAS:", str(e), flush=True)

        return jsonify({
            "error": "No se pudieron consultar las materias."
        }), 500

    finally:
        if cursor:
            cursor.close()


# ------------------------------------------------------------
# GUARDAR MATERIAS PENDIENTES
# ------------------------------------------------------------

@app.route(
    "/api/secretaria/materias-pendientes",
    methods=["POST", "OPTIONS"]
)
def guardar_materias_pendientes():

    if request.method == "OPTIONS":
        return "", 200

    user_id, rol, error = autorizar_personal_administrativo()

    if error:
        return error

    datos = request.get_json(silent=True) or {}

    usuario_id = datos.get("usuario_id")
    materias_ids = datos.get("materias_ids")

    if not usuario_id or not isinstance(materias_ids, list):
        return jsonify({"error": "Los datos recibidos no son válidos."}), 400

    try:
        usuario_id = int(usuario_id)
        materias_ids = list(set(int(x) for x in materias_ids))
    except (ValueError, TypeError):
        return jsonify({"error": "Hay identificadores inválidos."}), 400

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        exalumno = obtener_datos_exalumno(cursor, usuario_id)

        if not exalumno:
            return jsonify({"error": "No se encontró el exalumno confirmado."}), 404

        id_exalumno = exalumno[4]
        id_alumno = exalumno[5]
        orientacion = exalumno[6]

        cursor.execute("""
            SELECT idMaterias
            FROM materias
            WHERE LOWER(TRIM(orientacion)) = LOWER(TRIM(%s))
              AND curso IS NOT NULL
        """, (orientacion,))

        ids_permitidos = {int(fila[0]) for fila in cursor.fetchall()}

        cursor.execute("""
            SELECT materias_idmaterias
            FROM materias_pendientes
            WHERE ex_alumno_idex_alumno = %s
        """, (id_exalumno,))

        ids_existentes = {
            int(fila[0]) for fila in cursor.fetchall()
        }

        nuevas = set(materias_ids) - ids_existentes

        if not nuevas.issubset(ids_permitidos):
            return jsonify({
                "error": "Hay materias que no corresponden a la orientación."
            }), 400

        for materia_id in nuevas:
            cursor.execute("""
                INSERT INTO materias_pendientes (
                    alumno_idAlumno,
                    materias_idmaterias,
                    estado,
                    ex_alumno_idex_alumno
                )
                VALUES (%s, %s, 'Pendiente', %s)
            """, (id_alumno, materia_id, id_exalumno))

        mysql.connection.commit()

        return jsonify({
            "mensaje": "Las nuevas materias pendientes se guardaron correctamente.",
            "cantidad_nuevas": len(nuevas)
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        print("ERROR GUARDANDO MATERIAS:", str(e), flush=True)

        return jsonify({
            "error": "No se pudieron guardar las materias."
        }), 500

    finally:
        if cursor:
            cursor.close()

# ============================================================
# INSCRIPCIÓN A MESAS DE EXAMEN - EXALUMNOS
# ============================================================

@app.route("/api/exalumno/mesas-disponibles", methods=["GET", "OPTIONS"])
def obtener_mesas_exalumno():
    if request.method == "OPTIONS":
        return "", 200

    user_id = obtener_usuario_del_token()
    if not user_id:
        return jsonify({"error": "La sesión no es válida o venció."}), 401

    cursor = None
    try:
        cursor = mysql.connection.cursor()

        exalumno = obtener_datos_exalumno(cursor, user_id)
        if not exalumno:
            return jsonify({
                "error": "No se encontró un perfil de exalumno confirmado con orientación."
            }), 404

        # exalumno: (u.id, u.nombre, u.apellido, u.email, e.idex_alumno, e.alumno_idAlumno, p.orientacion)
        id_exalumno = exalumno[4]
        orientacion = exalumno[6]

        # Traer las materias pendientes cargadas por secretaría para este exalumno
        cursor.execute("""
            SELECT
                m.idMaterias,
                m.Materiascol,
                m.curso,
                m.orientacion,
                mp.estado AS estado_pendiente,
                im.idinscripcion_mesa,
                im.fecha_inscripcion,
                im.estado AS estado_inscripcion
            FROM materias_pendientes mp
            INNER JOIN materias m
                ON m.idMaterias = mp.materias_idmaterias
            LEFT JOIN inscripcion_mesa im
                ON im.materias_idMaterias = m.idMaterias
               AND im.ex_alumno_idex_alumno = mp.ex_alumno_idex_alumno
            WHERE mp.ex_alumno_idex_alumno = %s
              AND LOWER(TRIM(m.orientacion)) = LOWER(TRIM(%s))
            ORDER BY
                CAST(LEFT(m.curso, 1) AS UNSIGNED),
                m.curso,
                m.idMaterias
        """, (id_exalumno, orientacion))

        filas = cursor.fetchall()
        materias = []

        for fila in filas:
            fecha_ins = (
                fila[6].strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(fila[6], "strftime")
                else (str(fila[6]) if fila[6] else None)
            )
            materias.append({
                "idMaterias": fila[0],
                "nombre": fila[1],
                "curso": fila[2],
                "orientacion": fila[3],
                "estado_pendiente": fila[4],
                "idinscripcion_mesa": fila[5],
                "fecha_inscripcion": fecha_ins,
                "estado_inscripcion": fila[7]
            })

        return jsonify({
            "exalumno": {
                "usuario_id": exalumno[0],
                "idex_alumno": exalumno[4],
                "nombre": exalumno[1],
                "apellido": exalumno[2],
                "email": exalumno[3],
                "orientacion": exalumno[6]
            },
            "materias": materias
        }), 200

    except Exception as e:
        print("ERROR OBTENIENDO MESAS EXALUMNO:", str(e), flush=True)
        return jsonify({"error": "No se pudieron cargar las materias pendientes."}), 500

    finally:
        if cursor:
            cursor.close()


@app.route("/api/exalumno/inscribir-mesa", methods=["POST", "OPTIONS"])
def inscribir_mesa_exalumno():
    if request.method == "OPTIONS":
        return "", 200

    user_id = obtener_usuario_del_token()
    if not user_id:
        return jsonify({"error": "La sesión no es válida o venció."}), 401

    datos = request.get_json(silent=True) or {}
    materias_ids = datos.get("materias_ids")

    if not isinstance(materias_ids, list) or len(materias_ids) == 0:
        return jsonify({"error": "Seleccioná al menos una materia para inscribirte."}), 400

    try:
        materias_ids = list(set(int(x) for x in materias_ids))
    except (ValueError, TypeError):
        return jsonify({"error": "Hay identificadores de materias inválidos."}), 400

    cursor = None
    try:
        cursor = mysql.connection.cursor()

        exalumno = obtener_datos_exalumno(cursor, user_id)
        if not exalumno:
            return jsonify({"error": "No se encontró el perfil del exalumno."}), 404

        id_exalumno = exalumno[4]
        orientacion = exalumno[6]

        # Verificar que las materias elegidas estén en sus materias_pendientes y en su orientación
        cursor.execute("""
            SELECT mp.materias_idmaterias
            FROM materias_pendientes mp
            INNER JOIN materias m ON m.idMaterias = mp.materias_idmaterias
            WHERE mp.ex_alumno_idex_alumno = %s
              AND LOWER(TRIM(m.orientacion)) = LOWER(TRIM(%s))
        """, (id_exalumno, orientacion))

        ids_habilitados = {int(fila[0]) for fila in cursor.fetchall()}

        if not set(materias_ids).issubset(ids_habilitados):
            return jsonify({
                "error": "Alguna de las materias seleccionadas no figura como pendiente en tu orientación."
            }), 400

        # Verificar cuáles ya están inscriptas en inscripcion_mesa
        cursor.execute("""
            SELECT materias_idMaterias
            FROM inscripcion_mesa
            WHERE ex_alumno_idex_alumno = %s
        """, (id_exalumno,))

        ya_inscriptas = {int(fila[0]) for fila in cursor.fetchall()}
        nuevas = set(materias_ids) - ya_inscriptas

        for materia_id in nuevas:
            cursor.execute("""
                INSERT INTO inscripcion_mesa (
                    fecha_inscripcion,
                    estado,
                    materias_idMaterias,
                    ex_alumno_idex_alumno
                )
                VALUES (NOW(), 'Pendiente', %s, %s)
            """, (materia_id, id_exalumno))

        mysql.connection.commit()

        return jsonify({
            "mensaje": "Inscripción registrada correctamente.",
            "cantidad_nuevas": len(nuevas)
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        print("ERROR INSCRIBIENDO EN MESA:", str(e), flush=True)
        return jsonify({"error": "No se pudo registrar la inscripción."}), 500

    finally:
        if cursor:
            cursor.close()


@app.route("/api/exalumno/baja-mesa", methods=["POST", "OPTIONS"])
def baja_mesa_exalumno():
    if request.method == "OPTIONS":
        return "", 200

    user_id = obtener_usuario_del_token()
    if not user_id:
        return jsonify({"error": "La sesión no es válida o venció."}), 401

    datos = request.get_json(silent=True) or {}
    materias_ids = datos.get("materias_ids")

    if not isinstance(materias_ids, list) or len(materias_ids) == 0:
        return jsonify({"error": "No se indicaron materias para dar de baja."}), 400

    try:
        materias_ids = list(set(int(x) for x in materias_ids))
    except (ValueError, TypeError):
        return jsonify({"error": "Identificadores inválidos."}), 400

    cursor = None
    try:
        cursor = mysql.connection.cursor()

        exalumno = obtener_datos_exalumno(cursor, user_id)
        if not exalumno:
            return jsonify({"error": "No se encontró el perfil del exalumno."}), 404

        id_exalumno = exalumno[4]
        placeholders = ", ".join(["%s"] * len(materias_ids))

        cursor.execute(f"""
            DELETE FROM inscripcion_mesa
            WHERE ex_alumno_idex_alumno = %s
              AND materias_idMaterias IN ({placeholders})
        """, [id_exalumno] + materias_ids)

        mysql.connection.commit()

        return jsonify({"mensaje": "Inscripción dada de baja correctamente."}), 200

    except Exception as e:
        mysql.connection.rollback()
        print("ERROR DANDO DE BAJA MESA:", str(e), flush=True)
        return jsonify({"error": "No se pudo dar de baja la inscripción."}), 500

    finally:
        if cursor:
            cursor.close()


# ============================================================
# PANEL DE SECRETARÍA: INSCRIPTOS Y ARMADO DE MESAS
# ============================================================

@app.route("/api/secretaria/inscriptos", methods=["GET", "OPTIONS"])
def listar_inscriptos_mesa_secretaria():
    if request.method == "OPTIONS":
        return "", 200

    user_id, rol, error = autorizar_personal_administrativo()
    if error:
        return error

    cursor = None
    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                im.idinscripcion_mesa,
                im.fecha_inscripcion,
                im.estado,
                m.idMaterias,
                m.Materiascol AS materia_nombre,
                m.curso,
                m.orientacion,
                e.idex_alumno,
                u.id AS usuario_id,
                u.nombre,
                u.apellido,
                u.email
            FROM inscripcion_mesa im
            INNER JOIN materias m
                ON m.idMaterias = im.materias_idMaterias
            INNER JOIN ex_alumno e
                ON e.idex_alumno = im.ex_alumno_idex_alumno
            INNER JOIN perfil p
                ON p.idperfil = e.perfil_idperfil
            INNER JOIN usuario u
                ON u.perfil_idperfil = p.idperfil
            ORDER BY im.fecha_inscripcion DESC, m.curso, m.Materiascol
        """)

        filas = cursor.fetchall()
        inscriptos = []

        for fila in filas:
            fecha_ins = (
                fila[1].strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(fila[1], "strftime")
                else str(fila[1] or "")
            )
            inscriptos.append({
                "idinscripcion_mesa": fila[0],
                "fecha_inscripcion": fecha_ins,
                "estado": fila[2],
                "idMaterias": fila[3],
                "materia": fila[4],
                "curso": fila[5],
                "orientacion": fila[6],
                "idex_alumno": fila[7],
                "usuario_id": fila[8],
                "alumno": f"{fila[9] or ''} {fila[10] or ''}".strip(),
                "email": fila[11]
            })

        return jsonify({"inscriptos": inscriptos}), 200

    except Exception as e:
        print("ERROR LISTANDO INSCRIPTOS SECRETARIA:", str(e), flush=True)
        return jsonify({"error": "No se pudieron consultar los exalumnos inscriptos."}), 500

    finally:
        if cursor:
            cursor.close()


@app.route("/api/secretaria/armar-mesa", methods=["POST", "OPTIONS"])
def armar_mesa_secretaria():
    """
    1. Busca la materia y el curso en MySQL.
    2. Registra la relación en la tabla materias_cursos (cursos_idCursos, materias_idMaterias).
    3. Confirma en inscripcion_mesa a los exalumnos anotados en esa materia y devuelve el detalle.
    """
    if request.method == "OPTIONS":
        return "", 200

    user_id, rol, error = autorizar_personal_administrativo()
    if error:
        return error

    datos = request.get_json(silent=True) or {}
    curso_codigo = str(datos.get("curso") or "").strip()
    materia_nombre = str(datos.get("materia") or "").strip()
    orientacion = str(datos.get("modalidad") or "").strip()

    if not curso_codigo or not materia_nombre:
        return jsonify({"error": "Faltan datos de curso o materia."}), 400

    cursor = None
    try:
        cursor = mysql.connection.cursor()

        # 1. Buscar idMaterias en la tabla materias
        cursor.execute("""
            SELECT idMaterias, Materiascol, curso
            FROM materias
            WHERE LOWER(TRIM(Materiascol)) = LOWER(TRIM(%s))
              AND LOWER(TRIM(curso)) = LOWER(TRIM(%s))
            LIMIT 1
        """, (materia_nombre, curso_codigo))

        fila_materia = cursor.fetchone()
        if not fila_materia:
            return jsonify({
                "error": f"No se encontró la materia '{materia_nombre}' ({curso_codigo}) en la base de datos."
            }), 404

        id_materia = int(fila_materia[0])
        nombre_materia_db = fila_materia[1]

        # 2. Buscar idCursos en la tabla cursos (si existe el código de curso, ej: '1A', '6B')
        cursor.execute("""
            SELECT idCursos
            FROM cursos
            WHERE LOWER(TRIM(curso)) = LOWER(TRIM(%s))
               OR LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
            LIMIT 1
        """, (curso_codigo, curso_codigo))

        fila_curso = cursor.fetchone()

        # Si la tabla cursos usa otra columna o no tiene esa fila, usamos el número del curso como respaldo
        if fila_curso:
            id_curso = int(fila_curso[0])
        else:
            cursor.execute("SELECT idCursos FROM cursos LIMIT 1")
            primer_curso = cursor.fetchone()
            id_curso = int(primer_curso[0]) if primer_curso else int("".join(filter(str.isdigit, curso_codigo)) or 1)

        # 3. Insertar en materias_cursos si aún no existe esa combinación
        cursor.execute("""
            SELECT idmaterias_cursos
            FROM materias_cursos
            WHERE cursos_idCursos = %s
              AND materias_idMaterias = %s
            LIMIT 1
        """, (id_curso, id_materia))

        existente = cursor.fetchone()
        if existente:
            id_materias_cursos = existente[0]
        else:
            cursor.execute("""
                INSERT INTO materias_cursos (cursos_idCursos, materias_idMaterias)
                VALUES (%s, %s)
            """, (id_curso, id_materia))
            id_materias_cursos = cursor.lastrowid

        # 4. Obtener los exalumnos inscriptos en esa materia y pasarlos a 'Confirmado'
        cursor.execute("""
            SELECT
                im.idinscripcion_mesa,
                e.idex_alumno,
                u.nombre,
                u.apellido,
                u.email
            FROM inscripcion_mesa im
            INNER JOIN ex_alumno e ON e.idex_alumno = im.ex_alumno_idex_alumno
            INNER JOIN perfil p ON p.idperfil = e.perfil_idperfil
            INNER JOIN usuario u ON u.perfil_idperfil = p.idperfil
            WHERE im.materias_idMaterias = %s
        """, (id_materia,))

        inscriptos_materia = cursor.fetchall()

        cursor.execute("""
            UPDATE inscripcion_mesa
            SET estado = 'Confirmado'
            WHERE materias_idMaterias = %s
        """, (id_materia,))

        mysql.connection.commit()

        exalumnos_mesa = [
            {
                "idinscripcion_mesa": row[0],
                "idex_alumno": row[1],
                "nombre": f"{row[2] or ''} {row[3] or ''}".strip(),
                "email": row[4]
            }
            for row in inscriptos_materia
        ]

        return jsonify({
            "mensaje": "Mesa armada y registrada en materias_cursos correctamente.",
            "idmaterias_cursos": id_materias_cursos,
            "cursos_idCursos": id_curso,
            "materias_idMaterias": id_materia,
            "materia_nombre": nombre_materia_db,
            "exalumnos": exalumnos_mesa
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        print("ERROR ARMANDO MESA SECRETARIA:", str(e), flush=True)
        return jsonify({"error": f"No se pudo registrar la mesa en Railway: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)