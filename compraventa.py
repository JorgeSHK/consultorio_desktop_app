import customtkinter as ctk
import sqlite3

from tkinter import messagebox, END, ttk
from tkcalendar import Calendar
from tkinter import StringVar, BooleanVar, simpledialog
from datetime import datetime

class CompraVenta:
    def __init__(self, parent, inventario,conn):
        self.parent = parent
        self.es_distribuidor = False  # Inicializar con un valor por defecto
        self.conn = conn
        self.inventario = inventario
        self.paciente_id = None
        self.cita_id = None
        self.fecha_cita = None
        self.create_widgets()
        self.conectar_db()
        self.actualizar_lista_pacientes()
        self.actualizar_lista_citas(None)
        self.estados_plantilla = {
            'PENDIENTE DE PAGO': 'Pendiente de pago',
            'PAGADA': 'Pagada'
        }

    def conectar_db(self):
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()
    
    def guardar_cobro(self):
        print("Método guardar_cobro llamado")
        
        if self.paciente_id is None or self.fecha_cita is None:
            messagebox.showwarning("Advertencia", "Error al obtener información del paciente.")
            return

        try:
            with sqlite3.connect('consultorioDB.db', timeout=20) as conn:
                cursor = conn.cursor()
                
                paciente_id_correcto = self.paciente_id
                print(f"Guardando cobros para paciente_id: {paciente_id_correcto}")

                # Recolectar todos los cobros actuales
                estado_actual_cobros = []
                for item in self.treeview_cobros.get_children():
                    valores = self.treeview_cobros.item(item)['values']
                    if len(valores) >= 3:
                        estado_actual_cobros.append((valores[0], valores[1], valores[2]))

                # Eliminar cobros existentes
                cursor.execute('DELETE FROM cobros WHERE paciente_id=? AND fecha=?', 
                            (paciente_id_correcto, self.fecha_cita))

                # Insertar nuevos cobros
                for descripcion, cantidad, total in estado_actual_cobros:
                    # Insertar cobro
                    cursor.execute('''
                        INSERT INTO cobros (paciente_id, fecha, descripcion, cantidad, total)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (paciente_id_correcto, self.fecha_cita, descripcion, cantidad, total))

                    # Actualizar plantillas en la misma conexión
                    cursor.execute('''
                        UPDATE plantillas 
                        SET cantidad_pagada = COALESCE(cantidad_pagada, 0) + ?,
                            estado = CASE 
                                WHEN COALESCE(cantidad_pagada, 0) + ? >= precio THEN ?
                                ELSE estado 
                            END
                        WHERE nombre = ? AND paciente_id = ?
                    ''', (float(total), float(total), self.estados_plantilla['PAGADA'], 
                        descripcion, paciente_id_correcto))

                    # Actualizar inventario
                    if descripcion != "Consulta":
                        cantidad_inicial = self.estado_inicial_cobros.get(descripcion, 0)
                        diferencia = int(cantidad) - int(cantidad_inicial)
                        
                        if diferencia != 0:
                            # Actualizar productos
                            cursor.execute('''
                                UPDATE productos
                                SET cantidad = cantidad - ?
                                WHERE nombre = ?
                            ''', (diferencia, descripcion))

                            # Actualizar materiales
                            cursor.execute('''
                                UPDATE materiales_cirugia
                                SET cantidad = cantidad - ?
                                WHERE nombre = ?
                            ''', (diferencia, descripcion))

                # Guardar cambios
                conn.commit()
                print("Cambios guardados exitosamente")

                # Actualizar estado inicial
                self.estado_inicial_cobros = {item[0]: item[1] for item in estado_actual_cobros}

                messagebox.showinfo("Éxito", "Cobro registrado exitosamente.")

                # Actualizar interfaces
                self.inventario.actualizar_lista_productos()
                self.inventario.actualizar_lista_materiales()

        except sqlite3.Error as e:
            print(f"Error de base de datos: {e}")
            messagebox.showerror("Error", f"Error en la base de datos: {str(e)}")
        except Exception as e:
            print(f"Error inesperado: {e}")
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
        finally:
            if self.ventana_cobro.winfo_exists():
                self.ventana_cobro.destroy()

        print("Función guardar_cobro completada")

    def crear_nuevo_paciente(self):
        # Crear una nueva ventana
        ventana_nuevo_paciente = ctk.CTkToplevel(self.ventana_cobro)
        ventana_nuevo_paciente.title("Nuevo Paciente")
        ventana_nuevo_paciente.geometry("300x200")

        # Crear y colocar los widgets
        frame = ctk.CTkFrame(ventana_nuevo_paciente)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Nombre:").pack(pady=(0, 5))
        entry_nombre = ctk.CTkEntry(frame)
        entry_nombre.pack(pady=(0, 10), fill="x")

        ctk.CTkLabel(frame, text="Teléfono:").pack(pady=(0, 5))
        entry_telefono = ctk.CTkEntry(frame)
        entry_telefono.pack(pady=(0, 10), fill="x")

        def guardar_paciente():
            nombre = entry_nombre.get()
            telefono = entry_telefono.get()

            if nombre and telefono:
                try:
                    conn = sqlite3.connect('consultorioDB.db')
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO pacientes (nombre, telefono) VALUES (?, ?)', (nombre, telefono))
                    conn.commit()
                    nuevo_id = cursor.lastrowid
                    conn.close()

                    messagebox.showinfo("Éxito", "Paciente guardado exitosamente.")
                    self.cargar_lista_pacientes()  # Actualizar la lista de pacientes
                    self.combo_pacientes.set(f"{nuevo_id} - {nombre}")  # Seleccionar el nuevo paciente
                    ventana_nuevo_paciente.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo guardar el paciente: {str(e)}")
            else:
                messagebox.showwarning("Advertencia", "Por favor, complete todos los campos.")

        boton_guardar = ctk.CTkButton(frame, text="Guardar", command=guardar_paciente)
        boton_guardar.pack(pady=10)

    def cargar_lista_pacientes(self):
        # Cargar la lista de pacientes en el combobox
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre FROM pacientes')
        pacientes = cursor.fetchall()
        conn.close()

        self.combo_pacientes['values'] = [f"{id} - {nombre}" for id, nombre in pacientes]

    def guardar_cobro_sin_cita(self):
        if self.paciente_id is None:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un paciente.")
            return

        fecha_actual = datetime.now().strftime('%Y-%m-%d')

        try:
            with sqlite3.connect('consultorioDB.db', timeout=20) as conn:
                cursor = conn.cursor()

                for item in self.treeview_cobros.get_children():
                    valores = self.treeview_cobros.item(item)["values"]
                    descripcion, cantidad, total = valores[0], int(valores[1]), float(valores[2])
                    
                    # Insertar el cobro
                    cursor.execute('''
                        INSERT INTO cobros (paciente_id, fecha, descripcion, cantidad, total)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (self.paciente_id, fecha_actual, descripcion, cantidad, total))
                    
                    print(f"Paciente ID correcto: {self.paciente_id}")

                    # Actualizar plantillas en la misma conexión
                    cursor.execute('''
                        UPDATE plantillas 
                        SET cantidad_pagada = COALESCE(cantidad_pagada, 0) + ?,
                            estado = CASE 
                                WHEN COALESCE(cantidad_pagada, 0) + ? >= precio THEN ?
                                ELSE estado 
                            END
                        WHERE nombre = ? AND paciente_id = ?
                    ''', (float(total), float(total), self.estados_plantilla['PAGADA'], 
                        descripcion, self.paciente_id))

                    # Actualizar el inventario de productos
                    cursor.execute('SELECT COUNT(*) FROM productos WHERE nombre = ?', (descripcion,))
                    if cursor.fetchone()[0] > 0:
                        cursor.execute('''
                            UPDATE productos
                            SET cantidad = cantidad - ?
                            WHERE nombre = ?
                        ''', (cantidad, descripcion))
                    else:
                        # Si no es un producto, verificar si es un material
                        cursor.execute('SELECT COUNT(*) FROM materiales_cirugia WHERE nombre = ?', (descripcion,))
                        if cursor.fetchone()[0] > 0:
                            cursor.execute('''
                                UPDATE materiales_cirugia
                                SET cantidad = cantidad - ?
                                WHERE nombre = ?
                            ''', (cantidad, descripcion))

                    print(f"Actualizando {descripcion}, cantidad: {cantidad}, filas afectadas: {cursor.rowcount}")

                conn.commit()
                print("Cambios guardados exitosamente")
                messagebox.showinfo("Éxito", "Cobro registrado exitosamente y el inventario ha sido actualizado.")

                # Actualizar las interfaces
                self.inventario.actualizar_lista_productos()
                self.inventario.actualizar_lista_materiales()

        except sqlite3.Error as e:
            print(f"Error de base de datos: {e}")
            messagebox.showerror("Error", f"Error en la base de datos: {str(e)}")
        except Exception as e:
            print(f"Error inesperado: {e}")
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
        finally:
            if self.ventana_cobro.winfo_exists():
                self.ventana_cobro.destroy()

        print("Función guardar_cobro_sin_cita completada")

    def filtrar_pacientes_cobro(self, event):
        filtro = self.entry_buscar_paciente.get()
        for row in self.treeview_pacientes.get_children():
            self.treeview_pacientes.delete(row)
        
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, telefono FROM pacientes WHERE nombre LIKE ?', ('%' + filtro + '%',))
        pacientes = cursor.fetchall()
        conn.close()
        
        if pacientes:
            for paciente in pacientes:
                self.treeview_pacientes.insert("", "end", values=(paciente[0], paciente[1], paciente[2]))
        else:
            self.treeview_pacientes.insert('', 'end', values=('', 'No se encontraron resultados', ''))

    def seleccionar_paciente_cobro(self, event):
        seleccionado = self.treeview_pacientes.selection()
        if seleccionado:
            paciente_id = self.treeview_pacientes.item(seleccionado[0])['values'][0]
            self.paciente_id = paciente_id

            # Obtener si el paciente es distribuidor
            es_distribuidor = self.treeview_pacientes.item(seleccionado[0])['values'][3]
            self.es_distribuidor = es_distribuidor == "Sí"

            # Actualizar la lista de productos con los precios correspondientes
            self.cargar_productos()

            # Cargar las plantillas del paciente
            self.cargar_plantillas_paciente()

    def actualizar_lista_pacientes_cobro(self):
        for row in self.treeview_pacientes.get_children():
            self.treeview_pacientes.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, telefono, es_distribuidor FROM pacientes')
        pacientes = cursor.fetchall()
        conn.close()
        for paciente in pacientes:
            es_distribuidor = "Sí" if paciente[3] else "No"
            self.treeview_pacientes.insert("", "end", values=(paciente[0], paciente[1], paciente[2], es_distribuidor))

    def cargar_productos(self):
        for row in self.treeview_productos.get_children():
            self.treeview_productos.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        if hasattr(self, 'es_distribuidor') and self.es_distribuidor:
            cursor.execute('SELECT id, nombre, marca, precio_distribuidor as precio, cantidad FROM productos')
        else:
            cursor.execute('SELECT id, nombre, marca, precio, cantidad FROM productos')
        productos = cursor.fetchall()
        conn.close()
        for producto in productos:
            self.treeview_productos.insert("", "end", values=(producto[0], producto[1], producto[2], producto[3], producto[4]))

    def abrir_ventana_cobro_sin_cita(self):
        self.ventana_cobro = ctk.CTkToplevel(self.parent)
        self.ventana_cobro.title("Cobro Sin Cita")
        self.ventana_cobro.geometry("1800x1100")

         # Frame para la fecha del cobro
        frame_fecha = ctk.CTkFrame(self.ventana_cobro)
        frame_fecha.pack(fill='x', padx=20, pady=10)

        ctk.CTkLabel(frame_fecha, 
                    text="Fecha del cobro:", 
                    font=("Arial", 12, "bold")
                    ).pack(side='left', padx=5)
        
        # Por defecto, usar la fecha actual
        self.fecha_cobro = datetime.now().strftime('%Y-%m-%d')
        
        # Mostrar la fecha en un label con estilo destacado
        self.label_fecha_cobro = ctk.CTkLabel(
            frame_fecha,
            text=self.fecha_cobro,
            font=("Arial", 12),
            fg_color="lightblue",  # Color de fondo para destacar
            corner_radius=6,
            padx=10,
            pady=5
        )
        self.label_fecha_cobro.pack(side='left', padx=10)

        # Botón para cambiar la fecha si es necesario
        def cambiar_fecha():
            # Crear un calendario emergente para seleccionar la fecha
            top = ctk.CTkToplevel(self.ventana_cobro)
            top.title("Seleccionar Fecha")
            
            cal = Calendar(top, selectmode='day', date_pattern='yyyy-mm-dd')
            cal.pack(padx=10, pady=10)
            
            def confirmar_fecha():
                nueva_fecha = cal.get_date()
                # Confirmar si la fecha no es hoy
                if nueva_fecha != datetime.now().strftime('%Y-%m-%d'):
                    if messagebox.askyesno("Confirmar", 
                        "¿Está seguro de registrar el cobro en una fecha diferente a hoy?"):
                        self.fecha_cobro = nueva_fecha
                        self.label_fecha_cobro.configure(text=nueva_fecha)
                top.destroy()

            ctk.CTkButton(top, text="Confirmar", command=confirmar_fecha).pack(pady=10)

        boton_cambiar_fecha = ctk.CTkButton(
            frame_fecha,
            text="Cambiar Fecha",
            command=cambiar_fecha,
            width=100
        )
        boton_cambiar_fecha.pack(side='left', padx=5)

        # Hacer la ventana modal
        self.ventana_cobro.grab_set()

        # Centrar la ventana en la pantalla
        self.ventana_cobro.update_idletasks()
        width = 1800
        height = 1100
        x = (self.ventana_cobro.winfo_screenwidth() // 2) - (width // 2)
        y = (self.ventana_cobro.winfo_screenheight() // 2) - (height // 2)
        self.ventana_cobro.geometry('{}x{}+{}+{}'.format(width, height, x, y))

         # Asegurar que la ventana esté por encima
        self.ventana_cobro.lift()
        self.ventana_cobro.focus_force()
        
        # Frame para la selección de paciente
        frame_paciente = ctk.CTkFrame(self.ventana_cobro)
        frame_paciente.pack(side="top", fill="x", padx=20, pady=20)

        label_buscar_paciente = ctk.CTkLabel(frame_paciente, text="Buscar Paciente:")
        label_buscar_paciente.pack(pady=(0, 5))
        self.entry_buscar_paciente = ctk.CTkEntry(frame_paciente)
        self.entry_buscar_paciente.pack(fill="x", pady=(0, 10))
        self.entry_buscar_paciente.bind("<KeyRelease>", self.filtrar_pacientes_cobro)

        self.treeview_pacientes = ttk.Treeview(frame_paciente, columns=("ID", "Nombre", "Teléfono", "Es Distribuidor"), show='headings', height=6)
        self.treeview_pacientes.heading("ID", text="ID")
        self.treeview_pacientes.heading("Nombre", text="Nombre")
        self.treeview_pacientes.heading("Teléfono", text="Teléfono")
        self.treeview_pacientes.heading("Es Distribuidor", text="Es Distribuidor")
        self.treeview_pacientes.pack(fill='x', pady=5, padx=5)
        self.treeview_pacientes.bind("<<TreeviewSelect>>", self.seleccionar_paciente_cobro)

        # Frame para los interruptores y buscadores
        frame_opciones = ctk.CTkFrame(self.ventana_cobro)
        frame_opciones.pack(side="left", fill="y", padx=20, pady=20)

        # Interruptor para mostrar/ocultar la lista de productos
        self.mostrar_productos_var = ctk.BooleanVar(value=False)
        switch_mostrar_productos = ctk.CTkSwitch(frame_opciones, text="Agregar Productos", variable=self.mostrar_productos_var, command=self.mostrar_ocultar_productos)
        switch_mostrar_productos.pack(pady=10)

        # Frame para la búsqueda y selección de productos
        self.frame_productos = ctk.CTkFrame(frame_opciones)
        self.frame_productos.pack(fill="both", expand=True, pady=10)

        frame_buscar_producto = ctk.CTkFrame(self.frame_productos)
        frame_buscar_producto.pack(fill="x", pady=5)

        label_buscar_producto = ctk.CTkLabel(frame_buscar_producto, text="Buscar Producto:")
        label_buscar_producto.pack(side="left", padx=5)
        self.entry_buscar_producto = ctk.CTkEntry(frame_buscar_producto)
        self.entry_buscar_producto.pack(side="left", padx=5, expand=True, fill="x")

        label_cantidad = ctk.CTkLabel(frame_buscar_producto, text="Cantidad:")
        label_cantidad.pack(side="left", padx=5)
        vcmd_cantidad = (self.parent.register(self.validar_cantidad), '%P')
        self.entry_cantidad_producto = ctk.CTkEntry(frame_buscar_producto, validate="key", validatecommand=vcmd_cantidad, width=50)
        self.entry_cantidad_producto.pack(side="left", padx=5)

        self.entry_buscar_producto.bind("<KeyRelease>", self.filtrar_productos)

        self.treeview_productos = ttk.Treeview(self.frame_productos, columns=("ID", "Nombre", "Marca", "Precio", "Cantidad Disponible"), show='headings')
        self.treeview_productos.heading("ID", text="ID")
        self.treeview_productos.heading("Nombre", text="Nombre")
        self.treeview_productos.heading("Marca", text="Marca")
        self.treeview_productos.heading("Precio", text="Precio")
        self.treeview_productos.heading("Cantidad Disponible", text="Cantidad Disponible")
        self.treeview_productos.pack(pady=5, fill="both", expand=True)

        boton_agregar_producto = ctk.CTkButton(frame_buscar_producto, text="Agregar", command=self.agregar_producto_cobro, width=80)
        boton_agregar_producto.pack(side="left", padx=5)

        # Ocultar el frame de productos al inicio
        self.frame_productos.pack_forget()

        # Interruptor para mostrar/ocultar la lista de materiales
        self.mostrar_materiales_var = ctk.BooleanVar(value=False)
        switch_mostrar_materiales = ctk.CTkSwitch(frame_opciones, text="Agregar Materiales", variable=self.mostrar_materiales_var, command=self.mostrar_ocultar_materiales)
        switch_mostrar_materiales.pack(pady=10)

        # Frame para la búsqueda y selección de materiales
        self.frame_materiales = ctk.CTkFrame(frame_opciones)
        self.frame_materiales.pack(fill="both", expand=True, pady=10)

        frame_buscar_material = ctk.CTkFrame(self.frame_materiales)
        frame_buscar_material.pack(fill="x", pady=5)

        label_buscar_material = ctk.CTkLabel(frame_buscar_material, text="Buscar Material:")
        label_buscar_material.pack(side="left", padx=5)
        self.entry_buscar_material = ctk.CTkEntry(frame_buscar_material)
        self.entry_buscar_material.pack(side="left", padx=5, expand=True, fill="x")

        label_cantidad_material = ctk.CTkLabel(frame_buscar_material, text="Cantidad:")
        label_cantidad_material.pack(side="left", padx=5)
        vcmd_cantidad_material = (self.parent.register(self.validar_cantidad), '%P')
        self.entry_cantidad_material = ctk.CTkEntry(frame_buscar_material, validate="key", validatecommand=vcmd_cantidad_material, width=50)
        self.entry_cantidad_material.pack(side="left", padx=5)

        self.entry_buscar_material.bind("<KeyRelease>", self.filtrar_materiales)

        self.treeview_materiales = ttk.Treeview(self.frame_materiales, columns=("ID", "Nombre", "Precio", "Cantidad Disponible"), show='headings')
        self.treeview_materiales.heading("ID", text="ID")
        self.treeview_materiales.heading("Nombre", text="Nombre")
        self.treeview_materiales.heading("Precio", text="Precio")
        self.treeview_materiales.heading("Cantidad Disponible", text="Cantidad Disponible")
        self.treeview_materiales.pack(pady=5, fill="both", expand=True)

        boton_agregar_material = ctk.CTkButton(frame_buscar_material, text="Agregar", command=self.agregar_material_cobro, width=80)
        boton_agregar_material.pack(side="left", padx=5)

        # Ocultar el frame de materiales al inicio
        self.frame_materiales.pack_forget()

        self.mostrar_plantillas_var = ctk.BooleanVar(value=False)
        switch_mostrar_plantillas = ctk.CTkSwitch(frame_opciones, text="Agregar Plantillas", variable=self.mostrar_plantillas_var, command=self.mostrar_ocultar_plantillas)
        switch_mostrar_plantillas.pack(pady=10)

        # Frame para la búsqueda y selección de plantillas
        self.frame_plantillas = ctk.CTkFrame(frame_opciones)
        self.frame_plantillas.pack(fill="both", expand=True, pady=10)

        frame_buscar_plantilla = ctk.CTkFrame(self.frame_plantillas)
        frame_buscar_plantilla.pack(fill="x", pady=5)

        label_buscar_plantilla = ctk.CTkLabel(frame_buscar_plantilla, text="Buscar Plantilla:")
        label_buscar_plantilla.pack(side="left", padx=5)
        self.entry_buscar_plantilla = ctk.CTkEntry(frame_buscar_plantilla)
        self.entry_buscar_plantilla.pack(side="left", padx=5, expand=True, fill="x")

        self.entry_buscar_plantilla.bind("<KeyRelease>", self.filtrar_plantillas)

        self.treeview_plantillas = ttk.Treeview(self.frame_plantillas, columns=("Nombre", "Cantidad Pagada", "Precio"), show='headings')
        self.treeview_plantillas.heading("Nombre", text="Nombre")
        self.treeview_plantillas.heading("Cantidad Pagada", text="Cantidad Pagada")
        self.treeview_plantillas.heading("Precio", text="Precio")
        self.treeview_plantillas.pack(pady=5, fill="both", expand=True)

        boton_agregar_plantilla = ctk.CTkButton(frame_buscar_plantilla, text="Agregar", command=self.agregar_plantilla_cobro, width=80)
        boton_agregar_plantilla.pack(side="right", padx=5)

        # Ocultar el frame de plantillas al inicio
        self.frame_plantillas.pack_forget()

        # Frame para la lista de cobros
        frame_cobros = ctk.CTkFrame(self.ventana_cobro)
        frame_cobros.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        label_cobros = ctk.CTkLabel(frame_cobros, text="Cobros:")
        label_cobros.pack(pady=5)

        self.treeview_cobros = ttk.Treeview(frame_cobros, columns=("Descripcion", "Cantidad", "Total"), show='headings')
        self.treeview_cobros.heading("Descripcion", text="Descripción")
        self.treeview_cobros.heading("Cantidad", text="Cantidad")
        self.treeview_cobros.heading("Total", text="Total")
        self.treeview_cobros.pack(fill="both", expand=True)

        self.treeview_cobros.bind("<Double-1>", self.eliminar_elemento_cobro)

        # Botón para eliminar un elemento de cobro
        boton_eliminar = ctk.CTkButton(frame_cobros, text="Eliminar Selección", command=self.eliminar_elemento_cobro)
        boton_eliminar.pack(pady=10)

        # Botón para guardar el cobro
        boton_guardar = ctk.CTkButton(frame_opciones, text="Guardar", command=self.guardar_cobro_sin_cita)
        boton_guardar.pack(pady=10)

        self.actualizar_lista_pacientes_cobro()

        # Asegurarse de liberar el control cuando se cierre la ventana
        self.ventana_cobro.protocol("WM_DELETE_WINDOW", self.cerrar_ventana_cobro)

    def cerrar_ventana_cobro(self):
        self.ventana_cobro.grab_release()
        self.ventana_cobro.destroy()

    def calcular_total(self, descripcion, cantidad):
        if descripcion == "Consulta":
            precio = 700  # Precio fijo para la consulta
        else:
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('SELECT precio FROM productos WHERE nombre = ? UNION SELECT precio FROM materiales_cirugia WHERE nombre = ?', (descripcion, descripcion))
            resultado = cursor.fetchone()
            conn.close()
            if resultado:
                precio = resultado[0]
            else:
                raise ValueError(f"No se encontró el precio para el producto/material: {descripcion}")
        return precio * cantidad

    def abrir_ventana_cobro(self):
        seleccionado = self.treeview_citas.selection()
        if not seleccionado:
            messagebox.showwarning("Advertencia", "Seleccione un paciente de la lista de citas para registrar el cobro.")
            return

        cita = self.treeview_citas.item(seleccionado[0])['values']
        cita_id = cita[0]  # ID de la cita
        
        # Obtener el paciente_id y es_distribuidor de la cita
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT pacientes.id, pacientes.es_distribuidor FROM citas JOIN pacientes ON citas.paciente_id = pacientes.id WHERE citas.id = ?', (cita_id,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            self.paciente_id, es_distribuidor = resultado
            self.es_distribuidor = bool(es_distribuidor)
        else:
            messagebox.showerror("Error", "No se pudo obtener la información del paciente.")
            return

        self.fecha_cita = cita[2]  # Asumiendo que la fecha es el tercer valor

        print(f"Abriendo ventana de cobro para paciente_id: {self.paciente_id}, fecha: {self.fecha_cita}, Es distribuidor: {self.es_distribuidor}")

        self.ventana_cobro = ctk.CTkToplevel(self.parent)
        self.ventana_cobro.title("Cobro de Paciente")
        self.ventana_cobro.geometry("1800x1100")

        # Frame para los interruptores y buscadores
        frame_opciones = ctk.CTkFrame(self.ventana_cobro)
        frame_opciones.pack(side="left", fill="y", padx=20, pady=20)

        # Interruptor para seleccionar si se va a cobrar la consulta
        self.cobro_consulta_var = BooleanVar(value=False)
        switch_cobro_consulta = ctk.CTkSwitch(frame_opciones, text="Cobrar Consulta", variable=self.cobro_consulta_var, onvalue=True, offvalue=False, command=self.actualizar_cobro_consulta)
        switch_cobro_consulta.pack(pady=10)

        # Interruptor para mostrar/ocultar la lista de productos
        self.mostrar_productos_var = BooleanVar(value=False)
        switch_mostrar_productos = ctk.CTkSwitch(frame_opciones, text="Agregar Productos", variable=self.mostrar_productos_var, onvalue=True, offvalue=False, command=self.mostrar_ocultar_productos)
        switch_mostrar_productos.pack(pady=10)

        # Frame para la búsqueda y selección de productos
        self.frame_productos = ctk.CTkFrame(frame_opciones)
        self.frame_productos.pack(fill="both", expand=True, pady=10)

        frame_buscar_producto = ctk.CTkFrame(self.frame_productos)
        frame_buscar_producto.pack(fill="x", pady=5)

        label_buscar_producto = ctk.CTkLabel(frame_buscar_producto, text="Buscar Producto:")
        label_buscar_producto.pack(side="left", padx=5)
        self.entry_buscar_producto = ctk.CTkEntry(frame_buscar_producto)
        self.entry_buscar_producto.pack(side="left", padx=5, expand=True, fill="x")

        label_cantidad = ctk.CTkLabel(frame_buscar_producto, text="Cantidad:")
        label_cantidad.pack(side="left", padx=5)
        vcmd_cantidad = (self.parent.register(self.validar_cantidad), '%P')
        self.entry_cantidad_producto = ctk.CTkEntry(frame_buscar_producto, validate="key", validatecommand=vcmd_cantidad, width=50)
        self.entry_cantidad_producto.pack(side="left", padx=5)

        self.entry_buscar_producto.bind("<KeyRelease>", self.filtrar_productos)

        self.treeview_productos = ttk.Treeview(self.frame_productos, columns=("ID", "Nombre", "Marca", "Precio", "Cantidad Disponible"), show='headings')
        self.treeview_productos.heading("ID", text="ID")
        self.treeview_productos.heading("Nombre", text="Nombre")
        self.treeview_productos.heading("Marca", text="Marca")
        self.treeview_productos.heading("Precio", text="Precio")
        self.treeview_productos.heading("Cantidad Disponible", text="Cantidad Disponible")
        self.treeview_productos.pack(pady=5, fill="both", expand=True)

        boton_agregar_producto = ctk.CTkButton(frame_buscar_producto, text="Agregar", command=self.agregar_producto_cobro, width=80)
        boton_agregar_producto.pack(side="left", padx=5)

        # Ocultar el frame de productos al inicio
        self.frame_productos.pack_forget()

        # Interruptor para mostrar/ocultar la lista de materiales
        self.mostrar_materiales_var = BooleanVar(value=False)
        switch_mostrar_materiales = ctk.CTkSwitch(frame_opciones, text="Agregar Materiales", variable=self.mostrar_materiales_var, onvalue=True, offvalue=False, command=self.mostrar_ocultar_materiales)
        switch_mostrar_materiales.pack(pady=10)

        # Frame para la búsqueda y selección de materiales
        self.frame_materiales = ctk.CTkFrame(frame_opciones)
        self.frame_materiales.pack(fill="both", expand=True, pady=10)

        frame_buscar_material = ctk.CTkFrame(self.frame_materiales)
        frame_buscar_material.pack(fill="x", pady=5)

        label_buscar_material = ctk.CTkLabel(frame_buscar_material, text="Buscar Material:")
        label_buscar_material.pack(side="left", padx=5)
        self.entry_buscar_material = ctk.CTkEntry(frame_buscar_material)
        self.entry_buscar_material.pack(side="left", padx=5, expand=True, fill="x")

        label_cantidad_material = ctk.CTkLabel(frame_buscar_material, text="Cantidad:")
        label_cantidad_material.pack(side="left", padx=5)
        vcmd_cantidad_material = (self.parent.register(self.validar_cantidad), '%P')
        self.entry_cantidad_material = ctk.CTkEntry(frame_buscar_material, validate="key", validatecommand=vcmd_cantidad_material, width=50)
        self.entry_cantidad_material.pack(side="left", padx=5)

        self.entry_buscar_material.bind("<KeyRelease>", self.filtrar_materiales)

        self.treeview_materiales = ttk.Treeview(self.frame_materiales, columns=("ID", "Nombre", "Precio", "Cantidad Disponible"), show='headings')
        self.treeview_materiales.heading("ID", text="ID")
        self.treeview_materiales.heading("Nombre", text="Nombre")
        self.treeview_materiales.heading("Precio", text="Precio")
        self.treeview_materiales.heading("Cantidad Disponible", text="Cantidad Disponible")
        self.treeview_materiales.pack(pady=5, fill="both", expand=True)

        boton_agregar_material = ctk.CTkButton(frame_buscar_material, text="Agregar", command=self.agregar_material_cobro, width=80)
        boton_agregar_material.pack(side="left", padx=5)

        # Ocultar el frame de materiales al inicio
        self.frame_materiales.pack_forget()

        # Interruptor para mostrar/ocultar la lista de plantillas
        self.mostrar_plantillas_var = ctk.BooleanVar(value=False)
        switch_mostrar_plantillas = ctk.CTkSwitch(frame_opciones, text="Agregar Plantillas", variable=self.mostrar_plantillas_var, command=self.mostrar_ocultar_plantillas)
        switch_mostrar_plantillas.pack(pady=10)

        # Frame para la búsqueda y selección de plantillas
        self.frame_plantillas = ctk.CTkFrame(frame_opciones)
        self.frame_plantillas.pack(fill="both", expand=True, pady=10)

        frame_buscar_plantilla = ctk.CTkFrame(self.frame_plantillas)
        frame_buscar_plantilla.pack(fill="x", pady=5)

        label_buscar_plantilla = ctk.CTkLabel(frame_buscar_plantilla, text="Buscar Plantilla:")
        label_buscar_plantilla.pack(side="left", padx=5)
        self.entry_buscar_plantilla = ctk.CTkEntry(frame_buscar_plantilla)
        self.entry_buscar_plantilla.pack(side="left", padx=5, expand=True, fill="x")

        self.entry_buscar_plantilla.bind("<KeyRelease>", self.filtrar_plantillas)

        self.treeview_plantillas = ttk.Treeview(self.frame_plantillas, columns=("Nombre", "Cantidad Pagada", "Precio"), show='headings')
        self.treeview_plantillas.heading("Nombre", text="Nombre")
        self.treeview_plantillas.heading("Cantidad Pagada", text="Cantidad Pagada")
        self.treeview_plantillas.heading("Precio", text="Precio")
        self.treeview_plantillas.pack(pady=5, fill="both", expand=True)

        boton_agregar_plantilla = ctk.CTkButton(frame_buscar_plantilla, text="Agregar", command=self.agregar_plantilla_cobro, width=80)
        boton_agregar_plantilla.pack(side="right", padx=5)

        # Ocultar el frame de plantillas al inicio
        self.frame_plantillas.pack_forget()

        # Frame para la lista de cobros
        frame_cobros = ctk.CTkFrame(self.ventana_cobro)
        frame_cobros.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        label_cobros = ctk.CTkLabel(frame_cobros, text="Cobros:")
        label_cobros.pack(pady=5)

        self.treeview_cobros = ttk.Treeview(frame_cobros, columns=("Descripcion", "Cantidad", "Total"), show='headings')
        self.treeview_cobros.heading("Descripcion", text="Descripción")
        self.treeview_cobros.heading("Cantidad", text="Cantidad")
        self.treeview_cobros.heading("Total", text="Total")
        self.treeview_cobros.pack(fill="both", expand=True)

        self.treeview_cobros.bind("<Double-1>", self.eliminar_elemento_cobro)

        # Botón para eliminar un elemento de cobro
        boton_eliminar = ctk.CTkButton(frame_cobros, text="Eliminar Selección", command=self.eliminar_elemento_cobro)
        boton_eliminar.pack(pady=10)

        # Botón para guardar el cobro
        boton_guardar = ctk.CTkButton(frame_opciones, text="Guardar", command=self.guardar_cobro)
        boton_guardar.pack(pady=10)

        # Guardar el estado inicial de los cobros
        self.cargar_cobros_existentes()

        # Actualizar la lista de productos con los precios correspondientes
        self.cargar_productos()

        # Actualizar el estado de los switches basado en los cobros existentes
        self.actualizar_switches_cobro()

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
        mensaje_ayuda = """Guía de Uso - Módulo de Compra/Venta

            ESTRUCTURA PRINCIPAL
            -------------------
            La ventana está dividida en dos secciones principales:
            • Izquierda: Agenda y gestión de citas
            • Derecha: Lista de citas del día seleccionado

            1. SECCIÓN DE BÚSQUEDA DE PACIENTES
            ---------------------------------
            Ubicada en la parte superior izquierda:
            • Campo "Buscar Paciente": Escriba el nombre para filtrar
            • Tabla de resultados: Muestra ID, Nombre y Teléfono
            • Seleccione un paciente haciendo clic en la tabla

            2. CALENDARIO Y SELECCIÓN DE FECHA
            -------------------------------
            Ubicado debajo de la búsqueda de pacientes:
            • Calendario mensual interactivo
            • Seleccione una fecha haciendo clic
            • Las fechas con citas se marcarán automáticamente
            • La fecha actual aparece resaltada

            3. CONFIGURACIÓN DE CITA
            ----------------------
            Ubicada debajo del calendario:
            • Selector de "Hora": Muestra horarios disponibles
            • Selector de "Confirmado": Opciones "Sí/No"
            • Solo se muestran horarios libres para la fecha seleccionada

            4. BOTONES DE GESTIÓN DE CITAS
            ----------------------------
            Primera fila de botones:
            • "Guardar Cita": Registra una nueva cita
            • "Actualizar Cita": Modifica cita seleccionada
            • "Eliminar Cita": Borra cita seleccionada
            • "Ayuda": Muestra esta guía

            Segunda fila de botones:
            • "Cobro Paciente": Registra cobro de cita (activo al seleccionar cita)
            • "Nuevo Cobro Sin Cita": Registra venta sin cita programada
            • "Gestionar Cobros": Administra y modifica cobros realizados

            5. LISTA DE CITAS
            ---------------
            Panel derecho:
            • Muestra todas las citas del día seleccionado
            • Columnas: ID, Paciente, Fecha, Hora, Confirmado
            • Doble clic: Carga datos de la cita para edición
            • Las citas confirmadas aparecen resaltadas en verde

            6. VENTANA DE COBRO
            -----------------
            Se activa con "Cobro Paciente" o "Nuevo Cobro Sin Cita":
            
            Panel Izquierdo:
            • Selección de productos/materiales/plantillas
            • Casillas para marcar ítems a cobrar
            • Campos para especificar cantidades

            Panel Derecho:
            • Lista de ítems agregados al cobro
            • Muestra subtotales y total
            • Doble clic elimina ítem de la lista

            7. GESTIÓN DE COBROS
            ------------------
            Accesible desde "Gestionar Cobros":
            • Selector de fecha: Filtra cobros por día
            • Búsqueda de paciente: Filtra por nombre
            • Tabla de cobros: Muestra todos los cobros del día
            • Opciones para modificar fecha o eliminar cobros
            • Total del día calculado automáticamente

            CONSEJOS Y ATAJOS
            ----------------
            • Para crear una cita:
            1. Busque y seleccione el paciente
            2. Elija fecha en el calendario
            3. Seleccione hora disponible
            4. Indique si está confirmada
            5. Presione "Guardar Cita"

            • Para realizar un cobro de cita:
            1. Seleccione la cita en la lista
            2. Presione "Cobro Paciente"
            3. Seleccione productos/servicios
            4. Verifique cantidades y total
            5. Guarde el cobro

            • Para ventas sin cita:
            1. Presione "Nuevo Cobro Sin Cita"
            2. Seleccione el paciente
            3. Agregue productos/servicios
            4. Verifique el total
            5. Guarde el cobro

            NOTAS IMPORTANTES
            ----------------
            • Los cobros actualizan automáticamente el inventario
            • Verifique los datos antes de guardar
            • Los cobros eliminados restauran el inventario
            • Las citas pueden reprogramarse seleccionándolas y usando "Actualizar Cita"
            • Use "Gestionar Cobros" para corregir errores en cobros realizados
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

    def cargar_cobros_existentes(self):
        print(f"Cargando cobros para paciente_id: {self.paciente_id}, fecha: {self.fecha_cita}")
        
        # Limpiar cobros existentes en el treeview
        for row in self.treeview_cobros.get_children():
            self.treeview_cobros.delete(row)
        
        try:
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            
            # Ya tenemos el paciente_id correcto en self.paciente_id, no necesitamos buscarlo
            cursor.execute('''
                SELECT descripcion, cantidad, total
                FROM cobros
                WHERE paciente_id = ? AND fecha = ?
            ''', (self.paciente_id, self.fecha_cita))
            
            cobros = cursor.fetchall()
            print(f"Cobros encontrados: {cobros}")
            
            for cobro in cobros:
                self.treeview_cobros.insert("", "end", values=cobro)
            
            self.estado_inicial_cobros = {cobro[0]: cobro[1] for cobro in cobros}
            print(f"Estado inicial de cobros: {self.estado_inicial_cobros}")
            
        except Exception as e:
            print(f"Error al cargar cobros: {str(e)}")
            messagebox.showerror("Error", f"Error al cargar cobros: {str(e)}")
        finally:
            conn.close()

        # Actualizar los switches basados en los cobros cargados
        self.actualizar_switches_cobro()

    def actualizar_switches_cobro(self):
        print("Actualizando switches de cobro")
        # Resetear todos los switches
        self.cobro_consulta_var.set(False)
        self.mostrar_productos_var.set(False)
        self.mostrar_materiales_var.set(False)
        self.mostrar_plantillas_var.set(False)  # Asegúrate de que esta variable existe

        for item in self.treeview_cobros.get_children():
            descripcion = self.treeview_cobros.item(item)["values"][0]
            print(f"Revisando item: {descripcion}")
            if descripcion == "Consulta":
                self.cobro_consulta_var.set(True)
                print("Activando switch de consulta")
            elif any(descripcion == self.treeview_productos.item(producto)["values"][1] for producto in self.treeview_productos.get_children()):
                self.mostrar_productos_var.set(True)
                print("Activando switch de productos")
            elif any(descripcion == self.treeview_materiales.item(material)["values"][1] for material in self.treeview_materiales.get_children()):
                self.mostrar_materiales_var.set(True)
                print("Activando switch de materiales")
            else:
                # Si no es producto ni material, asumimos que es una plantilla
                self.mostrar_plantillas_var.set(True)
                print("Activando switch de plantillas")

        # Actualizar la visibilidad de los frames
        self.mostrar_ocultar_productos()
        self.mostrar_ocultar_materiales()
        self.mostrar_ocultar_plantillas()

    def mostrar_ventana_precio_consulta(self, precio_inicial=700):
        ventana_precio = ctk.CTkToplevel(self.ventana_cobro)
        ventana_precio.title("Precio de Consulta")
        
        # Hacer la ventana modal
        ventana_precio.grab_set()
        
        # Variables para almacenar resultados
        resultado = {'precio': None, 'confirmar': False}
        
        # Frame principal 
        frame = ctk.CTkFrame(ventana_precio)
        frame.pack(padx=40, pady=40, fill="both", expand=True)
        
        # Frame para la información
        frame_info = ctk.CTkFrame(frame)
        frame_info.pack(pady=20, padx=20, fill="x")
        
        # Título e información
        ctk.CTkLabel(frame_info, 
                    text="Ajustar Precio de Consulta", 
                    font=("Arial", 20, "bold")
                    ).pack(pady=20)
        
        ctk.CTkLabel(frame_info, 
                    text=f"Precio sugerido: ${precio_inicial:.2f}", 
                    font=("Arial", 18)
                    ).pack(pady=20)
        
        # Frame para el nuevo precio
        frame_precio = ctk.CTkFrame(frame)
        frame_precio.pack(pady=20, fill="x", padx=20)
        
        ctk.CTkLabel(frame_precio, 
                    text="Nuevo precio: $", 
                    font=("Arial", 18)
                    ).pack(side="left", padx=20)
        
        entry_precio = ctk.CTkEntry(frame_precio, 
                                width=200,
                                height=40,
                                font=("Arial", 18))
        entry_precio.insert(0, str(precio_inicial))
        entry_precio.pack(side="left", padx=20)
        
        def confirmar():
            try:
                precio = float(entry_precio.get())
                resultado['precio'] = precio
                resultado['confirmar'] = True
                ventana_precio.destroy()
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese un precio válido")
        
        def cancelar():
            ventana_precio.destroy()
        
        # Frame para botones
        frame_botones = ctk.CTkFrame(frame)
        frame_botones.pack(pady=30)
        
        # Botones
        ctk.CTkButton(frame_botones, 
                    text="Confirmar", 
                    command=confirmar,
                    width=180,
                    height=50,
                    font=("Arial", 16)
                    ).pack(side="left", padx=20)
        
        ctk.CTkButton(frame_botones, 
                    text="Cancelar", 
                    command=cancelar,
                    width=180,
                    height=50,
                    font=("Arial", 16)
                    ).pack(side="left", padx=20)
        
        # Ajustar el tamaño de la ventana al contenido
        ventana_precio.update_idletasks()
        ventana_precio.pack_propagate(False)
        
        # Obtener el tamaño necesario del contenido
        required_width = frame.winfo_reqwidth() + 100
        required_height = frame.winfo_reqheight() + 100
        
        # Establecer un tamaño mínimo
        required_width = max(required_width, 700)
        required_height = max(required_height, 400)
        
        # Centrar la ventana en la pantalla
        x = (ventana_precio.winfo_screenwidth() // 2) - (required_width // 2)
        y = (ventana_precio.winfo_screenheight() // 2) - (required_height // 2)
        
        # Establecer el tamaño y posición final
        ventana_precio.geometry(f"{required_width}x{required_height}+{x}+{y}")
        
        ventana_precio.wait_window()
        return resultado

    def actualizar_cobro_consulta(self):
        if self.cobro_consulta_var.get():
            # Verificar si ya existe el cobro de la consulta en la lista
            for item in self.treeview_cobros.get_children():
                if self.treeview_cobros.item(item, "values")[0] == "Consulta":
                    messagebox.showwarning("Advertencia", "La consulta ya está agregada a la lista de cobros.")
                    self.cobro_consulta_var.set(False)
                    return
            
            # Mostrar la ventana personalizada para el precio de la consulta
            resultado = self.mostrar_ventana_precio_consulta()
            
            if resultado['confirmar'] and resultado['precio'] is not None:
                self.treeview_cobros.insert("", "end", values=("Consulta", 1, resultado['precio']))
            else:
                self.cobro_consulta_var.set(False)
        else:
            # Buscar y eliminar la fila que contiene "Consulta"
            for item in self.treeview_cobros.get_children():
                if self.treeview_cobros.item(item, "values")[0] == "Consulta":
                    self.treeview_cobros.delete(item)
                    break

    def mostrar_ocultar_productos(self):
        if self.mostrar_productos_var.get():
            self.frame_productos.pack(fill="both", expand=True, pady=10)
        else:
            self.frame_productos.pack_forget()

    def mostrar_ocultar_materiales(self):
        if self.mostrar_materiales_var.get():
            self.frame_materiales.pack(fill="both", expand=True, pady=10)
        else:
            self.frame_materiales.pack_forget()
    
    def mostrar_ocultar_plantillas(self):
        if self.mostrar_plantillas_var.get():
            self.frame_plantillas.pack(fill="both", expand=True, pady=10)
            self.cargar_plantillas_paciente()
        else:
            self.frame_plantillas.pack_forget()

    def cargar_plantillas_paciente(self):
        print(f"Cargando plantillas para paciente ID: {self.paciente_id}")
        for row in self.treeview_plantillas.get_children():
            self.treeview_plantillas.delete(row)
        
        if self.paciente_id:
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nombre, cantidad_pagada, precio
                FROM plantillas
                WHERE paciente_id = ? AND estado != ?
            ''', (self.paciente_id, self.estados_plantilla['PAGADA']))
            plantillas = cursor.fetchall()
            conn.close()

            print(f"Plantillas encontradas: {plantillas}")
            for plantilla in plantillas:
                nombre = plantilla[0]
                cantidad_pagada = plantilla[1]
                precio = plantilla[2]
                monto_pendiente = precio - cantidad_pagada
                estado = self.estados_plantilla['PAGADA'] if monto_pendiente <= 0 else self.estados_plantilla['PENDIENTE DE PAGO']
                
                # Insertar en el treeview con el formato: [nombre, cantidad_pagada, precio, estado]
                self.treeview_plantillas.insert("", "end", values=(nombre, cantidad_pagada, precio, estado))
        else:
            print("No hay paciente seleccionado")



    def filtrar_productos(self, event):
        filtro = self.entry_buscar_producto.get()
        for row in self.treeview_productos.get_children():
            self.treeview_productos.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        if self.es_distribuidor:
            cursor.execute('SELECT id, nombre, marca, precio_distribuidor as precio, cantidad FROM productos WHERE nombre LIKE ?', ('%' + filtro + '%',))
        else:
            cursor.execute('SELECT id, nombre, marca, precio, cantidad FROM productos WHERE nombre LIKE ?', ('%' + filtro + '%',))
        productos = cursor.fetchall()
        conn.close()
        for producto in productos:
            self.treeview_productos.insert("", "end", values=(producto[0], producto[1], producto[2], producto[3], producto[4]))

    def filtrar_plantillas(self, event):
        filtro = self.entry_buscar_plantilla.get().lower()
        print(f"Filtrando plantillas con: {filtro}")
        
        for row in self.treeview_plantillas.get_children():
            self.treeview_plantillas.delete(row)
        
        if self.paciente_id:
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nombre, cantidad_pagada, precio
                FROM plantillas
                WHERE paciente_id = ? AND estado != 'Entregada' AND LOWER(nombre) LIKE ?
            ''', (self.paciente_id, f'%{filtro}%'))
            plantillas = cursor.fetchall()
            conn.close()

            print(f"Plantillas encontradas: {plantillas}")
            for plantilla in plantillas:
                self.treeview_plantillas.insert("", "end", values=plantilla)
        else:
            print("No hay paciente seleccionado")

    def agregar_producto_cobro(self):
        seleccionado = self.treeview_productos.selection()
        if seleccionado and self.entry_cantidad_producto.get().isdigit():
            producto_id = self.treeview_productos.item(seleccionado[0])['values'][0]
            nombre_producto = self.treeview_productos.item(seleccionado[0])['values'][1]
            precio_producto = self.treeview_productos.item(seleccionado[0])['values'][3]
            cantidad_disponible = self.treeview_productos.item(seleccionado[0])['values'][4]
            cantidad = int(self.entry_cantidad_producto.get())

            if cantidad > int(cantidad_disponible):
                messagebox.showwarning("Advertencia", f"La cantidad solicitada supera la cantidad disponible en inventario. Solo hay {cantidad_disponible} disponibles.")
                return

            # Mostrar ventana de ajuste de precio
            resultado = self.mostrar_ventana_ajuste_precio(nombre_producto, float(precio_producto), cantidad)
            
            if resultado['confirmar'] and resultado['precio'] is not None:
                precio_ajustado = resultado['precio']
                total = precio_ajustado * cantidad

                # Verificar si el producto ya está en la lista de cobros
                for item in self.treeview_cobros.get_children():
                    if self.treeview_cobros.item(item, "values")[0] == nombre_producto:
                        cantidad_actual = int(self.treeview_cobros.item(item, "values")[1])
                        nueva_cantidad = cantidad_actual + cantidad
                        nuevo_total = precio_ajustado * nueva_cantidad
                        self.treeview_cobros.item(item, values=(nombre_producto, nueva_cantidad, nuevo_total))
                        return

                # Si el producto no está en la lista, agregarlo
                self.treeview_cobros.insert("", "end", values=(nombre_producto, cantidad, total))
        else:
            messagebox.showwarning("Advertencia", "Seleccione un producto y asegúrese de que la cantidad sea un número entero.")

    def mostrar_ventana_ajuste_precio(self, nombre_producto, precio_actual, cantidad):
        ventana_ajuste = ctk.CTkToplevel(self.ventana_cobro)
        ventana_ajuste.title(f"Ajustar Precio - {nombre_producto}")
        
        # Hacer la ventana modal
        ventana_ajuste.grab_set()
        
        # Variables para almacenar resultados
        resultado = {'precio': None, 'confirmar': False}
        
        # Frame principal 
        frame = ctk.CTkFrame(ventana_ajuste)
        frame.pack(padx=40, pady=40, fill="both", expand=True)
        
        # Frame para la información del producto
        frame_info = ctk.CTkFrame(frame)
        frame_info.pack(pady=20, padx=20, fill="x")
        
        # Información del producto con fuentes más grandes
        ctk.CTkLabel(frame_info, 
                    text=f"Producto: {nombre_producto}", 
                    font=("Arial", 20, "bold")
                    ).pack(pady=20)
        
        ctk.CTkLabel(frame_info, 
                    text=f"Precio actual: ${precio_actual:.2f}", 
                    font=("Arial", 18)
                    ).pack(pady=20)
        
        ctk.CTkLabel(frame_info, 
                    text=f"Cantidad: {cantidad}", 
                    font=("Arial", 18)
                    ).pack(pady=20)
        
        # Frame para el nuevo precio
        frame_precio = ctk.CTkFrame(frame)
        frame_precio.pack(pady=20, fill="x", padx=20)
        
        ctk.CTkLabel(frame_precio, 
                    text="Nuevo precio unitario: $", 
                    font=("Arial", 18)
                    ).pack(side="left", padx=20)
        
        entry_precio = ctk.CTkEntry(frame_precio, 
                                width=200,
                                height=40,
                                font=("Arial", 18))
        entry_precio.insert(0, str(precio_actual))
        entry_precio.pack(side="left", padx=20)
        
        # Frame para el total
        frame_total = ctk.CTkFrame(frame)
        frame_total.pack(pady=20, fill="x", padx=20)
        
        label_total = ctk.CTkLabel(frame_total, 
                                text=f"Total: ${precio_actual * cantidad:.2f}",
                                font=("Arial", 20, "bold"))
        label_total.pack(pady=20)
        
        def actualizar_total(*args):
            try:
                nuevo_precio = float(entry_precio.get())
                label_total.configure(text=f"Total: ${nuevo_precio * cantidad:.2f}")
            except ValueError:
                label_total.configure(text="Total: $0.00")
        
        entry_precio.bind('<KeyRelease>', actualizar_total)
        
        def confirmar():
            try:
                resultado['precio'] = float(entry_precio.get())
                resultado['confirmar'] = True
                ventana_ajuste.destroy()
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese un precio válido")
        
        def cancelar():
            ventana_ajuste.destroy()
        
        # Frame para botones
        frame_botones = ctk.CTkFrame(frame)
        frame_botones.pack(pady=30)
        
        # Botones más grandes
        ctk.CTkButton(frame_botones, 
                    text="Confirmar", 
                    command=confirmar,
                    width=180,
                    height=50,
                    font=("Arial", 16)
                    ).pack(side="left", padx=20)
        
        ctk.CTkButton(frame_botones, 
                    text="Cancelar", 
                    command=cancelar,
                    width=180,
                    height=50,
                    font=("Arial", 16)
                    ).pack(side="left", padx=20)
        
        # Ajustar el tamaño de la ventana al contenido
        ventana_ajuste.update_idletasks()
        ventana_ajuste.pack_propagate(False)
        
        # Obtener el tamaño necesario del contenido
        required_width = frame.winfo_reqwidth() + 100  # Agregar padding extra
        required_height = frame.winfo_reqheight() + 100
        
        # Establecer un tamaño mínimo
        required_width = max(required_width, 800)  # Ancho mínimo
        required_height = max(required_height, 600)  # Alto mínimo
        
        # Centrar la ventana en la pantalla
        x = (ventana_ajuste.winfo_screenwidth() // 2) - (required_width // 2)
        y = (ventana_ajuste.winfo_screenheight() // 2) - (required_height // 2)
        
        # Establecer el tamaño y posición final
        ventana_ajuste.geometry(f"{required_width}x{required_height}+{x}+{y}")
        
        ventana_ajuste.wait_window()
        return resultado

    def agregar_plantilla_cobro(self):
        seleccionado = self.treeview_plantillas.selection()
        if seleccionado:
            valores = self.treeview_plantillas.item(seleccionado[0])['values']
            print(f"Valores de la plantilla seleccionada: {valores}")
            
            if len(valores) < 3:
                print(f"Error: No hay suficientes valores. Valores disponibles: {valores}")
                messagebox.showerror("Error", "No se pudo obtener la información completa de la plantilla.")
                return

            try:
                nombre_plantilla = valores[0]
                cantidad_pagada = float(valores[1])
                precio_total = float(valores[2])
                
                monto_pendiente = precio_total - cantidad_pagada
                
                # Mostrar ventana para ingresar la cantidad a pagar
                cantidad_a_pagar = self.mostrar_ventana_pago(nombre_plantilla, monto_pendiente)
                
                if cantidad_a_pagar is not None:
                    nueva_cantidad_pagada = cantidad_pagada + cantidad_a_pagar
                    
                    # Usar with para manejar la conexión
                    try:
                        with sqlite3.connect('consultorioDB.db', timeout=20) as conn:
                            cursor = conn.cursor()
                            
                            # Agregar al treeview de cobros
                            self.treeview_cobros.insert("", "end", values=(nombre_plantilla, 1, cantidad_a_pagar))
                            
                            # Actualizar la cantidad pagada en la base de datos
                            cursor.execute('''
                                UPDATE plantillas
                                SET cantidad_pagada = ?
                                WHERE nombre = ? AND paciente_id = ?
                            ''', (nueva_cantidad_pagada, nombre_plantilla, self.paciente_id))
                            
                            # Verificar si la plantilla está completamente pagada
                            if nueva_cantidad_pagada >= precio_total:
                                cursor.execute('''
                                    UPDATE plantillas
                                    SET estado = ?
                                    WHERE nombre = ? AND paciente_id = ?
                                ''', (self.estados_plantilla['PAGADA'], nombre_plantilla, self.paciente_id))
                            
                            conn.commit()
                            
                    except sqlite3.Error as e:
                        print(f"Error de base de datos: {e}")
                        messagebox.showerror("Error", f"Error al acceder a la base de datos: {e}")
                        return
                        
            except ValueError as e:
                print(f"Error al procesar valores: {e}")
                messagebox.showerror("Error", "Error al procesar la información de la plantilla.")
            except Exception as e:
                print(f"Error inesperado: {e}")
                messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")
        else:
            messagebox.showwarning("Advertencia", "Por favor, seleccione una plantilla.")

    def mostrar_ventana_pago(self, nombre_plantilla, monto_pendiente):
        ventana_pago = ctk.CTkToplevel(self.ventana_cobro)
        ventana_pago.title(f"Pago para {nombre_plantilla}")
        ventana_pago.geometry("300x150")
        
        label = ctk.CTkLabel(ventana_pago, text=f"Monto pendiente: ${monto_pendiente:.2f}")
        label.pack(pady=10)
        
        entry = ctk.CTkEntry(ventana_pago)
        entry.pack(pady=10)
        
        cantidad_a_pagar = None
        
        def confirmar_pago():
            nonlocal cantidad_a_pagar
            try:
                cantidad = float(entry.get())
                if 0 < cantidad <= monto_pendiente:
                    cantidad_a_pagar = cantidad
                    ventana_pago.destroy()
                else:
                    messagebox.showwarning("Advertencia", "El monto debe ser mayor a 0 y no exceder el monto pendiente.")
            except ValueError:
                messagebox.showwarning("Advertencia", "Por favor, ingrese un número válido.")
        
        boton_confirmar = ctk.CTkButton(ventana_pago, text="Confirmar", command=confirmar_pago)
        boton_confirmar.pack(pady=10)
        
        ventana_pago.wait_window()
        return cantidad_a_pagar

    def actualizar_cantidad_pagada_plantilla(self, nombre_plantilla, nueva_cantidad_pagada):
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE plantillas
            SET cantidad_pagada = ?
            WHERE nombre = ? AND paciente_id = ?
        ''', (nueva_cantidad_pagada, nombre_plantilla, self.paciente_id))
        conn.commit()
        conn.close()

    def actualizar_estado_plantilla(self, nombre_plantilla, nuevo_estado):
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE plantillas
            SET estado = ?
            WHERE nombre = ? AND paciente_id = ?
        ''', (nuevo_estado, nombre_plantilla, self.paciente_id))
        conn.commit()
        conn.close()

    def filtrar_materiales(self, event):
        filtro = self.entry_buscar_material.get()
        for row in self.treeview_materiales.get_children():
            self.treeview_materiales.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, precio, cantidad FROM materiales_cirugia WHERE nombre LIKE ?', ('%' + filtro + '%',))
        materiales = cursor.fetchall()
        conn.close()
        for material in materiales:
            self.treeview_materiales.insert("", "end", values=(material[0], material[1], material[2], material[3]))

    def agregar_material_cobro(self):
        seleccionado = self.treeview_materiales.selection()
        if seleccionado and self.entry_cantidad_material.get().isdigit():
            material_id = self.treeview_materiales.item(seleccionado[0])['values'][0]
            nombre_material = self.treeview_materiales.item(seleccionado[0])['values'][1]
            precio_material = self.treeview_materiales.item(seleccionado[0])['values'][2]
            cantidad_disponible = self.treeview_materiales.item(seleccionado[0])['values'][3]
            cantidad = int(self.entry_cantidad_material.get())

            if cantidad > int(cantidad_disponible):
                messagebox.showwarning("Advertencia", f"La cantidad solicitada supera la cantidad disponible en inventario. Solo hay {cantidad_disponible} disponibles.")
                return

            total = float(precio_material) * cantidad

            # Verificar si el material ya está en la lista de cobros
            for item in self.treeview_cobros.get_children():
                if self.treeview_cobros.item(item, "values")[0] == nombre_material:
                    cantidad_actual = int(self.treeview_cobros.item(item, "values")[1])
                    nueva_cantidad = cantidad_actual + cantidad
                    nuevo_total = float(precio_material) * nueva_cantidad
                    self.treeview_cobros.item(item, values=(nombre_material, nueva_cantidad, nuevo_total))
                    return

            # Si el material no está en la lista, agregarlo
            self.treeview_cobros.insert("", "end", values=(nombre_material, cantidad, total))
        else:
            messagebox.showwarning("Advertencia", "Seleccione un material y asegúrese de que la cantidad sea un número entero.")

    def eliminar_elemento_cobro(self, event=None):
        seleccionado = self.treeview_cobros.selection()
        if seleccionado:
            item = seleccionado[0]
            descripcion, cantidad, _ = self.treeview_cobros.item(item, "values")
            
            # Eliminar el elemento de la lista de cobros
            self.treeview_cobros.delete(item)
            
            # Eliminar el elemento de la tabla cobros en la base de datos
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cobros WHERE paciente_id=? AND fecha=? AND descripcion=? AND cantidad=?',
                           (self.paciente_id, self.fecha_cita, descripcion, cantidad))
            conn.commit()
            conn.close()

    def validar_cantidad(self, text):
        return text.isdigit() or text == ""

    def create_widgets(self):
        # Frame principal que contiene todos los elementos
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Frame izquierdo para la agenda
        frame_agenda = ctk.CTkFrame(main_frame)
        frame_agenda.pack(side='left', fill='both', expand=True, padx=(0, 5), pady=5)

        label_agenda = ctk.CTkLabel(frame_agenda, text="Agenda de Citas")
        label_agenda.pack(pady=5)

        # Frame para búsqueda y lista de pacientes
        self.frame_pacientes = ctk.CTkFrame(frame_agenda)
        self.frame_pacientes.pack(fill='x', pady=5)

        label_buscar_paciente = ctk.CTkLabel(self.frame_pacientes, text="Buscar Paciente:")
        label_buscar_paciente.pack(side='left', padx=5)
        self.entry_buscar_paciente = ctk.CTkEntry(self.frame_pacientes)
        self.entry_buscar_paciente.pack(side='left', expand=True, fill='x', padx=5)
        self.entry_buscar_paciente.bind("<KeyRelease>", self.filtrar_pacientes)

        self.treeview_pacientes = ttk.Treeview(frame_agenda, columns=("ID", "Nombre", "Teléfono"), show='headings', height=6)
        self.treeview_pacientes.heading("ID", text="ID")
        self.treeview_pacientes.heading("Nombre", text="Nombre")
        self.treeview_pacientes.heading("Teléfono", text="Teléfono")
        self.treeview_pacientes.pack(fill='x', pady=5, padx=5)

        # Frame para fecha y hora
        frame_fecha_hora = ctk.CTkFrame(frame_agenda)
        frame_fecha_hora.pack(fill='x', pady=5)

        label_fecha = ctk.CTkLabel(frame_fecha_hora, text="Fecha:")
        label_fecha.pack(side='left', padx=5)
        self.calendario = Calendar(frame_fecha_hora, selectmode='day', date_pattern='yyyy-mm-dd', locale='es', font="Arial 10", selectbackground='blue', width=200, height=200)
        self.calendario.pack(side='left', pady=5, padx=5)
        self.calendario.bind("<<CalendarSelected>>", self.on_calendar_select)

        frame_hora_confirmado = ctk.CTkFrame(frame_agenda)
        frame_hora_confirmado.pack(fill='x', pady=5)

        label_hora = ctk.CTkLabel(frame_hora_confirmado, text="Hora:")
        label_hora.pack(side='left', padx=5)
        self.combo_hora = ttk.Combobox(frame_hora_confirmado, state='readonly', width=10)
        self.combo_hora.pack(side='left', padx=5)

        label_confirmado = ctk.CTkLabel(frame_hora_confirmado, text="Confirmado:")
        label_confirmado.pack(side='left', padx=5)
        self.confirmado_var = StringVar(value="No")
        self.option_confirmado = ttk.Combobox(frame_hora_confirmado, textvariable=self.confirmado_var, values=["Sí", "No"], state='readonly', width=5)
        self.option_confirmado.pack(side='left', padx=5)

        # Frame para botones
        frame_botones = ctk.CTkFrame(frame_agenda)
        frame_botones.pack(fill='x', pady=10)

        boton_guardar_cita = ctk.CTkButton(frame_botones, text="Guardar Cita", command=self.guardar_cita, width=20)
        boton_guardar_cita.pack(side='left', padx=5, expand=True, fill='x')

        boton_actualizar_cita = ctk.CTkButton(frame_botones, text="Actualizar Cita", command=self.actualizar_cita, width=20)
        boton_actualizar_cita.pack(side='left', padx=5, expand=True, fill='x')

        boton_eliminar_cita = ctk.CTkButton(frame_botones, text="Eliminar Cita", command=self.eliminar_cita, width=20)
        boton_eliminar_cita.pack(side='left', padx=5, expand=True, fill='x')
        
        boton_ayuda = ctk.CTkButton(frame_botones, text="Ayuda", command=self.mostrar_ayuda, width=20)
        boton_ayuda.pack(side='left', padx=5, expand=True, fill='x')    

        self.boton_cobro_cita = ctk.CTkButton(frame_agenda, text="Cobro Paciente", state="disabled", command=self.cobro_pacientes, width=20)
        self.boton_cobro_cita.pack(pady=(10,5), padx=5, fill='x')

        # Frame derecho para la lista de citas
        frame_lista_citas = ctk.CTkFrame(main_frame)
        frame_lista_citas.pack(side='right', fill='both', expand=True, padx=(5, 0), pady=5)

        # Añadir el nuevo botón para cobro sin cita justo después del botón de cobro de paciente
        self.boton_cobro_sin_cita = ctk.CTkButton(frame_agenda, text="Nuevo Cobro Sin Cita", state="disabled", command=self.abrir_ventana_cobro_sin_cita, width=20)
        self.boton_cobro_sin_cita.pack(pady=(0,10), padx=5, fill='x')

        # En el método create_widgets de CompraVenta
        self.boton_gestion_cobros = ctk.CTkButton(
            frame_botones, 
            text="Gestionar Cobros", 
            command=self.mostrar_gestion_cobros
        )
        self.boton_gestion_cobros.pack(pady=(0,10), padx=5, fill='x')

        label_lista_citas = ctk.CTkLabel(frame_lista_citas, text="Lista de Citas:")
        label_lista_citas.pack(pady=5)
        self.treeview_citas = ttk.Treeview(frame_lista_citas, columns=("ID", "Paciente", "Fecha", "Hora", "Confirmado"), show='headings')
        self.treeview_citas.heading("ID", text="ID")
        self.treeview_citas.heading("Paciente", text="Paciente")
        self.treeview_citas.heading("Fecha", text="Fecha")
        self.treeview_citas.heading("Hora", text="Hora")
        self.treeview_citas.heading("Confirmado", text="Confirmado")
        self.treeview_citas.pack(pady=5, fill='both', expand=True)
        self.treeview_citas.bind("<Double-1>", self.cargar_datos_cita)
        self.treeview_citas.bind("<<TreeviewSelect>>", self.habilitar_boton_cobro)

    def filtrar_pacientes(self, event):
        filtro = self.entry_buscar_paciente.get().lower()  # Convertir a minúsculas para búsqueda insensible
        
        try:
            for row in self.treeview_pacientes.get_children():
                self.treeview_pacientes.delete(row)
                
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nombre, telefono 
                FROM pacientes 
                WHERE LOWER(nombre) LIKE ? OR LOWER(telefono) LIKE ?
            ''', (f'%{filtro}%', f'%{filtro}%'))
            pacientes = cursor.fetchall()
            conn.close()
            
            for paciente in pacientes:
                self.treeview_pacientes.insert("", END, values=paciente)
                
        except Exception as e:
            print(f"Error al filtrar pacientes: {e}")
            # Intentar recuperar la lista completa en caso de error
            self.actualizar_lista_pacientes()

    def cobro_pacientes(self, event=None):
        self.abrir_ventana_cobro()

    def on_calendar_select(self, event):
        self.actualizar_horas_disponibles(event)
        self.habilitar_boton_cobro_sin_cita(event)

    def actualizar_horas_disponibles(self, event=None):
        fecha = self.calendario.get_date()
        self.actualizar_lista_citas(fecha)
        horas_disponibles = [
            "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
            "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30",
            "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"
        ]
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT hora FROM citas WHERE fecha=?', (fecha,))
        horas_ocupadas = cursor.fetchall()
        conn.close()

        horas_ocupadas = [hora[0] for hora in horas_ocupadas]
        horas_filtradas = [hora for hora in horas_disponibles if hora not in horas_ocupadas]

        self.combo_hora['values'] = horas_filtradas
        if horas_filtradas:
            self.combo_hora.current(0)
        else:
            self.combo_hora.set('')

    def habilitar_boton_cobro(self, event):
        seleccionado = self.treeview_citas.selection()
        if seleccionado:
            self.boton_cobro_cita.configure(state="normal")
        else:
            self.boton_cobro_cita.configure(state="disabled")

    def habilitar_boton_cobro_sin_cita(self,event):
        fecha_seleccionada = self.calendario.get_date()
        if fecha_seleccionada:
            self.boton_cobro_sin_cita.configure(state="normal")
        else:
            self.boton_cobro_sin_cita.configure(state="disabled")

    def cargar_datos_cita(self, event):
        seleccionado = self.treeview_citas.selection()
        if seleccionado:
            cita_id = self.treeview_citas.item(seleccionado[0])['values'][0]
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('SELECT paciente_id, fecha, hora, confirmado FROM citas WHERE id=?', (cita_id,))
            cita = cursor.fetchone()
            conn.close()
            if cita:
                self.actualizar_lista_pacientes()
                self.calendario.selection_set(cita[1])
                self.combo_hora.set(cita[2])
                self.confirmado_var.set(cita[3])

    def guardar_cita(self):
        try:
            if not self.treeview_pacientes.winfo_exists():
                self.actualizar_lista_pacientes()  

            seleccionado = self.treeview_pacientes.selection()
            if seleccionado:
                paciente_id = self.treeview_pacientes.item(seleccionado[0])['values'][0]
                fecha = self.calendario.get_date()  # Guardar la fecha seleccionada
                hora = self.combo_hora.get()
                confirmado = self.confirmado_var.get()

                if paciente_id and fecha and hora:
                    try:
                        conn = sqlite3.connect('consultorioDB.db')
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO citas (paciente_id, fecha, hora, confirmado)
                            VALUES (?, ?, ?, ?)
                        ''', (paciente_id, fecha, hora, confirmado))
                        conn.commit()
                        conn.close()
                        messagebox.showinfo("Éxito", "Cita guardada exitosamente.")
                        self.limpiar_campos_cita()
                        
                        # Mantener la fecha seleccionada y actualizar las listas
                        self.calendario.selection_set(fecha)  # Mantener la fecha seleccionada
                        self.actualizar_lista_citas(fecha)   # Actualizar la lista de citas
                        self.actualizar_horas_disponibles()  # Actualizar horas disponibles
                        
                    except Exception as e:
                        messagebox.showerror("Error", str(e))
                else:
                    messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
            else:
                messagebox.showwarning("Advertencia", "Seleccione un paciente para agendar la cita.")
        except Exception as e:
            print(f"Error al guardar cita: {e}")
            messagebox.showerror("Error", "Ocurrió un error al guardar la cita. Por favor, intente nuevamente.")

    def mostrar_ventana_actualizar_cita(self, cita_actual):
        ventana_actualizar = ctk.CTkToplevel(self.parent)
        ventana_actualizar.title("Actualizar Cita")
        
        # Hacer la ventana modal
        ventana_actualizar.grab_set()
        
        # Variables para almacenar resultados
        resultado = {
            'confirmar': False,
            'fecha': None,
            'hora': None,
            'confirmado': None
        }
        
        # Frame principal 
        frame = ctk.CTkFrame(ventana_actualizar)
        frame.pack(padx=40, pady=40, fill="both", expand=True)
        
        # Título
        ctk.CTkLabel(frame, 
                    text="Actualizar Cita", 
                    font=("Arial", 24, "bold")
                    ).pack(pady=20)
        
        # Información del paciente
        frame_info = ctk.CTkFrame(frame)
        frame_info.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(frame_info, 
                    text=f"Paciente: {cita_actual['paciente']}", 
                    font=("Arial", 18)
                    ).pack(pady=10)
        
        # Frame para fecha
        frame_fecha = ctk.CTkFrame(frame)
        frame_fecha.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(frame_fecha, 
                    text="Fecha:", 
                    font=("Arial", 16)
                    ).pack(side="left", padx=20)
        
        calendario = Calendar(frame_fecha, 
                            selectmode='day', 
                            date_pattern='yyyy-mm-dd',
                            locale='es',
                            font="Arial 12",
                            selectbackground='blue',
                            width=300,
                            height=200)
        calendario.pack(pady=10)
        calendario.selection_set(cita_actual['fecha'])  # Establecer fecha actual
        
        frame_hora = ctk.CTkFrame(frame)
        frame_hora.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(frame_hora, 
                    text="Hora:", 
                    font=("Arial", 16)
                    ).pack(side="left", padx=20)
        
        # Obtener horas disponibles para la fecha actual
        horas_disponibles = self.obtener_horas_disponibles(cita_actual['fecha'], cita_actual['id'])
        
        # Asegurarse de que la hora actual de la cita esté en la lista
        if cita_actual['hora'] not in horas_disponibles:
            horas_disponibles.append(cita_actual['hora'])
            horas_disponibles.sort()
        
        combo_hora = ttk.Combobox(frame_hora, 
                                values=horas_disponibles, 
                                state='readonly',
                                width=20)
        combo_hora.set(cita_actual['hora'])
        combo_hora.pack(side="left", padx=20)

        # Frame para confirmado
        frame_confirmado = ctk.CTkFrame(frame)
        frame_confirmado.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(frame_confirmado, 
                    text="¿Cita confirmada?:", 
                    font=("Arial", 16)
                    ).pack(side="left", padx=20)
        
        confirmado_var = StringVar(value=cita_actual['confirmado'])
        combo_confirmado = ttk.Combobox(frame_confirmado, 
                                    textvariable=confirmado_var,
                                    values=["Sí", "No"],
                                    state='readonly',
                                    width=10)
        combo_confirmado.pack(side="left", padx=20)

        def actualizar_horas_disponibles(*args):
            nueva_fecha = calendario.get_date()
            # Obtener nuevas horas disponibles
            horas = self.obtener_horas_disponibles(nueva_fecha, cita_actual['id'])
            
            # Si la fecha es la misma que la original, asegurarse de incluir la hora original
            if nueva_fecha == cita_actual['fecha'] and cita_actual['hora'] not in horas:
                horas.append(cita_actual['hora'])
                horas.sort()
                
            combo_hora['values'] = horas
            
            # Si la hora actual seleccionada no está disponible en la nueva fecha,
            # seleccionar la primera hora disponible
            if combo_hora.get() not in horas:
                if horas:
                    combo_hora.set(horas[0])
                else:
                    combo_hora.set('')

        calendario.bind('<<CalendarSelected>>', actualizar_horas_disponibles)
        
        def confirmar():
            resultado['confirmar'] = True
            resultado['fecha'] = calendario.get_date()
            resultado['hora'] = combo_hora.get()
            resultado['confirmado'] = confirmado_var.get()
            ventana_actualizar.destroy()
        
        def cancelar():
            ventana_actualizar.destroy()
        
        # Frame para botones
        frame_botones = ctk.CTkFrame(frame)
        frame_botones.pack(pady=30)
        
        # Botones
        ctk.CTkButton(frame_botones, 
                    text="Confirmar", 
                    command=confirmar,
                    width=180,
                    height=50,
                    font=("Arial", 16)
                    ).pack(side="left", padx=20)
        
        ctk.CTkButton(frame_botones, 
                    text="Cancelar", 
                    command=cancelar,
                    width=180,
                    height=50,
                    font=("Arial", 16)
                    ).pack(side="left", padx=20)
        
        # Ajustar tamaño y posición
        ventana_actualizar.update_idletasks()
        width = 800
        height = 800
        x = (ventana_actualizar.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana_actualizar.winfo_screenheight() // 2) - (height // 2)
        ventana_actualizar.geometry(f"{width}x{height}+{x}+{y}")
        
        ventana_actualizar.wait_window()
        return resultado

    def obtener_horas_disponibles(self, fecha, cita_id=None):
        horas_base = [
            "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", 
            "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
            "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
            "17:00", "17:30", "18:00", "18:30", "19:00", "19:30",
            "20:00", "20:30", "21:00"
        ]
        
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        
        # Obtener todas las horas ocupadas para esa fecha, excepto la de la cita actual
        cursor.execute('''
            SELECT hora 
            FROM citas 
            WHERE fecha = ? AND id != ?
        ''', (fecha, cita_id))
        
        horas_ocupadas = [hora[0] for hora in cursor.fetchall()]
        conn.close()
        
        # Filtrar las horas ocupadas
        horas_disponibles = [hora for hora in horas_base if hora not in horas_ocupadas]
        
        print(f"Fecha: {fecha}")
        print(f"Cita ID: {cita_id}")
        print(f"Horas ocupadas: {horas_ocupadas}")
        print(f"Horas disponibles: {horas_disponibles}")
        
        return horas_disponibles

    def actualizar_cita(self):
        seleccionado = self.treeview_citas.selection()
        if not seleccionado:
            messagebox.showwarning("Advertencia", "Por favor, seleccione una cita para actualizar.")
            return
        
        cita_actual = self.treeview_citas.item(seleccionado[0])['values']
        datos_cita = {
            'id': cita_actual[0],
            'paciente': cita_actual[1],
            'fecha': cita_actual[2],
            'hora': cita_actual[3],
            'confirmado': cita_actual[4]
        }
        
        resultado = self.mostrar_ventana_actualizar_cita(datos_cita)
        
        if resultado['confirmar']:
            try:
                conn = sqlite3.connect('consultorioDB.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE citas
                    SET fecha=?, hora=?, confirmado=?
                    WHERE id=?
                ''', (resultado['fecha'], resultado['hora'], 
                    resultado['confirmado'], datos_cita['id']))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Éxito", "Cita actualizada exitosamente.")
                
                # Mantener la fecha seleccionada y actualizar las listas
                self.calendario.selection_set(resultado['fecha'])  # Mantener la fecha actualizada
                self.actualizar_lista_citas(resultado['fecha'])   # Actualizar la lista de citas
                self.actualizar_horas_disponibles()               # Actualizar horas disponibles
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar la cita: {str(e)}")

    def eliminar_cita(self):
        seleccionado = self.treeview_citas.selection()
        if seleccionado:
            cita_id = self.treeview_citas.item(seleccionado[0])['values'][0]
            fecha = self.calendario.get_date()
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM citas WHERE id=?', (cita_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Cita eliminada exitosamente.")
            self.actualizar_lista_citas(fecha)
            self.actualizar_horas_disponibles()
            
        else:
            messagebox.showwarning("Advertencia", "Seleccione una cita para eliminar.")

    def limpiar_campos_cita(self):
        self.combo_hora.set('')
        self.calendario.selection_clear()
        self.confirmado_var.set("No")

    def actualizar_lista_citas(self, fecha=None):
        for row in self.treeview_citas.get_children():
            self.treeview_citas.delete(row)
        if fecha:
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT citas.id, pacientes.nombre, citas.fecha, citas.hora, citas.confirmado
                FROM citas
                JOIN pacientes ON citas.paciente_id = pacientes.id
                WHERE citas.fecha=?
                ORDER BY citas.hora
            ''', (fecha,))
            citas = cursor.fetchall()
            conn.close()
            for cita in citas:
                item = self.treeview_citas.insert("", END, values=(cita[0], cita[1], cita[2], cita[3], cita[4]))
                if cita[4] == "Sí":
                    self.treeview_citas.item(item, tags=('confirmado',))
            self.treeview_citas.tag_configure('confirmado', background='lightgreen')

    def actualizar_lista_pacientes(self):
        try:
            if hasattr(self, 'treeview_pacientes'):
                for row in self.treeview_pacientes.get_children():
                    self.treeview_pacientes.delete(row)
                    
                conn = sqlite3.connect('consultorioDB.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, nombre, telefono, es_distribuidor FROM pacientes ORDER BY nombre')
                pacientes = cursor.fetchall()
                conn.close()
                
                for paciente in pacientes:
                    es_distribuidor = "Sí" if paciente[3] else "No"
                    self.treeview_pacientes.insert("", END, values=(paciente[0], paciente[1], paciente[2], es_distribuidor))
        except Exception as e:
            print(f"Error al actualizar lista de pacientes: {e}")
            messagebox.showerror("Error", "No se pudo actualizar la lista de pacientes. Por favor, reinicie la aplicación.")

    def mostrar_gestion_cobros(self):
        # Crear ventana de gestión de cobros
        ventana_gestion = ctk.CTkToplevel(self.parent)
        ventana_gestion.title("Gestión de Cobros")
        ventana_gestion.geometry("1200x800")

        ventana_gestion.transient(self.parent)  # Hacer ventana hija de la principal
        ventana_gestion.grab_set()

        # Centrar la ventana en la pantalla
        ventana_gestion.update_idletasks()
        width = ventana_gestion.winfo_width()
        height = ventana_gestion.winfo_height()
        x = (ventana_gestion.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana_gestion.winfo_screenheight() // 2) - (height // 2)
        ventana_gestion.geometry(f'+{x}+{y}')

        # Asegurar que la ventana esté por encima
        ventana_gestion.lift()
        ventana_gestion.focus_force()

        # Variables globales para la ventana
        fecha_actual = datetime.now().strftime('%Y-%m-%d')

        def cargar_cobros():
            fecha = label_fecha.cget("text")  # Obtener fecha del label
            paciente_filtro = entry_buscar.get().strip()
            
            # Limpiar tabla
            for item in tree_cobros.get_children():
                tree_cobros.delete(item)

            try:
                conn = sqlite3.connect('consultorioDB.db')
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        c.id, 
                        c.fecha, 
                        COALESCE(p.nombre, 'Paciente borrado') as nombre_paciente, 
                        c.descripcion, 
                        c.cantidad, 
                        c.total
                    FROM cobros c
                    LEFT JOIN pacientes p ON c.paciente_id = p.id
                    WHERE c.fecha = ?
                """
                params = [fecha]

                if paciente_filtro:
                    query += " AND (p.nombre LIKE ? OR (p.nombre IS NULL AND ? = 'Paciente borrado'))"
                    params.extend([f"%{paciente_filtro}%", paciente_filtro])

                cursor.execute(query, params)
                cobros = cursor.fetchall()
                
                for cobro in cobros:
                    # Formatear el total como moneda
                    valores = list(cobro)
                    valores[5] = f"${valores[5]:.2f}"  # Formatear el total
                    
                    # Aplicar un estilo diferente si es un paciente borrado
                    if valores[2] == 'Paciente borrado':
                        tree_cobros.insert("", "end", values=valores, tags=('paciente_borrado',))
                    else:
                        tree_cobros.insert("", "end", values=valores)

                # Configurar el estilo para pacientes borrados (fondo rojo claro)
                tree_cobros.tag_configure('paciente_borrado', 
                         background='#ffcdd2',     # Rosa medio
                         foreground='#b71c1c') 
                # Actualizar total del día
                cursor.execute("""
                    SELECT SUM(total)
                    FROM cobros
                    WHERE fecha = ?
                """, [fecha])
                total_dia = cursor.fetchone()[0] or 0
                label_total.configure(text=f"Total del día: ${total_dia:.2f}")

                conn.close()
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar cobros: {str(e)}")

        def eliminar_cobro(event=None):
            seleccionado = tree_cobros.selection()
            if not seleccionado:
                messagebox.showwarning("Advertencia", "Por favor, seleccione un cobro para eliminar.")
                return

            valores = tree_cobros.item(seleccionado[0])['values']
            mensaje = f"""¿Está seguro de eliminar este cobro?

    Fecha: {valores[1]}
    Paciente: {valores[2]}
    Descripción: {valores[3]}
    Cantidad: {valores[4]}
    Total: {valores[5]}

    Esta acción no se puede deshacer."""

            if messagebox.askyesno("Confirmar Eliminación", mensaje, icon='warning'):
                try:
                    conn = sqlite3.connect('consultorioDB.db')
                    cursor = conn.cursor()
                    
                    # Obtener información del cobro antes de eliminarlo
                    cursor.execute("""
                        SELECT descripcion, cantidad
                        FROM cobros
                        WHERE id = ?
                    """, (valores[0],))
                    
                    cobro_info = cursor.fetchone()
                    if cobro_info:
                        descripcion, cantidad = cobro_info
                        
                        # Actualizar inventario si es producto o material
                        cursor.execute("""
                            UPDATE productos
                            SET cantidad = cantidad + ?
                            WHERE nombre = ?
                        """, (cantidad, descripcion))
                        
                        cursor.execute("""
                            UPDATE materiales_cirugia
                            SET cantidad = cantidad + ?
                            WHERE nombre = ?
                        """, (cantidad, descripcion))

                    # Eliminar el cobro
                    cursor.execute("DELETE FROM cobros WHERE id = ?", (valores[0],))
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("Éxito", "Cobro eliminado correctamente.")
                    cargar_cobros()  # Recargar la lista
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error al eliminar cobro: {str(e)}")

        def modificar_fecha_cobro(event=None):
            seleccionado = tree_cobros.selection()
            if not seleccionado:
                messagebox.showwarning("Advertencia", "Por favor, seleccione un cobro para modificar.")
                return

            valores = tree_cobros.item(seleccionado[0])['values']
            
            # Ventana para seleccionar nueva fecha
            ventana_fecha = ctk.CTkToplevel(ventana_gestion)
            ventana_fecha.title("Modificar Fecha")
            ventana_fecha.geometry("300x400")
            
            frame_fecha = ctk.CTkFrame(ventana_fecha)
            frame_fecha.pack(expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(frame_fecha, text="Fecha actual:").pack(pady=5)
            ctk.CTkLabel(frame_fecha, text=valores[1], font=("Arial", 12, "bold")).pack(pady=5)
            ctk.CTkLabel(frame_fecha, text="Seleccione la nueva fecha:").pack(pady=10)
            
            calendario = Calendar(frame_fecha, 
                                selectmode='day', 
                                date_pattern='yyyy-mm-dd',
                                locale='es')
            calendario.pack(pady=10)
            
            def confirmar_cambio_fecha():
                try:
                    nueva_fecha = calendario.get_date()
                    
                    # Confirmar el cambio
                    if messagebox.askyesno("Confirmar", 
                        f"¿Desea cambiar la fecha del cobro del {valores[1]} al {nueva_fecha}?"):
                        
                        conn = sqlite3.connect('consultorioDB.db')
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE cobros 
                            SET fecha = ? 
                            WHERE id = ?
                        """, (nueva_fecha, valores[0]))
                        conn.commit()
                        conn.close()
                        
                        messagebox.showinfo("Éxito", "Fecha modificada correctamente.")
                        ventana_fecha.destroy()
                        cargar_cobros()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error al modificar fecha: {str(e)}")

            frame_botones = ctk.CTkFrame(frame_fecha)
            frame_botones.pack(fill='x', pady=10)
            
            ctk.CTkButton(frame_botones, 
                        text="Confirmar",
                        command=confirmar_cambio_fecha,
                        width=100).pack(side='left', padx=5, expand=True)
            
            ctk.CTkButton(frame_botones, 
                        text="Cancelar",
                        command=ventana_fecha.destroy,
                        width=100).pack(side='left', padx=5, expand=True)

        # Frame principal
        main_frame = ctk.CTkFrame(ventana_gestion)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Frame para filtros con estilo
        frame_filtros = ctk.CTkFrame(main_frame)
        frame_filtros.pack(fill='x', pady=(0, 20))

        # Frame para la fecha con estilo CustomTkinter
        frame_fecha = ctk.CTkFrame(frame_filtros)
        frame_fecha.pack(side='left', padx=10, pady=5)

        ctk.CTkLabel(frame_fecha, 
                    text="Fecha seleccionada:", 
                    font=("Arial", 12, "bold")
                    ).pack(side='left', padx=5)

        # Label para mostrar la fecha con estilo
        label_fecha = ctk.CTkLabel(
            frame_fecha,
            text=fecha_actual,
            font=("Arial", 12),
            fg_color=("gray85", "gray25"),
            corner_radius=6,
            width=100,
            height=28
        )
        label_fecha.pack(side='left', padx=5)

        def seleccionar_fecha():
            top = ctk.CTkToplevel(ventana_gestion)
            top.title("Seleccionar Fecha")
            top.geometry("300x350")
            
            frame_cal = ctk.CTkFrame(top)
            frame_cal.pack(expand=True, fill='both', padx=20, pady=20)

            ctk.CTkLabel(frame_cal, 
                        text="Seleccione una fecha:", 
                        font=("Arial", 14, "bold")
                        ).pack(pady=(0, 10))

            cal = Calendar(frame_cal, 
                        selectmode='day',
                        date_pattern='yyyy-mm-dd',
                        locale='es',
                        font="Arial 10")
            cal.pack(pady=10)
            
            def confirmar_fecha():
                nueva_fecha = cal.get_date()
                label_fecha.configure(text=nueva_fecha)
                top.destroy()
                cargar_cobros()

            frame_botones = ctk.CTkFrame(frame_cal)
            frame_botones.pack(fill='x', pady=10)

            ctk.CTkButton(frame_botones, 
                        text="Confirmar",
                        command=confirmar_fecha,
                        width=100).pack(side='left', padx=5, expand=True)

            ctk.CTkButton(frame_botones, 
                        text="Cancelar",
                        command=top.destroy,
                        width=100).pack(side='left', padx=5, expand=True)

        ctk.CTkButton(frame_fecha, 
                    text="Cambiar Fecha",
                    command=seleccionar_fecha,
                    width=120,
                    height=32,
                    font=("Arial", 12)
                    ).pack(side='left', padx=10)

        # Label para mostrar el total del día
        label_total = ctk.CTkLabel(
            frame_fecha,
            text="Total del día: $0.00",
            font=("Arial", 12, "bold"),
            fg_color=("gray85", "gray25"),
            corner_radius=6,
            width=200,
            height=28
        )
        label_total.pack(side='left', padx=20)

        # Separador visual
        separador = ctk.CTkFrame(frame_filtros, width=2, height=36, fg_color=("gray70", "gray30"))
        separador.pack(side='left', padx=15, pady=5)

        # Frame para búsqueda de paciente
        frame_busqueda = ctk.CTkFrame(frame_filtros)
        frame_busqueda.pack(side='left', fill='x', expand=True, pady=5)

        ctk.CTkLabel(frame_busqueda, 
                    text="Buscar paciente:", 
                    font=("Arial", 12, "bold")
                    ).pack(side='left', padx=5)

        entry_buscar = ctk.CTkEntry(frame_busqueda, 
                                width=300,
                                height=32,
                                placeholder_text="Escriba el nombre del paciente...",
                                font=("Arial", 12)
                                )
        entry_buscar.pack(side='left', padx=5)

        # Frame para la tabla
        frame_tabla = ctk.CTkFrame(main_frame)
        frame_tabla.pack(fill='both', expand=True, pady=10)

        # Estilo personalizado para el Treeview
        style = ttk.Style()
        style.configure("Custom.Treeview",
                    background="#2b2b2b",
                    foreground="white",
                    fieldbackground="#2b2b2b",
                    borderwidth=0)
        style.configure("Custom.Treeview.Heading",
                    background="#1f538d",
                    foreground="white",
                    borderwidth=1)

        # Crear Treeview
        columnas = ("ID", "Fecha", "Paciente", "Descripción", "Cantidad", "Total")
        tree_cobros = ttk.Treeview(frame_tabla, 
                                columns=columnas, 
                                show='headings',
                                style="Custom.Treeview")

        # Configurar columnas
        tree_cobros.heading("ID", text="ID")
        tree_cobros.heading("Fecha", text="Fecha")
        tree_cobros.heading("Paciente", text="Paciente")
        tree_cobros.heading("Descripción", text="Descripción")
        tree_cobros.heading("Cantidad", text="Cantidad")
        tree_cobros.heading("Total", text="Total")

        tree_cobros.column("ID", width=50, anchor='center')
        tree_cobros.column("Fecha", width=100, anchor='center')
        tree_cobros.column("Paciente", width=200)
        tree_cobros.column("Descripción", width=200)
        tree_cobros.column("Cantidad", width=100, anchor='center')
        tree_cobros.column("Total", width=100, anchor='e')

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree_cobros.yview)
        tree_cobros.configure(yscrollcommand=scrollbar.set)

        tree_cobros.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Frame para botones de acción
        frame_acciones = ctk.CTkFrame(main_frame)
        frame_acciones.pack(fill='x', pady=10)

        # Botones de acción
        ctk.CTkButton(frame_acciones, 
                    text="Modificar Fecha",
                    command=lambda: modificar_fecha_cobro(),
                    width=150,
                    height=32,
                    font=("Arial", 12)
                    ).pack(side='left', padx=5)

        ctk.CTkButton(frame_acciones, 
                    text="Eliminar Cobro",
                    command=lambda: eliminar_cobro(),
                    width=150,
                    height=32,
                    font=("Arial", 12),
                    fg_color="#FF5252",
                    hover_color="#FF1744"
                    ).pack(side='left', padx=5)

        # Vincular eventos
        entry_buscar.bind('<KeyRelease>', lambda e: cargar_cobros())
        tree_cobros.bind('<Double-1>', modificar_fecha_cobro)
        tree_cobros.bind('<Delete>', eliminar_cobro)

        # Cargar cobros iniciales
        cargar_cobros()

# Ejemplo de cómo instanciar y mostrar la ventana de compra/venta en tu aplicación principal
if __name__ == "__main__":
    root = ctk.CTk()
    app = CompraVenta(root)
    root.mainloop()