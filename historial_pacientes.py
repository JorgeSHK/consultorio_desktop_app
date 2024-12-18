import customtkinter as ctk
import sqlite3
from tkinter import ttk, messagebox
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class HistorialPacientes:
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn
        self.create_widgets()

    def create_widgets(self):
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.parent)
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Frame de búsqueda
        self.frame_busqueda = ctk.CTkFrame(self.main_frame)
        self.frame_busqueda.pack(fill='x', padx=10, pady=10)

        ctk.CTkLabel(self.frame_busqueda, 
                    text="Buscar Paciente:", 
                    font=("Arial", 12, "bold")
                    ).pack(side='left', padx=5)

        # Frame para el área de búsqueda
        search_area = ctk.CTkFrame(self.frame_busqueda)
        search_area.pack(side='left', fill='x', expand=True, padx=5)
        
        self.entry_busqueda = ctk.CTkEntry(search_area, 
                                        width=300,
                                        placeholder_text="Escriba el nombre del paciente...")
        self.entry_busqueda.pack(fill='x', pady=5)
        
        # Lista de resultados (inicialmente oculta)
        self.lista_resultados = ttk.Treeview(search_area, 
                                            columns=("ID", "Nombre", "Teléfono"),
                                            show='headings',
                                            height=5)
        self.lista_resultados.heading("ID", text="ID")
        self.lista_resultados.heading("Nombre", text="Nombre")
        self.lista_resultados.heading("Teléfono", text="Teléfono")
        
        # Ocultar la columna ID
        self.lista_resultados.column("ID", width=0, stretch=False)
        
        # Vincular eventos
        self.entry_busqueda.bind('<KeyRelease>', self.buscar_paciente)
        self.lista_resultados.bind('<<TreeviewSelect>>', self.seleccionar_paciente)

        # Frame para la información del paciente (Este es el que faltaba)
        self.frame_info = ctk.CTkFrame(self.main_frame)
        self.frame_info.pack(fill='x', padx=10, pady=10)

        # Notebook para diferentes secciones
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Pestaña de Información General
        self.tab_info = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_info, text='Información General')

        # Pestaña de Historial de Citas
        self.tab_citas = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_citas, text='Historial de Citas')

        # Pestaña de Historial de Cobros
        self.tab_cobros = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_cobros, text='Historial de Cobros')

        # Pestaña de Historial de Plantillas
        self.tab_plantillas = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_plantillas, text='Historial de Plantillas')

        # Pestaña de Estadísticas
        self.tab_estadisticas = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_estadisticas, text='Estadísticas')

        frame_botones = ctk.CTkFrame(self.main_frame)
        frame_botones.pack(fill='x', pady=(0,5))

        boton_ayuda = ctk.CTkButton(
            frame_botones,
            text="Ayuda",
            command=self.mostrar_ayuda,
            width=100,
            height=32,
            font=("Arial",12)
        )
        boton_ayuda.pack(side='right',padx=10)
        
    def mostrar_info_paciente(self, paciente_id):
        # Limpiar frame de información
        for widget in self.frame_info.winfo_children():
            widget.destroy()

        try:
            cursor = self.conn.cursor()
            
            # Primera consulta para información básica y citas
            cursor.execute('''
                SELECT 
                    p.nombre, 
                    p.telefono, 
                    p.es_distribuidor,
                    COUNT(DISTINCT c.id) as total_citas,
                    MAX(c.fecha) as ultima_cita
                FROM pacientes p
                LEFT JOIN citas c ON p.id = c.paciente_id
                WHERE p.id = ?
                GROUP BY p.id
            ''', (paciente_id,))
            
            info_basica = cursor.fetchone()
            
            # Segunda consulta específica para cobros
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_cobros,
                    SUM(total) as total_gastado
                FROM cobros 
                WHERE paciente_id = ?
            ''', (paciente_id,))
            
            info_cobros = cursor.fetchone()
            
            if info_basica:
                # Frame para información básica
                info_basica_frame = ctk.CTkFrame(self.frame_info)
                info_basica_frame.pack(fill='x', padx=10, pady=5)
                
                # Título con el nombre
                ctk.CTkLabel(info_basica_frame, 
                            text=info_basica[0],
                            font=("Arial", 20, "bold")
                            ).pack(pady=5)
                
                # Grid de información
                info_grid = ctk.CTkFrame(info_basica_frame)
                info_grid.pack(fill='x', padx=10, pady=5)
                
                # Columna 1
                col1 = ctk.CTkFrame(info_grid)
                col1.pack(side='left', padx=10, expand=True)
                
                ctk.CTkLabel(col1, text=f"Teléfono: {info_basica[1]}", 
                            font=("Arial", 12)).pack(pady=2)
                ctk.CTkLabel(col1, text=f"Distribuidor: {'Sí' if info_basica[2] else 'No'}", 
                            font=("Arial", 12)).pack(pady=2)
                
                # Columna 2
                col2 = ctk.CTkFrame(info_grid)
                col2.pack(side='left', padx=10, expand=True)
                
                ctk.CTkLabel(col2, text=f"Total Citas: {info_basica[3] or 0}", 
                            font=("Arial", 12)).pack(pady=2)
                ctk.CTkLabel(col2, text=f"Total Cobros: {info_cobros[0] or 0}", 
                            font=("Arial", 12)).pack(pady=2)
                
                # Columna 3
                col3 = ctk.CTkFrame(info_grid)
                col3.pack(side='left', padx=10, expand=True)
                
                total_gastado = info_cobros[1] or 0
                ctk.CTkLabel(col3, text=f"Total Gastado: ${total_gastado:.2f}", 
                            font=("Arial", 12)).pack(pady=2)
                if info_basica[4]:  # ultima_cita
                    ctk.CTkLabel(col3, text=f"Última Cita: {info_basica[4]}", 
                                font=("Arial", 12)).pack(pady=2)
                
                # Actualizar las pestañas con la información detallada
                self.actualizar_informacion_general(paciente_id)
                self.actualizar_historial_citas(paciente_id)
                self.actualizar_historial_cobros(paciente_id)
                self.mostrar_historial_plantillas(paciente_id, self.tab_plantillas)
                self.actualizar_estadisticas(paciente_id)
                
        except Exception as e:
            print(f"Error al cargar información: {str(e)}")
            messagebox.showerror("Error", f"Error al cargar información: {str(e)}")

    def actualizar_informacion_general(self, paciente_id):
        # Limpiar pestaña
        for widget in self.tab_info.winfo_children():
            widget.destroy()

        main_frame = ctk.CTkFrame(self.tab_info)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        try:
            cursor = self.conn.cursor()
            
            # Obtener información general del paciente
            query = '''
                WITH datos_paciente AS (
                    SELECT 
                        p.nombre, 
                        p.telefono, 
                        p.es_distribuidor,
                        COUNT(DISTINCT c.id) as total_citas,
                        COUNT(DISTINCT co.id) as total_cobros,
                        SUM(co.total) as total_gastado,
                        MAX(c.fecha) as ultima_cita,
                        MIN(c.fecha) as primera_cita
                    FROM pacientes p
                    LEFT JOIN citas c ON p.id = c.paciente_id
                    LEFT JOIN cobros co ON p.id = co.paciente_id
                    WHERE p.id = ?
                    GROUP BY p.id
                )
                SELECT 
                    *,
                    (SELECT COUNT(*) FROM citas 
                    WHERE paciente_id = ? AND fecha >= date('now')) as citas_pendientes,
                    (SELECT COUNT(*) FROM plantillas 
                    WHERE paciente_id = ?) as total_plantillas
                FROM datos_paciente
            '''
            cursor.execute(query, (paciente_id, paciente_id, paciente_id))
            info = cursor.fetchone()

            if info:
                # Sección de Información Personal
                frame_personal = ctk.CTkFrame(main_frame)
                frame_personal.pack(fill='x', pady=10)
                
                ctk.CTkLabel(frame_personal, 
                            text="Información Personal", 
                            font=("Arial", 16, "bold")
                            ).pack(pady=10)

                info_personal = [
                    ("Teléfono:", info[1]),
                    ("Tipo de Cliente:", "Distribuidor" if info[2] else "Regular"),
                    ("Primera Visita:", info[7] or "N/A"),
                    ("Última Visita:", info[6] or "N/A")
                ]

                for label, value in info_personal:
                    frame_row = ctk.CTkFrame(frame_personal)
                    frame_row.pack(fill='x', padx=20, pady=2)
                    ctk.CTkLabel(frame_row, text=label, font=("Arial", 12, "bold")).pack(side='left')
                    ctk.CTkLabel(frame_row, text=str(value), font=("Arial", 12)).pack(side='left', padx=10)

                # Sección de Resumen de Actividad
                frame_resumen = ctk.CTkFrame(main_frame)
                frame_resumen.pack(fill='x', pady=10)
                
                ctk.CTkLabel(frame_resumen, 
                            text="Resumen de Actividad", 
                            font=("Arial", 16, "bold")
                            ).pack(pady=10)

                resumen_actividad = [
                    ("Total de Citas:", info[3] or 0),
                    ("Citas Pendientes:", info[8] or 0),
                    ("Total de Cobros:", info[4] or 0),
                    ("Total Gastado:", f"${info[5]:.2f}" if info[5] else "$0.00"),
                    ("Plantillas Solicitadas:", info[9] or 0)
                ]

                for label, value in resumen_actividad:
                    frame_row = ctk.CTkFrame(frame_resumen)
                    frame_row.pack(fill='x', padx=20, pady=2)
                    ctk.CTkLabel(frame_row, text=label, font=("Arial", 12, "bold")).pack(side='left')
                    ctk.CTkLabel(frame_row, text=str(value), font=("Arial", 12)).pack(side='left', padx=10)

                # Sección de Próximas Citas
                frame_proximas = ctk.CTkFrame(main_frame)
                frame_proximas.pack(fill='x', pady=10)
                
                ctk.CTkLabel(frame_proximas, 
                            text="Próximas Citas", 
                            font=("Arial", 16, "bold")
                            ).pack(pady=10)

                # Obtener próximas citas
                cursor.execute('''
                    SELECT fecha, hora, confirmado
                    FROM citas
                    WHERE paciente_id = ? AND fecha >= date('now')
                    ORDER BY fecha, hora
                    LIMIT 3
                ''', (paciente_id,))
                
                proximas_citas = cursor.fetchall()
                
                if proximas_citas:
                    for fecha, hora, confirmado in proximas_citas:
                        frame_cita = ctk.CTkFrame(frame_proximas)
                        frame_cita.pack(fill='x', padx=20, pady=2)
                        ctk.CTkLabel(frame_cita, 
                                text=f"Fecha: {fecha} - Hora: {hora} - Confirmado: {confirmado}",
                                font=("Arial", 12)
                                ).pack(pady=5)
                else:
                    ctk.CTkLabel(frame_proximas, 
                            text="No hay citas programadas",
                            font=("Arial", 12)
                            ).pack(pady=5)

        except Exception as e:
            print(f"Error al cargar información general: {str(e)}")
            messagebox.showerror("Error", f"Error al cargar información: {str(e)}")

    def actualizar_estadisticas(self, paciente_id):
        # Limpiar pestaña
        for widget in self.tab_estadisticas.winfo_children():
            widget.destroy()

        # Frame principal para los gráficos
        frame_estadisticas = ctk.CTkFrame(self.tab_estadisticas)
        frame_estadisticas.pack(fill='both', expand=True, padx=10, pady=5)

        # Crear figura con subplots
        fig = plt.Figure(figsize=(12, 8))
        fig.subplots_adjust(hspace=0.4, wspace=0.3)

        try:
            # 1. Gráfico de gastos mensuales
            ax1 = fig.add_subplot(221)
            self.grafico_gastos_mensuales(paciente_id, ax1)

            # 2. Gráfico de distribución de tipos de cobro
            ax2 = fig.add_subplot(222)
            self.grafico_distribucion_cobros(paciente_id, ax2)

            # 3. Gráfico de frecuencia de visitas
            ax3 = fig.add_subplot(223)
            self.grafico_frecuencia_visitas(paciente_id, ax3)

            # 4. Productos más comprados
            ax4 = fig.add_subplot(224)
            self.grafico_productos_frecuentes(paciente_id, ax4)

            # Crear el canvas y empaquetarlo
            canvas = FigureCanvasTkAgg(fig, frame_estadisticas)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)

            # Agregar resumen de estadísticas
            frame_resumen = ctk.CTkFrame(frame_estadisticas)
            frame_resumen.pack(fill='x', pady=10)

            # Obtener estadísticas generales
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            
            # Total gastado
            cursor.execute('''
                SELECT SUM(total) 
                FROM cobros 
                WHERE paciente_id = ?
            ''', (paciente_id,))
            total_gastado = cursor.fetchone()[0] or 0

            # Promedio por visita
            cursor.execute('''
                SELECT AVG(total) 
                FROM cobros 
                WHERE paciente_id = ?
            ''', (paciente_id,))
            promedio_visita = cursor.fetchone()[0] or 0

            # Total de visitas
            cursor.execute('''
                SELECT COUNT(DISTINCT fecha) 
                FROM cobros 
                WHERE paciente_id = ?
            ''', (paciente_id,))
            total_visitas = cursor.fetchone()[0] or 0

            # Producto más comprado
            cursor.execute('''
                SELECT descripcion, SUM(cantidad) as total_cantidad
                FROM cobros 
                WHERE paciente_id = ? AND descripcion != 'Consulta'
                GROUP BY descripcion
                ORDER BY total_cantidad DESC
                LIMIT 1
            ''', (paciente_id,))
            producto_frecuente = cursor.fetchone()

            conn.close()

            # Mostrar estadísticas
            ctk.CTkLabel(frame_resumen, 
                        text=f"Total Gastado: ${total_gastado:.2f}", 
                        font=("Arial", 12, "bold")).pack(side='left', padx=20)
            
            ctk.CTkLabel(frame_resumen, 
                        text=f"Promedio por Visita: ${promedio_visita:.2f}", 
                        font=("Arial", 12, "bold")).pack(side='left', padx=20)
            
            ctk.CTkLabel(frame_resumen, 
                        text=f"Total de Visitas: {total_visitas}", 
                        font=("Arial", 12, "bold")).pack(side='left', padx=20)

            if producto_frecuente:
                ctk.CTkLabel(frame_resumen, 
                            text=f"Producto más comprado: {producto_frecuente[0]} ({producto_frecuente[1]} unidades)", 
                            font=("Arial", 12, "bold")).pack(side='left', padx=20)

        except Exception as e:
            print(f"Error al cargar estadísticas: {str(e)}")
            ctk.CTkLabel(frame_estadisticas, 
                        text="Error al cargar estadísticas", 
                        font=("Arial", 14, "bold"),
                        text_color="red").pack(pady=20)

    def grafico_gastos_mensuales(self, paciente_id, ax):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', fecha) as mes,
                SUM(total) as total_mes
            FROM cobros 
            WHERE paciente_id = ?
            GROUP BY mes
            ORDER BY mes
            LIMIT 12
        ''', (paciente_id,))
        
        datos = cursor.fetchall()
        if datos:
            meses = [d[0] for d in datos]
            totales = [d[1] for d in datos]
            
            # Crear las barras con rango numérico
            x = range(len(meses))
            ax.bar(x, totales, color='skyblue')
            
            # Establecer los ticks y sus etiquetas
            ax.set_xticks(x)
            ax.set_xticklabels(meses, rotation=45, ha='right')
            
            ax.set_title('Gastos Mensuales')
            ax.set_ylabel('Total ($)')
            
            # Ajustar el diseño para que las etiquetas no se corten
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    def grafico_distribucion_cobros(self, paciente_id, ax):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN descripcion = 'Consulta' THEN 'Consultas'
                    WHEN descripcion IN (SELECT nombre FROM productos) THEN 'Productos'
                    WHEN descripcion IN (SELECT nombre FROM materiales_cirugia) THEN 'Materiales'
                    ELSE 'Otros'
                END as tipo,
                SUM(total) as total_tipo
            FROM cobros 
            WHERE paciente_id = ?
            GROUP BY tipo
        ''', (paciente_id,))
        
        datos = cursor.fetchall()
        if datos:
            tipos = [d[0] for d in datos]
            totales = [d[1] for d in datos]
            
            ax.pie(totales, labels=tipos, autopct='%1.1f%%')
            ax.set_title('Distribución de Gastos')

    def grafico_frecuencia_visitas(self, paciente_id, ax):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', fecha) as mes,
                COUNT(*) as num_visitas
            FROM citas 
            WHERE paciente_id = ?
            GROUP BY mes
            ORDER BY mes
            LIMIT 12
        ''', (paciente_id,))
        
        datos = cursor.fetchall()
        if datos:
            meses = [d[0] for d in datos]
            visitas = [d[1] for d in datos]
            
            # Crear el gráfico con rango numérico
            x = range(len(meses))
            ax.plot(x, visitas, 'o-', color='green')
            
            # Establecer los ticks y sus etiquetas
            ax.set_xticks(x)
            ax.set_xticklabels(meses, rotation=45, ha='right')
            
            ax.set_title('Frecuencia de Visitas')
            ax.set_ylabel('Número de Visitas')
            
            # Ajustar el diseño para que las etiquetas no se corten
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
    def grafico_productos_frecuentes(self, paciente_id, ax):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                descripcion,
                COUNT(*) as veces_comprado,
                SUM(cantidad) as cantidad_total
            FROM cobros 
            WHERE paciente_id = ? 
            AND descripcion != 'Consulta'
            GROUP BY descripcion
            ORDER BY veces_comprado DESC
            LIMIT 5
        ''', (paciente_id,))
        
        datos = cursor.fetchall()
        if datos:
            productos = [d[0] for d in datos]
            cantidades = [d[2] for d in datos]
            
            ax.barh(productos, cantidades, color='lightgreen')
            ax.set_title('Productos Más Comprados')
            ax.set_xlabel('Cantidad Total')

    def buscar_paciente(self, event):
        busqueda = self.entry_busqueda.get().strip()
        
        # Ocultar la lista si la búsqueda está vacía
        if not busqueda:
            self.lista_resultados.pack_forget()
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, nombre, telefono
                FROM pacientes
                WHERE nombre LIKE ?
                ORDER BY nombre
                LIMIT 10
            ''', (f'%{busqueda}%',))
            
            resultados = cursor.fetchall()
            
            # Limpiar resultados anteriores
            for item in self.lista_resultados.get_children():
                self.lista_resultados.delete(item)
                
            if resultados:
                # Mostrar la lista y agregar resultados
                self.lista_resultados.pack(fill='x', pady=5)
                for id_paciente, nombre, telefono in resultados:
                    self.lista_resultados.insert("", "end", values=(id_paciente, nombre, telefono))
            else:
                # Mostrar mensaje de "no se encontraron resultados"
                self.lista_resultados.pack(fill='x', pady=5)
                self.lista_resultados.insert("", "end", values=("", "No se encontraron resultados", ""))
                
        except Exception as e:
            print(f"Error en búsqueda: {str(e)}")

    def seleccionar_paciente(self, event):
        seleccion = self.lista_resultados.selection()
        if not seleccion:
            return
            
        # Obtener el ID del paciente seleccionado
        valores = self.lista_resultados.item(seleccion[0])['values']
        if valores and valores[0]:  # Asegurarse de que no es el mensaje "No se encontraron resultados"
            paciente_id = valores[0]
            self.mostrar_info_paciente(paciente_id)
            
            # Actualizar la entrada con el nombre seleccionado
            self.entry_busqueda.delete(0, 'end')
            self.entry_busqueda.insert(0, valores[1])
            
            # Ocultar la lista de resultados
            self.lista_resultados.pack_forget()

    def actualizar_historial_citas(self, paciente_id):
        # Limpiar pestaña
        for widget in self.tab_citas.winfo_children():
            widget.destroy()

        # Frame principal que contendrá todo
        main_frame = ctk.CTkFrame(self.tab_citas)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Frame para controles y filtros en la parte superior
        frame_controles = ctk.CTkFrame(main_frame)
        frame_controles.pack(fill='x', padx=10, pady=5)

        # Filtros para citas
        ctk.CTkLabel(frame_controles, text="Filtrar por:").pack(side='left', padx=5)
        
        self.filtro_citas = ctk.StringVar(value="Todas")
        opciones = ctk.CTkOptionMenu(
            frame_controles,
            values=["Todas", "Pendientes", "Realizadas", "Último Mes", "Último Año"],
            variable=self.filtro_citas,
            command=lambda x: self.filtrar_citas(paciente_id)
        )
        opciones.pack(side='left', padx=5)

        # Frame para la tabla de citas
        frame_tabla = ctk.CTkFrame(main_frame)
        frame_tabla.pack(fill='both', expand=True, padx=10, pady=5)

        # Crear Treeview para citas
        columns = ("Fecha", "Hora", "Confirmado", "Estado")
        self.tree_citas = ttk.Treeview(frame_tabla, columns=columns, show='headings')
        
        # Configurar columnas
        for col in columns:
            self.tree_citas.heading(col, text=col)
            self.tree_citas.column(col, width=100)

        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree_citas.yview)
        self.tree_citas.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar el treeview y scrollbar
        self.tree_citas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Frame para el resumen de estadísticas (ahora al final)
        frame_resumen = ctk.CTkFrame(main_frame)
        frame_resumen.pack(fill='x', padx=10, pady=5)

        try:
            cursor = self.conn.cursor()
            query = '''
                SELECT 
                    COUNT(*) as total_citas,
                    SUM(CASE WHEN fecha >= date('now') THEN 1 ELSE 0 END) as citas_pendientes,
                    SUM(CASE WHEN confirmado = 'Sí' THEN 1 ELSE 0 END) as citas_confirmadas,
                    MAX(fecha) as ultima_cita
                FROM citas 
                WHERE paciente_id = ?
            '''
            cursor.execute(query, (paciente_id,))
            stats = cursor.fetchone()
            
            if stats:
                # Primera línea de estadísticas
                frame_stats_1 = ctk.CTkFrame(frame_resumen)
                frame_stats_1.pack(fill='x', pady=5)
                
                ctk.CTkLabel(frame_stats_1, 
                            text=f"Total de Citas: {stats[0]}", 
                            font=("Arial", 12, "bold")
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(frame_stats_1, 
                            text=f"Citas Pendientes: {stats[1] or 0}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                # Segunda línea de estadísticas
                frame_stats_2 = ctk.CTkFrame(frame_resumen)
                frame_stats_2.pack(fill='x', pady=5)
                
                ctk.CTkLabel(frame_stats_2, 
                            text=f"Citas Confirmadas: {stats[2] or 0}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                if stats[3]:
                    ctk.CTkLabel(frame_stats_2, 
                                text=f"Última Cita: {stats[3]}", 
                                font=("Arial", 12)
                                ).pack(side='left', padx=20)

        except Exception as e:
            print(f"Error al cargar estadísticas de citas: {str(e)}")

        # Cargar las citas
        self.cargar_citas(paciente_id)

    def cargar_citas(self, paciente_id):
        try:
            cursor = self.conn.cursor()
            
            # Obtener la fecha actual para determinar el estado de las citas
            hoy = datetime.now().strftime('%Y-%m-%d')
            
            query = '''
                SELECT 
                    fecha, 
                    hora, 
                    confirmado,
                    CASE 
                        WHEN fecha > ? THEN 'Pendiente'
                        WHEN fecha = ? THEN 'Hoy'
                        ELSE 'Realizada'
                    END as estado
                FROM citas 
                WHERE paciente_id = ?
                ORDER BY fecha DESC, hora DESC
            '''
            
            cursor.execute(query, (hoy, hoy, paciente_id))
            citas = cursor.fetchall()
            
            # Limpiar treeview
            for item in self.tree_citas.get_children():
                self.tree_citas.delete(item)
            
            # Insertar citas con colores según estado
            for cita in citas:
                tags = ()
                if cita[3] == 'Pendiente':
                    tags = ('pendiente',)
                elif cita[3] == 'Hoy':
                    tags = ('hoy',)
                elif cita[3] == 'Realizada':
                    tags = ('realizada',)
                    
                self.tree_citas.insert("", "end", values=cita, tags=tags)
            
            # Configurar colores
            self.tree_citas.tag_configure('pendiente', background='#fff3e0')  # Naranja claro
            self.tree_citas.tag_configure('hoy', background='#e8f5e9')       # Verde claro
            self.tree_citas.tag_configure('realizada', background='#f5f5f5') # Gris claro
            
        except Exception as e:
            print(f"Error al cargar citas: {str(e)}")

    def actualizar_resumen_citas(self, paciente_id):
        try:
            cursor = self.conn.cursor()
            
            # Obtener estadísticas de citas
            query = '''
                SELECT 
                    COUNT(*) as total_citas,
                    SUM(CASE WHEN fecha >= date('now') THEN 1 ELSE 0 END) as citas_pendientes,
                    SUM(CASE WHEN confirmado = 'Sí' THEN 1 ELSE 0 END) as citas_confirmadas,
                    MAX(fecha) as ultima_cita
                FROM citas 
                WHERE paciente_id = ?
            '''
            
            cursor.execute(query, (paciente_id,))
            stats = cursor.fetchone()
            
            if stats:
                # Frame para estadísticas (quitamos el frame extra que causaba el cuadro negro)
                ctk.CTkLabel(self.tab_citas, 
                            text=f"Total de Citas: {stats[0]}", 
                            font=("Arial", 12, "bold")
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(self.tab_citas, 
                            text=f"Citas Pendientes: {stats[1] or 0}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(self.tab_citas, 
                            text=f"Citas Confirmadas: {stats[2] or 0}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                if stats[3]:
                    ctk.CTkLabel(self.tab_citas, 
                                text=f"Última Cita: {stats[3]}", 
                                font=("Arial", 12)
                                ).pack(side='left', padx=20)
                    
        except Exception as e:
            print(f"Error al actualizar resumen de citas: {str(e)}")

    def filtrar_citas(self, paciente_id):
        filtro = self.filtro_citas.get()
        try:
            cursor = self.conn.cursor()
            hoy = datetime.now().strftime('%Y-%m-%d')
            
            query = '''
                SELECT 
                    fecha, 
                    hora, 
                    confirmado,
                    CASE 
                        WHEN fecha > ? THEN 'Pendiente'
                        WHEN fecha = ? THEN 'Hoy'
                        ELSE 'Realizada'
                    END as estado
                FROM citas 
                WHERE paciente_id = ?
            '''
            
            if filtro == "Pendientes":
                query += " AND fecha >= ?"
                params = (hoy, hoy, paciente_id, hoy)
            elif filtro == "Realizadas":
                query += " AND fecha < ?"
                params = (hoy, hoy, paciente_id, hoy)
            elif filtro == "Último Mes":
                query += " AND fecha >= date(?, '-1 month')"
                params = (hoy, hoy, paciente_id, hoy)
            elif filtro == "Último Año":
                query += " AND fecha >= date(?, '-1 year')"
                params = (hoy, hoy, paciente_id, hoy)
            else:  # Todas
                params = (hoy, hoy, paciente_id)
                
            query += " ORDER BY fecha DESC, hora DESC"
            
            cursor.execute(query, params)
            citas = cursor.fetchall()
            
            # Actualizar treeview
            for item in self.tree_citas.get_children():
                self.tree_citas.delete(item)
                
            for cita in citas:
                tags = ()
                if cita[3] == 'Pendiente':
                    tags = ('pendiente',)
                elif cita[3] == 'Hoy':
                    tags = ('hoy',)
                elif cita[3] == 'Realizada':
                    tags = ('realizada',)
                    
                self.tree_citas.insert("", "end", values=cita, tags=tags)
                
        except Exception as e:
            print(f"Error al filtrar citas: {str(e)}")

    def actualizar_historial_cobros(self, paciente_id):
        # Limpiar pestaña
        for widget in self.tab_cobros.winfo_children():
            widget.destroy()

        # Frame para controles y filtros
        frame_controles = ctk.CTkFrame(self.tab_cobros)
        frame_controles.pack(fill='x', padx=10, pady=5)

        # Filtros para cobros
        ctk.CTkLabel(frame_controles, text="Filtrar por:").pack(side='left', padx=5)
        
        self.filtro_cobros = ctk.StringVar(value="Todos")
        opciones = ctk.CTkOptionMenu(
            frame_controles,
            values=["Todos", "Último Mes", "Últimos 3 Meses", "Este Año"],
            variable=self.filtro_cobros,
            command=lambda x: self.filtrar_cobros(paciente_id)
        )
        opciones.pack(side='left', padx=5)

        # Frame principal para la información de cobros
        frame_cobros = ctk.CTkFrame(self.tab_cobros)
        frame_cobros.pack(fill='both', expand=True, padx=10, pady=5)

        # Crear Treeview para cobros
        columns = ("Fecha", "Descripción", "Cantidad", "Total", "Tipo")
        self.tree_cobros = ttk.Treeview(frame_cobros, columns=columns, show='headings')
        
        # Configurar columnas
        self.tree_cobros.heading("Fecha", text="Fecha")
        self.tree_cobros.heading("Descripción", text="Descripción")
        self.tree_cobros.heading("Cantidad", text="Cantidad")
        self.tree_cobros.heading("Total", text="Total")
        self.tree_cobros.heading("Tipo", text="Tipo")
        
        # Ajustar anchos de columna
        self.tree_cobros.column("Fecha", width=100)
        self.tree_cobros.column("Descripción", width=200)
        self.tree_cobros.column("Cantidad", width=80)
        self.tree_cobros.column("Total", width=100)
        self.tree_cobros.column("Tipo", width=100)

        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(frame_cobros, orient="vertical", command=self.tree_cobros.yview)
        self.tree_cobros.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar el treeview y scrollbar
        self.tree_cobros.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Frame para resumen de cobros
        self.frame_resumen_cobros = ctk.CTkFrame(self.tab_cobros)
        self.frame_resumen_cobros.pack(fill='x', padx=10, pady=5)

        self.cargar_cobros(paciente_id)
        self.actualizar_resumen_cobros(paciente_id)

    def cargar_cobros(self, paciente_id):
        try:
            cursor = self.conn.cursor()
            query = '''
                SELECT 
                    fecha,
                    descripcion,
                    cantidad,
                    total,
                    CASE 
                        WHEN descripcion = 'Consulta' THEN 'Consulta'
                        WHEN descripcion IN (SELECT nombre FROM productos) THEN 'Producto'
                        WHEN descripcion IN (SELECT nombre FROM materiales_cirugia) THEN 'Material'
                        ELSE 'Otro'
                    END as tipo
                FROM cobros 
                WHERE paciente_id = ?
                ORDER BY fecha DESC
            '''
            
            cursor.execute(query, (paciente_id,))
            cobros = cursor.fetchall()
            
            # Limpiar treeview
            for item in self.tree_cobros.get_children():
                self.tree_cobros.delete(item)
            
            # Insertar cobros con colores según tipo
            for cobro in cobros:
                tipo = cobro[4]
                tags = (tipo.lower(),)
                valores = (
                    cobro[0],
                    cobro[1],
                    cobro[2],
                    f"${cobro[3]:.2f}",
                    tipo
                )
                self.tree_cobros.insert("", "end", values=valores, tags=tags)
            
            # Configurar colores por tipo
            self.tree_cobros.tag_configure('consulta', background='#e8f5e9')  # Verde claro
            self.tree_cobros.tag_configure('producto', background='#e3f2fd')  # Azul claro
            self.tree_cobros.tag_configure('material', background='#fff3e0')  # Naranja claro
            self.tree_cobros.tag_configure('otro', background='#f5f5f5')     # Gris claro
            
        except Exception as e:
            print(f"Error al cargar cobros: {str(e)}")

    def actualizar_resumen_cobros(self, paciente_id):
        try:
            cursor = self.conn.cursor()
            query = '''
                SELECT 
                    COUNT(*) as total_cobros,
                    SUM(total) as total_gastado,
                    COUNT(DISTINCT fecha) as dias_visita,
                    AVG(total) as promedio_gasto,
                    SUM(CASE WHEN descripcion = 'Consulta' THEN total ELSE 0 END) as total_consultas,
                    SUM(CASE WHEN descripcion != 'Consulta' THEN total ELSE 0 END) as total_productos
                FROM cobros 
                WHERE paciente_id = ?
            '''
            
            cursor.execute(query, (paciente_id,))
            stats = cursor.fetchone()
            
            # Limpiar frame de resumen
            for widget in self.frame_resumen_cobros.winfo_children():
                widget.destroy()
            
            if stats:
                # Crear frames para organizar la información
                frame_stats_1 = ctk.CTkFrame(self.frame_resumen_cobros)
                frame_stats_1.pack(fill='x', pady=5)
                
                frame_stats_2 = ctk.CTkFrame(self.frame_resumen_cobros)
                frame_stats_2.pack(fill='x', pady=5)
                
                # Primera línea de estadísticas
                ctk.CTkLabel(frame_stats_1, 
                            text=f"Total Cobros: {stats[0]}", 
                            font=("Arial", 12, "bold")
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(frame_stats_1, 
                            text=f"Total Gastado: ${stats[1]:.2f}", 
                            font=("Arial", 12, "bold")
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(frame_stats_1, 
                            text=f"Días de Visita: {stats[2]}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                # Segunda línea de estadísticas
                ctk.CTkLabel(frame_stats_2, 
                            text=f"Promedio por Compra: ${stats[3]:.2f}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(frame_stats_2, 
                            text=f"Total en Consultas: ${stats[4]:.2f}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(frame_stats_2, 
                            text=f"Total en Productos: ${stats[5]:.2f}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
        except Exception as e:
            print(f"Error al actualizar resumen de cobros: {str(e)}")

    def filtrar_cobros(self, paciente_id):
        filtro = self.filtro_cobros.get()
        try:
            cursor = self.conn.cursor()
            hoy = datetime.now().strftime('%Y-%m-%d')
            
            query = '''
                SELECT 
                    fecha,
                    descripcion,
                    cantidad,
                    total,
                    CASE 
                        WHEN descripcion = 'Consulta' THEN 'Consulta'
                        WHEN descripcion IN (SELECT nombre FROM productos) THEN 'Producto'
                        WHEN descripcion IN (SELECT nombre FROM materiales_cirugia) THEN 'Material'
                        ELSE 'Otro'
                    END as tipo
                FROM cobros 
                WHERE paciente_id = ?
            '''
            
            if filtro == "Último Mes":
                query += " AND fecha >= date(?, '-1 month')"
                params = (paciente_id, hoy)
            elif filtro == "Últimos 3 Meses":
                query += " AND fecha >= date(?, '-3 month')"
                params = (paciente_id, hoy)
            elif filtro == "Este Año":
                query += " AND strftime('%Y', fecha) = strftime('%Y', ?)"
                params = (paciente_id, hoy)
            else:  # Todos
                params = (paciente_id,)
                
            query += " ORDER BY fecha DESC"
            
            cursor.execute(query, params)
            cobros = cursor.fetchall()
            
            # Actualizar treeview
            for item in self.tree_cobros.get_children():
                self.tree_cobros.delete(item)
                
            for cobro in cobros:
                tipo = cobro[4]
                tags = (tipo.lower(),)
                valores = (
                    cobro[0],
                    cobro[1],
                    cobro[2],
                    f"${cobro[3]:.2f}",
                    tipo
                )
                self.tree_cobros.insert("", "end", values=valores, tags=tags)
            
            # Actualizar el resumen con los datos filtrados
            self.actualizar_resumen_cobros(paciente_id)
                
        except Exception as e:
            print(f"Error al filtrar cobros: {str(e)}")

    def mostrar_historial_plantillas(self, paciente_id, parent_frame):
        # Primero limpiar todo el contenido del parent_frame
        for widget in parent_frame.winfo_children():
            widget.destroy()

        # Frame principal que abarcará todo el espacio
        main_frame = ctk.CTkFrame(parent_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Frame para el encabezado y filtros
        frame_header = ctk.CTkFrame(main_frame)
        frame_header.pack(fill='x', pady=5, padx=10)

        # Título y filtro en la misma línea
        ctk.CTkLabel(frame_header, 
                    text="Historial de Plantillas", 
                    font=("Arial", 14, "bold")
                    ).pack(side='left', pady=5, padx=10)

        # Agregar filtro de estado
        ctk.CTkLabel(frame_header, text="Filtrar por estado:").pack(side='left', padx=5)
        self.filtro_plantillas = ctk.StringVar(value="Todas")
        filtro = ctk.CTkOptionMenu(
            frame_header,
            values=["Todas", "Pendientes", "Pagadas", "En Proceso"],
            variable=self.filtro_plantillas,
            command=lambda x: self.filtrar_plantillas(paciente_id)
        )
        filtro.pack(side='left', padx=5)

        # Frame para la tabla
        frame_tabla = ctk.CTkFrame(main_frame)
        frame_tabla.pack(fill='both', expand=True, padx=10, pady=5)

        # Crear Treeview para plantillas con más columnas
        columns = (
            "Nombre", "Fecha Pedido", "Fecha Entrega", "Número Calzado", 
            "Precio", "Cantidad Pagada", "Pendiente", "Estado"
        )
        tree_plantillas = ttk.Treeview(frame_tabla, columns=columns, show='headings')
        
        # Configurar columnas con ancho proporcional
        for col in columns:
            tree_plantillas.heading(col, text=col)
            tree_plantillas.column(col, width=150)  # Ancho uniforme para todas las columnas

        # Agregar scrollbars
        scrolly = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree_plantillas.yview)
        scrollx = ttk.Scrollbar(frame_tabla, orient="horizontal", command=tree_plantillas.xview)
        tree_plantillas.configure(yscrollcommand=scrolly.set, xscrollcommand=scrollx.set)
        
        # Empaquetar con scrollbars
        scrolly.pack(side='right', fill='y')
        scrollx.pack(side='bottom', fill='x')
        tree_plantillas.pack(side='left', fill='both', expand=True)

        # Cargar datos de plantillas
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    nombre,
                    fecha_pedido,
                    fecha_entrega,
                    numero_calzado,
                    precio,
                    COALESCE(cantidad_pagada, 0) as cantidad_pagada,
                    COALESCE(precio - cantidad_pagada, precio) as pendiente,
                    estado
                FROM plantillas
                WHERE paciente_id = ?
                ORDER BY fecha_pedido DESC
            ''', (paciente_id,))
            
            plantillas = cursor.fetchall()
            for plantilla in plantillas:
                # Configurar colores según el estado
                if plantilla[7] == 'Pagada':
                    tags = ('pagada',)
                elif plantilla[7] == 'Pendiente de pago':
                    tags = ('pendiente',)
                elif plantilla[7] == 'En Proceso':
                    tags = ('proceso',)
                else:
                    tags = ()

                # Formatear fechas y valores monetarios
                valores = list(plantilla)
                valores[4] = f"${valores[4]:.2f}"  # Precio
                valores[5] = f"${valores[5]:.2f}"  # Cantidad Pagada
                valores[6] = f"${valores[6]:.2f}"  # Pendiente
                
                tree_plantillas.insert("", "end", values=valores, tags=tags)

            # Configurar colores para los diferentes estados
            tree_plantillas.tag_configure('pagada', background='#e8f5e9')    # Verde claro
            tree_plantillas.tag_configure('pendiente', background='#fff3e0')  # Naranja claro
            tree_plantillas.tag_configure('proceso', background='#e3f2fd')   # Azul claro

            # Frame para el resumen
            frame_resumen = ctk.CTkFrame(main_frame)
            frame_resumen.pack(fill='x', pady=5, padx=10)

            # Agregar resumen de plantillas
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_plantillas,
                    COALESCE(SUM(precio), 0) as total_precio,
                    COALESCE(SUM(cantidad_pagada), 0) as total_pagado,
                    COALESCE(SUM(precio - cantidad_pagada), 0) as total_pendiente,
                    COUNT(CASE WHEN estado = 'Pagada' THEN 1 END) as plantillas_pagadas,
                    COUNT(CASE WHEN estado = 'Pendiente de pago' THEN 1 END) as plantillas_pendientes
                FROM plantillas
                WHERE paciente_id = ?
            ''', (paciente_id,))
            
            stats = cursor.fetchone()
            if stats and stats[0] > 0:  # Si hay plantillas
                # Primera línea de estadísticas
                frame_stats1 = ctk.CTkFrame(frame_resumen)
                frame_stats1.pack(fill='x', pady=2)
                
                total_precio = stats[1] if stats[1] is not None else 0
                total_pagado = stats[2] if stats[2] is not None else 0
                total_pendiente = stats[3] if stats[3] is not None else 0
                
                ctk.CTkLabel(frame_stats1, 
                            text=f"Total Plantillas: {stats[0]}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(frame_stats1, 
                            text=f"Monto Total: ${total_precio:.2f}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(frame_stats1, 
                            text=f"Total Pagado: ${total_pagado:.2f}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)

                # Segunda línea de estadísticas
                frame_stats2 = ctk.CTkFrame(frame_resumen)
                frame_stats2.pack(fill='x', pady=2)
                
                ctk.CTkLabel(frame_stats2, 
                            text=f"Pendiente de Pago: ${total_pendiente:.2f}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(frame_stats2, 
                            text=f"Plantillas Pagadas: {stats[4] or 0}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
                
                ctk.CTkLabel(frame_stats2, 
                            text=f"Plantillas Pendientes: {stats[5] or 0}", 
                            font=("Arial", 12)
                            ).pack(side='left', padx=20)
            else:
                # Si no hay plantillas, mostrar mensaje
                ctk.CTkLabel(frame_resumen, 
                            text="No hay plantillas registradas", 
                            font=("Arial", 12)
                            ).pack(pady=10)

        except Exception as e:
            print(f"Error al cargar historial de plantillas: {str(e)}")
            ctk.CTkLabel(frame_resumen, 
                        text="Error al cargar el historial", 
                        font=("Arial", 12),
                        text_color="red"
                        ).pack(pady=10)

    def filtrar_plantillas(self, paciente_id):
        """Función para filtrar plantillas por estado"""
        filtro = self.filtro_plantillas.get()

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
        Guía de Uso - Historial de Pacientes

        BARRA DE BÚSQUEDA
        ----------------
        Ubicada en la parte superior:
        • Campo "Buscar Paciente": Escriba el nombre para buscar
        • La búsqueda se realiza en tiempo real
        • Los resultados aparecen en una lista desplegable
        • Seleccione un paciente para ver su historial completo

        INFORMACIÓN GENERAL DEL PACIENTE
        -----------------------------
        Panel superior:
        • Nombre del paciente
        • Número de teléfono
        • Estado de distribuidor
        • Resumen de actividad
        • Totales de citas y cobros

        PESTAÑAS DE INFORMACIÓN
        ----------------------
        1. INFORMACIÓN GENERAL
        • Datos personales completos
        • Historial de visitas
        • Próximas citas programadas
        • Resumen financiero
        • Estado de cuenta general

        2. HISTORIAL DE CITAS
        • Filtros disponibles:
            - Todas las citas
            - Pendientes
            - Realizadas
            - Último mes/año
        • Información por cita:
            - Fecha y hora
            - Estado de confirmación
            - Notas importantes
        • Código de colores:
            - Verde: Citas realizadas
            - Amarillo: Pendientes
            - Naranja: Hoy

        3. HISTORIAL DE COBROS
        • Filtros por período
        • Detalle de cada transacción:
            - Fecha
            - Descripción
            - Cantidad
            - Total
        • Totales y subtotales
        • Productos y servicios adquiridos

        4. HISTORIAL DE PLANTILLAS
        • Estado de cada plantilla:
            - Pendientes de pago
            - Pagadas
            - En proceso
        • Detalles técnicos
        • Historial de pagos
        • Fechas de pedido y entrega

        5. ESTADÍSTICAS
        • Gráficos de consumo
        • Frecuencia de visitas
        • Productos más comprados
        • Gastos mensuales
        • Tendencias de uso de servicios

        FUNCIONALIDADES ESPECIALES
        ------------------------
        1. Visualización de Datos:
        • Gráficos interactivos
        • Tablas ordenables
        • Filtros dinámicos
        • Resúmenes automáticos

        2. Seguimiento de Pagos:
        • Estado de cuenta
        • Pagos pendientes
        • Historial de transacciones
        • Balance general

        CONSEJOS DE USO
        --------------
        • Use los filtros para localizar información específica
        • Revise regularmente las estadísticas para identificar patrones
        • Verifique las próximas citas programadas
        • Mantenga actualizado el estado de las plantillas
        • Use los gráficos para análisis de largo plazo

        NOTAS IMPORTANTES
        ---------------
        • Toda la información se actualiza en tiempo real
        • Los montos se muestran en pesos mexicanos
        • Las citas pasadas no se pueden modificar
        • Los cobros eliminados se mantienen en el historial
        • Las estadísticas se actualizan automáticamente
        • Puede exportar datos específicos desde cada pestaña"""
        texto_ayuda.insert('1.0', mensaje_ayuda)
        texto_ayuda.configure(state='disabled')  # Hacer el texto de solo lectura

        # Botón de cerrar
        ctk.CTkButton(
            frame_principal,
            text="Cerrar",
            command=ventana_ayuda.destroy,
            width=100
        ).pack(pady=10)