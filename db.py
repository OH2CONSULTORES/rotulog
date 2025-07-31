import sqlite3
import datetime
import pandas as pd
import os
from io import BytesIO

# Ruta absoluta de la base de datos
DB_NAME = os.path.join(os.getcwd(), "rotulos.db")

# ===========================
# CONEXIÓN A LA BASE DE DATOS
# ===========================
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

# ===========================
# INICIALIZAR BASE DE DATOS
# ===========================
def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Crear tabla de rótulos
    c.execute("""
        CREATE TABLE IF NOT EXISTS rotulos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            producto TEXT,
            cantidad INTEGER,
            num_paquete INTEGER,
            codigo_lote TEXT,
            orden_compra TEXT,
            color_fondo TEXT,
            fecha_creacion TEXT
        )
    """)

    # Crear tabla de logos
    c.execute("""
        CREATE TABLE IF NOT EXISTS logos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT UNIQUE, -- 'izquierdo' o 'derecho'
            imagen BLOB
        )
    """)
    conn.commit()
    conn.close()

# ===========================
# FUNCIONES DE RÓTULOS
# ===========================
def insertar_rotulo(cliente, producto, cantidad, num_paquete, codigo_lote, orden_compra, color_fondo):
    conn = get_connection()
    c = conn.cursor()

    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO rotulos (
            cliente, producto, cantidad, num_paquete,
            codigo_lote, orden_compra, color_fondo, fecha_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente, producto, cantidad, num_paquete,
        codigo_lote, orden_compra, color_fondo, fecha_actual
    ))

    conn.commit()
    conn.close()

def obtener_historial():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM rotulos ORDER BY fecha_creacion DESC", conn)
    conn.close()
    return df

def eliminar_rotulo(rotulo_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM rotulos WHERE id = ?", (rotulo_id,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

def exportar_excel():
    df = obtener_historial()
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return output

# ===========================
# FUNCIONES DE LOGOS
# ===========================
def insertar_logo(tipo, imagen_bytes):
    conn = get_connection()
    c = conn.cursor()
    c.execute("REPLACE INTO logos (tipo, imagen) VALUES (?, ?)", (tipo, imagen_bytes))
    conn.commit()
    conn.close()

def obtener_logo(tipo):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT imagen FROM logos WHERE tipo = ?", (tipo,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def logo_existe(tipo):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT 1 FROM logos WHERE tipo = ?", (tipo,))
    exists = c.fetchone() is not None
    conn.close()
    return exists
