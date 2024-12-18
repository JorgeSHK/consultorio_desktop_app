import sqlite3

def conectar_db():
    conn = sqlite3.connect('consultorioDB.db')
    cursor = conn.cursor()
    
    # Crear o verificar tablas existentes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            es_distribuidor BOOLEAN
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            confirmado TEXT NOT NULL,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cobros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            marca TEXT NOT NULL,
            precio REAL NOT NULL,
            cantidad INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiales_cirugia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            cantidad INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plantillas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            numero_calzado TEXT NOT NULL,
            precio REAL NOT NULL,
            cantidad_pagada REAL DEFAULT 0,
            fecha_pedido DATE NOT NULL,
            fecha_entrega DATE,
            estado TEXT NOT NULL,
            productos TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    ''')

    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Verificar y añadir columnas faltantes en la tabla plantillas
    columnas_esperadas = ['fecha_pedido', 'fecha_entrega', 'estado']
    for columna in columnas_esperadas:
        cursor.execute(f"PRAGMA table_info(plantillas)")
        columnas_existentes = [column[1] for column in cursor.fetchall()]
        if columna not in columnas_existentes:
            tipo = 'DATE' if columna.startswith('fecha') else 'TEXT'
            cursor.execute(f"ALTER TABLE plantillas ADD COLUMN {columna} {tipo}")
            print(f"Columna '{columna}' añadida a la tabla plantillas")

    # Verificar y añadir la columna precio_distribuidor en la tabla productos
    cursor.execute("PRAGMA table_info(productos)")
    columnas_productos = [col[1] for col in cursor.fetchall()]
    if 'precio_distribuidor' not in columnas_productos:
        cursor.execute('ALTER TABLE productos ADD COLUMN precio_distribuidor REAL')
        print("Columna 'precio_distribuidor' añadida a la tabla productos")

    conn.commit()
    return conn   

def cerrar_db(conn):
    if conn:
        conn.close()

def imprimir_estructura_plantillas(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(plantillas)")
    columns = cursor.fetchall()
    print("Estructura actual de la tabla plantillas:")
    for column in columns:
        print(column)