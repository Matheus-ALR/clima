import psycopg2
import os
from datetime import datetime
import traceback

def get_connection():
    try:
        # Prioriza conexão de produção (Neon/Render) se PGHOST estiver presente
        if os.getenv("PGHOST"):
            return psycopg2.connect(
                host=os.getenv("PGHOST"),
                database=os.getenv("PGDATABASE"),
                user=os.getenv("PGUSER"),
                password=os.getenv("PGPASSWORD"),
                sslmode=os.getenv("PGSSLMODE", "require")
            )

        # Caso contrário, tenta conexão local
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
    except Exception:
        print("❌ ERRO AO CONECTAR NO BANCO:")
        traceback.print_exc()
        return None

def buscar_clima_no_banco(cidade):
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        hoje = datetime.now().strftime('%d/%m/%Y')
        cursor.execute("""
            SELECT cidade, data, umidade, vento, precipitacao, temp_min, temp_max
            FROM clima
            WHERE LOWER(cidade) = %s AND data = %s
        """, (cidade.lower(), hoje))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return {
                'cidade': result[0], 'data': result[1], 'umidade': result[2],
                'vento': result[3], 'precipitacao': result[4],
                'temperatura_min': result[5], 'temperatura_max': result[6],
                'previsao': []
            }
        return None
    except Exception:
        traceback.print_exc()
        return None

def salvar_clima_no_banco(dados):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clima (cidade, data, umidade, vento, precipitacao, temp_min, temp_max)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (dados['cidade'], dados['data'], dados['umidade'], dados['vento'],
              dados['precipitacao'], dados['temperatura_min'], dados['temperatura_max']))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        traceback.print_exc()