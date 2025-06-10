# Proyecto Flask con SQLite y JWT

Este proyecto es una API RESTful construida con Flask. Utiliza SQLite como base de datos y JWT para la autenticación.

## Requisitos

- Python 3.10 o superior (verifica con `python --version`)
- Git (opcional, para clonar el repositorio)

## Versión de Python

Este proyecto ha sido probado con:

Python 3.10.11

## Dependencias

Las dependencias están listadas en el archivo [`requirements.txt`](./requirements.txt).

## Pasos para ejecutar el proyecto en Windows

1. Clona el repositorio (opcional)

git clone https://github.com/Mi-Owen/Evaluacion-1.git
cd nombre-del-repo

2. Crea un entorno virtual

python -m venv venv

Puedes reemplazar venv por el nombre que prefieras.

3. Activa el entorno virtual

venv\Scripts\activate

4. Instala las dependencias

pip install -r requirements.txt

5. Ejecuta la aplicación

python app_insegura.py

Reemplaza app_vulnerable.py por el nombre de tu archivo principal si es diferente.

# Endpoints

Una vez corriendo, la API puede ser probada con herramientas como Postman o curl.

## Notas

Asegúrate de que database.db y las tablas necesarias están creadas antes de insertar datos.

Si usas JWT, primero haz login y luego usa el token en los endpoints protegidos.

### Estructura del proyecto

.
├── app_vulnerable.py
├── database.db
├── requirements.txt
└── README.md
