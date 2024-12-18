import customtkinter as ctk
import sqlite3
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

class ResumenCobros:
    def __init__(self, parent,conn):
        self.parent = parent
        self.conn = conn
        self.conectar_db()
        self.create_widgets()

    def conectar_db(self):
        self.conn = sqlite3.connect('consultorioDB.db')
        self.cursor = self.conn.cursor()

    def create_widgets(self):
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Panel de filtros
        self.crear_panel_filtros()

        # Panel de resumen
        self.crear_panel_resumen()

        # Notebook para diferentes vistas
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.crear_tab_cobros()
        self.crear_tab_productos()
        self.crear_tab_grafico()

        # Frame para botones
        button_frame = ctk.CTkFrame(self.frame)
        button_frame.pack(fill='x', padx=10, pady=10)

        # Botón para exportar datos
        self.button_exportar = ctk.CTkButton(button_frame, text="Exportar Datos", command=self.exportar_csv)
        self.button_exportar.pack(side='left', padx=10)

        # Botón de ayuda
        self.button_ayuda = ctk.CTkButton(button_frame, text="Ayuda", command=self.mostrar_ayuda)
        self.button_ayuda.pack(side='right', padx=10)

    def crear_panel_filtros(self):
        filter_frame = ctk.CTkFrame(self.frame)
        filter_frame.pack(fill='x', padx=10, pady=10)

        ctk.CTkLabel(filter_frame, text="Período:").pack(side='left', padx=5)
        self.periodo_var = ctk.StringVar(value="Hoy")  # Valor default ahora es "Hoy"
        periodo_menu = ctk.CTkOptionMenu(
            filter_frame, 
            values=["Hoy", "Este mes", "Último mes", "Este año", "Personalizado"], 
            variable=self.periodo_var, 
            command=self.actualizar_fechas
        )
        periodo_menu.pack(side='left', padx=5)

        self.date_frame = ctk.CTkFrame(filter_frame)
        self.date_frame.pack(side='left', padx=5)

        ctk.CTkLabel(self.date_frame, text="Desde:").pack(side='left', padx=5)
        self.date_entry_inicio = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.date_entry_inicio.pack(side='left', padx=5)

        ctk.CTkLabel(self.date_frame, text="Hasta:").pack(side='left', padx=5)
        self.date_entry_fin = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.date_entry_fin.pack(side='left', padx=5)

        self.date_frame.pack_forget()  # Inicialmente oculto

        self.button_aplicar = ctk.CTkButton(filter_frame, text="Aplicar Filtros", command=self.mostrar_resumen)
        self.button_aplicar.pack(side='left', padx=10)

    def crear_panel_resumen(self):
        self.resumen_frame = ctk.CTkFrame(self.frame)
        self.resumen_frame.pack(fill='x', padx=10, pady=10)

        self.total_ingresos_label = ctk.CTkLabel(self.resumen_frame, text="Total Ingresos: $0", font=("Arial", 16, "bold"))
        self.total_ingresos_label.pack(side='left', padx=20)

        self.total_ventas_label = ctk.CTkLabel(self.resumen_frame, text="Total Ventas: 0", font=("Arial", 16, "bold"))
        self.total_ventas_label.pack(side='left', padx=20)

        self.promedio_diario_label = ctk.CTkLabel(self.resumen_frame, text="Promedio Diario: $0", font=("Arial", 16, "bold"))
        self.promedio_diario_label.pack(side='left', padx=20)

    def crear_tab_cobros(self):
        self.tab_cobros = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_cobros, text='Lista de Cobros')

        self.tree = ttk.Treeview(self.tab_cobros, columns=('fecha', 'paciente_nombre', 'descripcion', 'cantidad', 'total'), show='headings')
        self.tree.heading('fecha', text='Fecha')
        self.tree.heading('paciente_nombre', text='Paciente')
        self.tree.heading('descripcion', text='Descripción')
        self.tree.heading('cantidad', text='Cantidad')
        self.tree.heading('total', text='Total')
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(self.tab_cobros, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)

    def crear_tab_productos(self):
        self.tab_productos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_productos, text='Productos Más Vendidos')

        self.tree_productos = ttk.Treeview(self.tab_productos, columns=('descripcion', 'cantidad', 'total'), show='headings')
        self.tree_productos.heading('descripcion', text='Producto/Servicio')
        self.tree_productos.heading('cantidad', text='Cantidad Vendida')
        self.tree_productos.heading('total', text='Total Ingresos')
        self.tree_productos.pack(fill='both', expand=True, padx=10, pady=10)

    def crear_tab_grafico(self):
        self.tab_grafico = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_grafico, text='Tendencias')

    def actualizar_fechas(self, *args):
        periodo = self.periodo_var.get()
        hoy = datetime.now().date()
        
        if periodo == "Hoy":
            inicio = hoy
            fin = hoy
        elif periodo == "Este mes":
            inicio = hoy.replace(day=1)
            fin = hoy
        elif periodo == "Último mes":
            fin = hoy.replace(day=1) - timedelta(days=1)
            inicio = fin.replace(day=1)
        elif periodo == "Este año":
            inicio = hoy.replace(month=1, day=1)
            fin = hoy
        elif periodo == "Personalizado":
            self.date_frame.pack(side='left', padx=5)
            return
        
        self.date_frame.pack_forget()
        self.date_entry_inicio.set_date(inicio)
        self.date_entry_fin.set_date(fin)

    def mostrar_resumen(self):
        fecha_inicio = self.date_entry_inicio.get_date().strftime('%Y-%m-%d')
        fecha_fin = self.date_entry_fin.get_date().strftime('%Y-%m-%d')
        
        self.filtrar_datos(fecha_inicio, fecha_fin)
        self.mostrar_productos_mas_vendidos(fecha_inicio, fecha_fin)
        self.mostrar_grafico_tendencias(fecha_inicio, fecha_fin)
        self.actualizar_panel_resumen(fecha_inicio, fecha_fin)

    def filtrar_datos(self, fecha_inicio, fecha_fin, paciente_id=None):
        # Usar LEFT JOIN para incluir cobros incluso cuando el paciente fue borrado
        query = """
            SELECT 
                c.fecha,
                COALESCE(p.nombre, 'Paciente Eliminado') as nombre_paciente,
                c.descripcion,
                c.cantidad,
                c.total
            FROM cobros c
            LEFT JOIN pacientes p ON c.paciente_id = p.id
            WHERE c.fecha BETWEEN ? AND ?
        """
        params = [fecha_inicio, fecha_fin]

        if paciente_id:
            query += " AND c.paciente_id = ?"
            params.append(paciente_id)

        query += " ORDER BY c.fecha DESC"

        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            for row in self.tree.get_children():
                self.tree.delete(row)

            for i, row in enumerate(rows):
                tags = ('deleted',) if row[1] == 'Paciente Eliminado' else ('alternate',) if i % 2 == 1 else ()
                self.tree.insert("", "end", values=row, tags=tags)

            # Configurar colores para las filas
            self.tree.tag_configure('alternate', background='#f0f0f0')
            self.tree.tag_configure('deleted', background='#ffebee')  # Rojo claro para pacientes eliminados

        except Exception as e:
            print(f"Error al filtrar datos: {e}")

    def mostrar_productos_mas_vendidos(self, fecha_inicio, fecha_fin):
        query = """
            SELECT descripcion, SUM(cantidad) as cantidad_total, SUM(total) as total_ingresos
            FROM cobros
            WHERE fecha BETWEEN ? AND ?
            GROUP BY descripcion
            ORDER BY cantidad_total DESC
            LIMIT 10
        """
        self.cursor.execute(query, (fecha_inicio, fecha_fin))
        rows = self.cursor.fetchall()

        for row in self.tree_productos.get_children():
            self.tree_productos.delete(row)

        for row in rows:
            self.tree_productos.insert("", "end", values=row)

    def mostrar_grafico_tendencias(self, fecha_inicio, fecha_fin):
        query = """
            SELECT fecha, SUM(total) as total_diario
            FROM cobros
            WHERE fecha BETWEEN ? AND ?
            GROUP BY fecha
            ORDER BY fecha
        """
        self.cursor.execute(query, (fecha_inicio, fecha_fin))
        rows = self.cursor.fetchall()

        fechas = [row[0] for row in rows]
        totales = [row[1] for row in rows]

        for widget in self.tab_grafico.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(fechas, totales)
        ax.set_title('Tendencia de Ingresos Diarios')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Ingresos Totales')
        plt.xticks(rotation=45)

        canvas = FigureCanvasTkAgg(fig, master=self.tab_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def actualizar_panel_resumen(self, fecha_inicio, fecha_fin):
        query = """
            SELECT SUM(total) as total_ingresos, COUNT(*) as total_ventas
            FROM cobros
            WHERE fecha BETWEEN ? AND ?
        """
        self.cursor.execute(query, (fecha_inicio, fecha_fin))
        result = self.cursor.fetchone()

        total_ingresos = result[0] or 0
        total_ventas = result[1] or 0

        dias = (datetime.strptime(fecha_fin, '%Y-%m-%d') - datetime.strptime(fecha_inicio, '%Y-%m-%d')).days + 1
        promedio_diario = total_ingresos / dias if dias > 0 else 0

        self.total_ingresos_label.configure(text=f"Total Ingresos: ${total_ingresos:.2f}")
        self.total_ventas_label.configure(text=f"Total Ventas: {total_ventas}")
        self.promedio_diario_label.configure(text=f"Promedio Diario: ${promedio_diario:.2f}")

        # Eliminar nota anterior si existe
        if hasattr(self, 'nota_cobros_eliminados'):
            self.nota_cobros_eliminados.destroy()

        query = """
            SELECT COUNT(*) 
            FROM cobros c 
            LEFT JOIN pacientes p ON c.paciente_id = p.id 
            WHERE c.fecha BETWEEN ? AND ? 
            AND p.id IS NULL
        """
        self.cursor.execute(query, [fecha_inicio, fecha_fin])
        cobros_eliminados = self.cursor.fetchone()[0]
        
        if cobros_eliminados > 0:
            self.nota_cobros_eliminados = ctk.CTkLabel(
                self.resumen_frame,
                text=f"(*) Incluye {cobros_eliminados} cobro{'s' if cobros_eliminados > 1 else ''} de paciente{'s' if cobros_eliminados > 1 else ''} eliminado{'s' if cobros_eliminados > 1 else ''}",
                text_color="red",
                font=("Arial", 12)
            )
            self.nota_cobros_eliminados.pack(side='right', padx=20)

    def exportar_csv(self):
        fecha_inicio = self.date_entry_inicio.get_date().strftime('%Y-%m-%d')
        fecha_fin = self.date_entry_fin.get_date().strftime('%Y-%m-%d')
        
        query = """
            SELECT c.fecha, p.nombre, c.descripcion, c.cantidad, c.total
            FROM cobros c
            JOIN pacientes p ON c.paciente_id = p.id
            WHERE c.fecha BETWEEN ? AND ?
            ORDER BY c.fecha
        """
        df = pd.read_sql_query(query, self.conn, params=(fecha_inicio, fecha_fin))
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            initialfile=f"resumen_cobros_{fecha_inicio}_{fecha_fin}.csv"
        )
        
        if filename:
            df.to_csv(filename, index=False)
            messagebox.showinfo("Exportar Datos", f"Datos exportados a {filename}")
        else:
            messagebox.showinfo("Exportar Datos", "Exportación cancelada")

    def mostrar_ayuda(self):
        # Crear ventana de ayuda
        ventana_ayuda = ctk.CTkToplevel(self.parent)
        ventana_ayuda.title("Ayuda - Historial de Pacientes")
        ventana_ayuda.geometry("800x600")  # Tamaño inicial más grande

        # Hacer la ventana modal
        ventana_ayuda.transient(self.parent)
        ventana_ayuda.grab_set()

        # Crear frame principal
        frame_principal = ctk.CTkFrame(ventana_ayuda)
        frame_principal.pack(fill='both', expand=True, padx=20, pady=20)

        # Título
        ctk.CTkLabel(
            frame_principal,
            text="Guía de Uso - Historial de Pacientes",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 10))

        # Crear widget de texto con scroll
        from tkinter import scrolledtext
        texto_ayuda = scrolledtext.ScrolledText(
            frame_principal,
            wrap='word',  # Envolver palabras
            font=("Arial", 12),
            padx=10,
            pady=10
        )
        texto_ayuda.pack(fill='both', expand=True)

        # Insertar el texto de ayuda
        mensaje_ayuda = """
            Guía de Uso - Módulo de Resumen de Cobros

            PANEL SUPERIOR - FILTROS Y CONTROLES
            ----------------------------------
            Ubicado en la parte superior de la ventana:

            1. Selector de Período:
            • "Hoy": Muestra cobros del día actual
            • "Este mes": Cobros del mes en curso
            • "Último mes": Cobros del mes anterior
            • "Este año": Todos los cobros del año actual
            • "Personalizado": Permite seleccionar rango de fechas específico

            2. Selector de Fechas (visible con período "Personalizado"):
            • "Desde": Seleccione fecha inicial
            • "Hasta": Seleccione fecha final

            3. Búsqueda de Paciente:
            • Campo de texto para filtrar por nombre de paciente
            • Búsqueda en tiempo real mientras escribe

            PANEL DE RESUMEN FINANCIERO
            --------------------------
            Muestra estadísticas generales del período seleccionado:
            • Total de Ingresos: Suma de todos los cobros
            • Total de Ventas: Número de transacciones
            • Promedio Diario: Ingresos promedio por día

            PESTAÑAS DE INFORMACIÓN
            ----------------------
            1. LISTA DE COBROS
            • Tabla detallada con todas las transacciones
            • Columnas:
                - ID: Identificador único del cobro
                - Fecha: Día de la transacción
                - Paciente: Nombre del cliente
                - Descripción: Detalle del cobro
                - Cantidad: Unidades vendidas
                - Total: Monto de la transacción
            • Los cobros de pacientes eliminados aparecen marcados
            • Ordenamiento por columnas disponible

            2. PRODUCTOS MÁS VENDIDOS
            • Ranking de productos por cantidad vendida
            • Muestra:
                - Nombre del producto/servicio
                - Cantidad total vendida
                - Total de ingresos generados
            • Limitado a los 10 productos más vendidos

            3. TENDENCIAS
            • Gráfico de ingresos diarios
            • Visualización de patrones de venta
            • Permite identificar:
                - Días pico de ventas
                - Tendencias temporales
                - Comparativas por período

            FUNCIONES ADICIONALES
            -------------------
            1. Exportar Datos:
            • Botón "Exportar Datos" genera archivo CSV
            • Incluye todos los cobros del período seleccionado
            • Útil para análisis externos o respaldo

            2. Actualización Automática:
            • Los datos se actualizan al cambiar filtros
            • La búsqueda filtra en tiempo real
            • Los totales se recalculan automáticamente

            CONSEJOS DE USO
            --------------
            • Use diferentes períodos para análisis comparativos
            • Exporte datos regularmente para respaldo
            • Verifique tendencias para:
                - Planificación de inventario
                - Identificar mejores días de venta
                - Análisis de comportamiento de ventas
            • Use la búsqueda para rastrear cobros específicos
            • Revise regularmente los productos más vendidos
            • Compare promedios diarios entre diferentes períodos

            NOTAS IMPORTANTES
            ---------------
            • Los montos se muestran en pesos mexicanos
            • Los cobros eliminados se mantienen en el historial
            • El sistema marca automáticamente pacientes eliminados
            • Los gráficos se actualizan con cada cambio de filtro
            • Puede ordenar las tablas por cualquier columna
            • Los datos exportados incluyen todos los detalles mostrados
            """
        texto_ayuda.insert('1.0', mensaje_ayuda)
        texto_ayuda.configure(state='disabled')  # Hacer el texto de solo lectura

        # Botón de cerrar
        ctk.CTkButton(
            frame_principal,
            text="Cerrar",
            command=ventana_ayuda.destroy,
            width=100
        ).pack(pady=10)

    def __del__(self):
        self.conn.close()