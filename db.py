import sqlite3
import datetime
import pandas as pd

DB_NAME = "rotulos.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
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

def insertar_rotulo(cliente, producto, cantidad, num_paquete, codigo_lote, orden_compra, color_fondo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO rotulos (
            cliente, producto, cantidad, num_paquete,
            codigo_lote, orden_compra, color_fondo, fecha_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente, producto, cantidad, num_paquete,
        codigo_lote, orden_compra, color_fondo,
        datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def obtener_historial():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM rotulos ORDER BY fecha_creacion DESC", conn)
    conn.close()
    return df

def eliminar_rotulo(rotulo_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM rotulos WHERE id = ?", (rotulo_id,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

def exportar_excel():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM rotulos ORDER BY fecha_creacion DESC", conn)
    conn.close()
    return df.to_excel(index=False, engine='openpyxl')

def insertar_logo(tipo, imagen_bytes):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("REPLACE INTO logos (tipo, imagen) VALUES (?, ?)", (tipo, imagen_bytes))
    conn.commit()
    conn.close()

def obtener_logo(tipo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT imagen FROM logos WHERE tipo = ?", (tipo,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def logo_existe(tipo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM logos WHERE tipo = ?", (tipo,))
    exists = c.fetchone() is not None
    conn.close()
    return exists