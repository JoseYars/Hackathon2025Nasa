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
    # Usamos un modelo actualizado y estable
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
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


# --- ENDPOINTS GENERALES DE LA API ---

@app.route("/")
def index():
    return jsonify({"status": "API funcionando correctamente"})

# Endpoint 1: Obtener un artículo COMPLETO por su ID
@app.route("/api/articles/<int:article_id>", methods=['GET'])
def get_article_by_id(article_id):
    """Obtiene todos los datos de un artículo específico."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cur = conn.cursor()
        query = """
            SELECT id, key_words, title, author, pub_year, abstract, related_articles, summary_sentence
            FROM articles
            WHERE id = %s;
        """
        cur.execute(query, (article_id,))
        article_data = cur.fetchone()
        
        if article_data:
            column_names = [desc[0] for desc in cur.description]
            article_dict = dict(zip(column_names, article_data))
            cur.close()
            return jsonify(article_dict)
        else:
            cur.close()
            return jsonify({"error": "Artículo no encontrado"}), 404
            
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error en el servidor: {e}"}), 500
    finally:
        if conn:
            conn.close()

# Endpoint 2: Realizar una búsqueda y consultar a Gemini 💎
@app.route("/api/search", methods=['POST'])
def search_with_gemini():
    """Recibe una búsqueda, crea un prompt para Gemini y devuelve su respuesta."""
    if not gemini_model:
        return jsonify({"error": "El modelo de Gemini no está configurado correctamente"}), 500
        
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "La clave 'query' es requerida en el cuerpo de la petición"}), 400
        
    user_query = data['query']
    prompt = f"""
    Eres un asistente experto en investigación académica.
    Basado en la siguiente consulta de un usuario: "{user_query}", genera un resumen conciso y relevante de 2 o 3 oraciones
    que capture la idea principal de la búsqueda. Este resumen se mostrará en una interfaz de usuario.
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return jsonify({
            "user_query": user_query,
            "gemini_summary": response.text
        })
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error al contactar a Gemini: {e}"}), 503


# --- FUNCIÓN AUXILIAR PARA OBTENER CAMPOS ESPECÍFICOS ---

def get_field_for_article(article_id, field_name):
    """Función genérica para obtener un solo campo de un artículo."""
    # Lista blanca de campos permitidos para evitar inyección SQL
    allowed_fields = ["title", "author", "pub_year", "abstract", "key_words", "related_articles", "summary_sentence"]
    if field_name not in allowed_fields:
        return jsonify({"error": "Campo no válido"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
    
    try:
        cur = conn.cursor()
        # Construimos la consulta de forma segura
        query = f"SELECT {field_name} FROM articles WHERE id = %s;"
        cur.execute(query, (article_id,))
        data = cur.fetchone()
        cur.close()

        if data:
            # Devolvemos el dato en un JSON con el nombre del campo como clave
            return jsonify({field_name: data[0]})
        else:
            return jsonify({"error": "Artículo no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error en el servidor: {e}"}), 500
    finally:
        if conn:
            conn.close()

# --- ENDPOINTS ESPECÍFICOS POR CAMPO ---

@app.route("/api/articles/<int:article_id>/title", methods=['GET'])
def get_article_title(article_id):
    return get_field_for_article(article_id, "title")

@app.route("/api/articles/<int:article_id>/author", methods=['GET'])
def get_article_author(article_id):
    return get_field_for_article(article_id, "author")

@app.route("/api/articles/<int:article_id>/year", methods=['GET'])
def get_article_year(article_id):
    return get_field_for_article(article_id, "pub_year")

@app.route("/api/articles/<int:article_id>/abstract", methods=['GET'])
def get_article_abstract(article_id):
    return get_field_for_article(article_id, "abstract")

@app.route("/api/articles/<int:article_id>/keywords", methods=['GET'])
def get_article_keywords(article_id):
    return get_field_for_article(article_id, "key_words")

@app.route("/api/articles/<int:article_id>/related", methods=['GET'])
def get_related_articles(article_id):
    return get_field_for_article(article_id, "related_articles")

@app.route("/api/articles/<int:article_id>/summary", methods=['GET'])
def get_article_summary(article_id):
    return get_field_for_article(article_id, "summary_sentence")

@app.route("/api/articles/<int:article_id>/related", methods=['GET'])
def get_related_articles(article_id):
    return get_field_for_article(article_id, "related_articles")

# --- INICIAR LA APLICACIÓN ---

if __name__ == '__main__':
    app.run(debug=True, port=5000)