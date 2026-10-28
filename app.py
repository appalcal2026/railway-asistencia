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
        print("DATOS RECIBIDOS:", datos)  # ← mira esto en la consola de Flask

        fecha = datos.get("fecha")
        legajo_alumno = datos.get("id_alumno")
        tipo_asistencia = datos.get("opcionSeleccionada")

        print(f"Legajo recibido: '{legajo_alumno}' (tipo: {type(legajo_alumno)})")

        if not all([fecha, legajo_alumno, tipo_asistencia]):
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        cursor = mysql.connection.cursor()

        # Probamos de varias formas
        legajo_str = str(legajo_alumno).strip()
        
        # 1. Como string
        cursor.execute("SELECT idAlumno FROM alumno WHERE legajo = %s", (legajo_str,))
        resultado = cursor.fetchone()
        print("Resultado como string:", resultado)

        # 2. Como número (por si la columna es INT)
        if resultado is None:
            try:
                legajo_num = int(legajo_str)
                cursor.execute("SELECT idAlumno FROM alumno WHERE legajo = %s", (legajo_num,))
                resultado = cursor.fetchone()
                print("Resultado como int:", resultado)
            except ValueError:
                print("No se pudo convertir a int")

        if not resultado:
            # Mostrar qué legajos hay (para comparar)
            cursor.execute("SELECT legajo FROM alumno LIMIT 10")
            existentes = cursor.fetchall()
            print("Algunos legajos existentes:", existentes)
            
            cursor.close()
            return jsonify({
                "error": "No se encontró el alumno",
                "legajo_recibido": legajo_alumno,
                "legajo_como_string": legajo_str,
                "ejemplos_en_bd": [str(r[0]) for r in existentes]
            }), 404

        id_alumno = resultado[0]
        print("idAlumno encontrado:", id_alumno)

        sql = """
            INSERT INTO asistencia (fecha, Alumno_idAlumno, tipo_asistencia_idtipo_asistencia)
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (fecha, id_alumno, tipo_asistencia))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"resultado": "Asistencia registrada correctamente"}), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Error en el registro de asistencia",
            "detalle": str(e)
        }), 500

    '''
    try:
        datos = request.get_json(force=True)
        fecha = datos["fecha"]
        #hora = datos["hora"]
        #id_preceptor = datos["id_preceptor"]
        legajo_alumno = datos["id_alumno"]
        tipo_asistencia = datos["opcionSeleccionada"]

        cursor = mysql.connection.cursor()
        sql0= "Select idAlumno from alumno where legajo = %s"
        cursor.execute(sql0, (legajo_alumno,))
        resultado = cursor.fetchone()
        id_alumno = resultado[0]


        sql = "INSERT INTO asistencia(fecha, Alumno_idAlumno, tipo_asistencia_idtipo_asistencia) VALUES (%s, %s, %s)"
        cursor.execute(sql, (fecha, id_alumno, tipo_asistencia))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"resultado": "Asistencia registrada correctamente"}), 201
    except Exception as e:
        return jsonify({"error": f"Error en el registro de asistencia: {str(e)}"}), 500
    '''

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
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)