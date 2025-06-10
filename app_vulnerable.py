from flask import Flask, request, jsonify
import sqlite3
import jwt
import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['DEBUG'] = True
SECRET_KEY = 'A9d$3f8#GjLqPwzVx7!KmRtYsB2eH4Uw'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token requerido'}), 401

        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401

        return f(*args, **kwargs)
    return decorated


def init_db():
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                birthdate TEXT,
                status TEXT DEFAULT 'active',
                secret_question TEXT,
                secret_answer TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO users (username, password, email, birthdate, secret_question, secret_answer) 
            SELECT 'admin', '1234', 'jaco@gmail.com', '2002-07-02', '¿Color favorito?', 'azul'
            WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
        """)
        cursor.execute("""
            INSERT INTO users (username, password)
            SELECT 'user', 'pass'
            WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'user')
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            fecha_creacion TEXT,
            precio_llegada REAL,
            precio_menudeo REAL,
            precio_mayoreo REAL,
            estado TEXT DEFAULT 'activo'
            )
        """)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    fields = ['username', 'password', 'email',
              'birthdate', 'secret_question', 'secret_answer']
    if not all(field in data for field in fields):
        return jsonify({"error": "Faltan campos"}), 400

    if len(data['username']) < 3 or len(data['password']) < 6:
        return jsonify({"error": "Usuario o contraseña demasiado cortos"}), 400

    hashed_password = generate_password_hash(data['password'])

    try:
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password, email, birthdate, secret_question, secret_answer)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data['username'], hashed_password, data['email'],
                data['birthdate'], data['secret_question'], data['secret_answer']
            ))
            conn.commit()
        return jsonify({"message": "Usuario registrado exitosamente"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "El nombre de usuario ya existe"}), 409


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

    if user and check_password_hash(user[2], password):
        token = jwt.encode({
            'user_id': user[0],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        }, SECRET_KEY, algorithm='HS256')
        return jsonify({"token": token})

    return jsonify({"message": "Credenciales inválidas"}), 401


@app.route('/user/<int:user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    data = request.get_json()
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET username = ?, email = ?, birthdate = ?, secret_question = ?, secret_answer = ?
            WHERE id = ?
        """, (
            data.get('username'), data.get('email'), data.get('birthdate'),
            data.get('secret_question'), data.get('secret_answer'), user_id
        ))
        conn.commit()
    return jsonify({"message": "Usuario actualizado"})


@app.route('/user/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET status = 'inactive' WHERE id = ?", (user_id,))
        conn.commit()
    return jsonify({"message": "Usuario desactivado (borrado lógico)"})


@app.route('/user/<int:user_id>', methods=['GET'])
@token_required
def get_user_by_id(user_id):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return jsonify({
                "id": user[0], "username": user[1],
                "email": user[3], "birthdate": user[4], "status": user[5],
                "secret_question": user[6], "secret_answer": user[7]
            })
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404


@app.route('/user')
@token_required
def get_user():
    username = request.args.get('username') or ''
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, birthdate, status, secret_question, secret_answer FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
    return jsonify({"user": user})


@app.route('/admin/data')
@token_required
def admin_data():
    return jsonify({"data": "Datos confidenciales. Acceso autenticado"})


@app.route('/productos', methods=['POST'])
@token_required
def create_producto():
    data = request.get_json()
    required_fields = ['nombre', 'descripcion', 'fecha_creacion',
                       'precio_llegada', 'precio_menudeo', 'precio_mayoreo']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Faltan campos"}), 400

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO productos (nombre, descripcion, fecha_creacion, precio_llegada, precio_menudeo, precio_mayoreo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data['nombre'], data['descripcion'], data['fecha_creacion'],
            data['precio_llegada'], data['precio_menudeo'], data['precio_mayoreo']
        ))
        conn.commit()
    return jsonify({"message": "Producto creado exitosamente"}), 201


@app.route('/productos', methods=['GET'])
@token_required
def get_productos():
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE estado = 'activo'")
        productos = cursor.fetchall()
        productos_list = [{
            "id": p[0], "nombre": p[1], "descripcion": p[2],
            "fecha_creacion": p[3], "precio_llegada": p[4],
            "precio_menudeo": p[5], "precio_mayoreo": p[6]
        } for p in productos]
    return jsonify({"productos": productos_list})


@app.route('/productos/<int:producto_id>', methods=['GET'])
@token_required
def get_producto_by_id(producto_id):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM productos WHERE id = ? AND estado = 'activo'
        """, (producto_id,))
        p = cursor.fetchone()
        if p:
            return jsonify({
                "id": p[0], "nombre": p[1], "descripcion": p[2],
                "fecha_creacion": p[3], "precio_llegada": p[4],
                "precio_menudeo": p[5], "precio_mayoreo": p[6]
            })
        else:
            return jsonify({"error": "Producto no encontrado"}), 404


@app.route('/productos/<int:producto_id>', methods=['PUT'])
@token_required
def update_producto(producto_id):
    data = request.get_json()
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE productos
            SET nombre = ?, descripcion = ?, fecha_creacion = ?, precio_llegada = ?, precio_menudeo = ?, precio_mayoreo = ?
            WHERE id = ?
        """, (
            data.get('nombre'), data.get(
                'descripcion'), data.get('fecha_creacion'),
            data.get('precio_llegada'), data.get(
                'precio_menudeo'), data.get('precio_mayoreo'), producto_id
        ))
        conn.commit()
    return jsonify({"message": "Producto actualizado"})


@app.route('/productos/<int:producto_id>', methods=['DELETE'])
@token_required
def delete_producto(producto_id):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE productos SET estado = 'inactivo' WHERE id = ?
        """, (producto_id,))
        conn.commit()
    return jsonify({"message": "Producto desactivado (borrado lógico)"}), 200


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
