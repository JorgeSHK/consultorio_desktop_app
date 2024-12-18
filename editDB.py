import sqlite3

conn = sqlite3.connect('consultorioDB.db')

cursor = conn.cursor()

cursor.execute("SELECT * FROM cobros")

#cursor.execute("SELECT * FROM pacientes")

#cursor.execute("SELECT * FROM productos")

#cursor.execute("SELECT * FROM citas")

#cursor.execute('SELECT paciente_id FROM citas WHERE id=8')

#cursor.execute("SELECT * FROM cobros WHERE paciente_id NOT IN (SELECT id FROM pacientes);")

#cursor.execute("SELECT * FROM cobros WHERE paciente_id IN (SELECT id FROM pacientes);")

resultados = cursor.fetchall()

for resultado in resultados:
    print(resultado)

conn.close