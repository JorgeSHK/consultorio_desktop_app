import customtkinter as ctk
import sqlite3
from tkinter import ttk
from tkcalendar import DateEntry

class ResumenCobros:
    def __init__(self, parent):
        self.parent = parent
        self.create_widgets()
        self.conectar_db()

    def conectar_db(self):
        self.conn = sqlite3.connect('consultorioDB.db')
        self.cursor = self.conn.cursor()

    def create_widgets(self):
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.pack(fill='both', expand=True, padx=20, pady=20)

        self.label = ctk.CTkLabel(self.frame, text="Selecciona una fecha:")
        self.label.pack(padx=10, pady=10)

        self.date_entry = DateEntry(self.frame, width=12, background='darkblue',
                                    foreground='white', borderwidth=2)
        self.date_entry.pack(padx=10, pady=10)

        self.button = ctk.CTkButton(self.frame, text="Mostrar Cobros", command=self.filtrar_datos)
        self.button.pack(padx=10, pady=10)

        self.tree = ttk.Treeview(self.frame, columns=('paciente_id', 'paciente_nombre', 'fecha', 'descripcion', 'cantidad', 'total'), show='headings')
        self.tree.heading('paciente_id', text='ID Paciente')
        self.tree.heading('paciente_nombre', text='Nombre del Paciente')
        self.tree.heading('fecha', text='Fecha')
        self.tree.heading('descripcion', text='Descripción')
        self.tree.heading('cantidad', text='Cantidad')
        self.tree.heading('total', text='Total')
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

    def filtrar_datos(self):
        fecha_seleccionada = self.date_entry.get_date().strftime('%Y-%m-%d')
        query = """
            SELECT c.paciente_id, p.nombre, c.fecha, c.descripcion, c.cantidad, c.total
            FROM cobros c
            JOIN pacientes p ON c.paciente_id = p.id
            WHERE c.fecha = ?
            ORDER BY c.paciente_id
        """
        self.cursor.execute(query, (fecha_seleccionada,))
        rows = self.cursor.fetchall()

        for row in self.tree.get_children():
            self.tree.delete(row)

        last_paciente_id = None
        for i, row in enumerate(rows):
            tags = ()
            if row[0] != last_paciente_id:
                tags = ('alternate',) if i % 2 == 1 else ()
            self.tree.insert("", "end", values=row, tags=tags)
            last_paciente_id = row[0]

        self.tree.tag_configure('alternate', background='#f0f0f0')

    def __del__(self):
        self.conn.close()
