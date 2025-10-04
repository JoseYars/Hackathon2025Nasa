# app.py

import os
import psycopg2
import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# --- CONFIGURACIÓN INICIAL ---

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configurar la aplicación Flask y habilitar CORS
app = Flask(__name__)
CORS(app)

# Configurar la API de Gemini con la clave del .env
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gemini_model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    print(f"Error configurando Gemini: {e}")
    gemini_model = None


# --- FUNCIÓN DE CONEXIÓN A LA BASE DE DATOS --- 🐘

def get_db_connection():
    """Crea y retorna una conexión a la base de datos PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None


# --- ENDPOINTS DE LA API ---

@app.route("/")
def index():
    return jsonify({"status": "API funcionando correctamente"})

# Endpoint 1: Obtener un artículo por su ID
@app.route("/api/articles/<int:article_id>", methods=['GET'])
def get_article_by_id(article_id):
    """Obtiene los datos de un artículo específico desde la base de datos."""
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        # Usamos un cursor para ejecutar comandos SQL
        cur = conn.cursor()
        
        # Consulta SQL para seleccionar los campos que necesitas
        # Usar %s previene la inyección SQL, es una práctica de seguridad crucial
        query = """
            SELECT key_words, title, author, pub_year, abstract, related_articles, summary_sentence
            FROM articles
            WHERE id = %s;
        """
        cur.execute(query, (article_id,))
        
        # Obtenemos el resultado
        article_data = cur.fetchone()
        
        cur.close()
        
        if article_data:
            # Creamos un diccionario con los nombres de las columnas para una respuesta JSON limpia
            column_names = [desc[0] for desc in cur.description]
            article_dict = dict(zip(column_names, article_data))
            return jsonify(article_dict)
        else:
            # Si fetchone() no devuelve nada, el artículo no fue encontrado
            return jsonify({"error": "Artículo no encontrado"}), 404
            
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error en el servidor: {e}"}), 500
    finally:
        # Siempre cerramos la conexión
        if conn:
            conn.close()


# Endpoint 2: Realizar una búsqueda y consultar a Gemini 💎
@app.route("/api/search", methods=['POST'])
def search_with_gemini():
    """Recibe una búsqueda, crea un prompt para Gemini y devuelve su respuesta."""
    
    if not gemini_model:
        return jsonify({"error": "El modelo de Gemini no está configurado correctamente"}), 500
        
    # Obtenemos los datos enviados en el cuerpo de la petición POST (deben estar en formato JSON)
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"error": "La clave 'query' es requerida en el cuerpo de la petición"}), 400
        
    user_query = data['query']
    
    # --- Creación del Prompt para Gemini ---
    # Este es el corazón de la interacción. Puedes hacerlo tan complejo como necesites.
    prompt = f"""
    Eres un asistente experto en investigación académica.
    Basado en la siguiente consulta de un usuario: "{user_query}", genera un resumen conciso y relevante de 2 o 3 oraciones
    que capture la idea principal de la búsqueda. Este resumen se mostrará en una interfaz de usuario.
    """
    
    try:
        # Enviamos el prompt al modelo
        response = gemini_model.generate_content(prompt)
        
        # Devolvemos la respuesta de Gemini en un objeto JSON
        return jsonify({
            "user_query": user_query,
            "gemini_summary": response.text
        })
        
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error al contactar a Gemini: {e}"}), 503 # Service Unavailable


# --- INICIAR LA APLICACIÓN ---

if __name__ == '__main__':
    # debug=True es para desarrollo. En producción, usa un servidor WSGI como Gunicorn.
    app.run(debug=True, port=5000)