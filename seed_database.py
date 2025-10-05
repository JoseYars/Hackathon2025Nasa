import os
import json
import psycopg2
from dotenv import load_dotenv

def seed_data():
    """
    Lee los datos de data.json y los inserta en la tabla 'articles' de la base de datos.
    """
    # Carga la configuración de la base de datos desde el archivo .env
    load_dotenv()
    
    # Carga los datos de los artículos desde el archivo JSON
    with open('data.json', 'r', encoding='utf-8') as f:
        articles_data = json.load(f)
        
    conn = None
    try:
        # Conecta a la base de datos PostgreSQL
        print("Conectando a la base de datos PostgreSQL...")
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()

        # Prepara el comando SQL para insertar un artículo
        # Las columnas de la BD están en inglés, los datos en el JSON en español.
        # Aquí hacemos el "mapeo" correcto.
        insert_query = """
            INSERT INTO articles (title, author, pub_year, abstract, key_words, related_articles, summary_sentence)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        
        # Itera sobre cada artículo en el JSON y lo inserta en la base de datos
        for article in articles_data:
            print(f"Insertando artículo: {article['título']}")
            
            # Crea una tupla de datos en el orden correcto para la consulta SQL
            article_tuple = (
                article['título'],
                article['autor'],
                article['año de publicación'],
                article['abstract'],
                article['keywords'],  # psycopg2 convierte listas de Python a arrays de PostgreSQL
                article['artículos relacionados —grafo'],
                article['Frase de resumen']
            )
            
            # Ejecuta la inserción
            cur.execute(insert_query, article_tuple)

        # Confirma todos los cambios en la base de datos
        conn.commit()
        print(f"\n✅ ¡Éxito! Se han insertado {len(articles_data)} artículos en la base de datos.")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"❌ Error al conectar o insertar datos: {error}")
    
    finally:
        # Cierra la conexión
        if conn is not None:
            conn.close()
            print("Conexión a la base de datos cerrada.")

# Llama a la función principal para que el script se ejecute
if __name__ == '__main__':
    seed_data()
