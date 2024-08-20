import customtkinter as ctk
import sqlite3

from tkinter import messagebox, END, ttk
from tkcalendar import Calendar
from tkinter import StringVar, BooleanVar, simpledialog
from datetime import datetime

class CompraVenta:
    def __init__(self, parent, inventario):
        self.parent = parent
        self.inventario = inventario
        self.paciente_id = None
        self.fecha_cita = None
        self.create_widgets()
        self.conectar_db()
        self.actualizar_lista_pacientes()
        self.actualizar_lista_citas(None)

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
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()

            # Verificar que el paciente_id es correcto
            cursor.execute('SELECT paciente_id FROM citas WHERE id=?', (self.paciente_id,))
            paciente_id_correcto = cursor.fetchone()
            if paciente_id_correcto:
                paciente_id_correcto = paciente_id_correcto[0]
            else:
                raise ValueError("No se encontró la cita correspondiente")

            print(f"Paciente ID correcto: {paciente_id_correcto}")

            # Eliminar los cobros existentes para el paciente y la fecha
            cursor.execute('DELETE FROM cobros WHERE paciente_id=? AND fecha=?', (paciente_id_correcto, self.fecha_cita))
            
            estado_actual_cobros = []
            for item in self.treeview_cobros.get_children():
                valores = self.treeview_cobros.item(item)['values']
                if len(valores) >= 3:
                    estado_actual_cobros.append((valores[0], valores[1], valores[2]))

            print(f"Estado actual de cobros: {estado_actual_cobros}")

            for descripcion, cantidad, total in estado_actual_cobros:
                cursor.execute('''
                INSERT INTO cobros (paciente_id, fecha, descripcion, cantidad, total)
                VALUES (?, ?, ?, ?, ?)
                ''', (paciente_id_correcto, self.fecha_cita, descripcion, cantidad, total))
                print(f"Insertado: {descripcion}, {cantidad}, {total}")

                # Verificar si hay cambios en la cantidad
                cantidad_inicial = self.estado_inicial_cobros.get(descripcion, 0)
                diferencia = int(cantidad) - int(cantidad_inicial)

                if diferencia != 0 and descripcion != "Consulta":  # Evitar actualizar inventario para "Consulta"
                    cursor.execute('SELECT COUNT(*) FROM productos WHERE nombre = ?', (descripcion,))
                    if cursor.fetchone()[0] > 0:
                        # Es un producto, actualizar la cantidad en el inventario
                        cursor.execute('''
                            UPDATE productos
                            SET cantidad = cantidad - ?
                            WHERE nombre = ?
                        ''', (diferencia, descripcion))
                    else:
                        # Es un material, actualizar la cantidad en la tabla materiales_cirugia
                        cursor.execute('''
                            UPDATE materiales_cirugia
                            SET cantidad = cantidad - ?
                            WHERE nombre = ?
                        ''', (diferencia, descripcion))

            conn.commit()
            print("Cobros guardados exitosamente")

            # Actualizar el estado inicial de cobros después de guardar
            self.estado_inicial_cobros = {item[0]: item[1] for item in estado_actual_cobros}

            messagebox.showinfo("Éxito", "Cobro registrado exitosamente.")

            # Actualizar las tablas de inventario
            self.inventario.actualizar_lista_productos()
            self.inventario.actualizar_lista_materiales()

        except ValueError as ve:
            print(f"Error de valor: {str(ve)}")
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            print(f"Error al guardar cobro: {str(e)}")
            messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
        finally:
            if conn:
                conn.close()
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
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()

            for item in self.treeview_cobros.get_children():
                valores = self.treeview_cobros.item(item)["values"]
                descripcion, cantidad, total = valores[0], int(valores[1]), float(valores[2])
                
                # Insertar el cobro
                cursor.execute('''
                    INSERT INTO cobros (paciente_id, fecha, descripcion, cantidad, total)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.paciente_id, fecha_actual, descripcion, cantidad, total))

                # Actualizar el inventario de productos
                cursor.execute('''
                    UPDATE productos
                    SET cantidad = cantidad - ?
                    WHERE nombre = ?
                ''', (cantidad, descripcion))
                
                # Si no se actualizó ningún producto, intentar con materiales
                if cursor.rowcount == 0:
                    cursor.execute('''
                        UPDATE materiales_cirugia
                        SET cantidad = cantidad - ?
                        WHERE nombre = ?
                    ''', (cantidad, descripcion))

                print(f"Actualizando {descripcion}, cantidad: {cantidad}, filas afectadas: {cursor.rowcount}")

            conn.commit()
            messagebox.showinfo("Éxito", "Cobro registrado exitosamente y el inventario ha sido actualizado.")

            # Actualizar las tablas de inventario
            self.inventario.actualizar_lista_productos()
            self.inventario.actualizar_lista_materiales()

        except Exception as e:
            conn.rollback()  # Deshacer cambios en caso de error
            messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
        finally:
            if conn:
                conn.close()
            if self.ventana_cobro.winfo_exists():
                self.ventana_cobro.destroy()

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

    def actualizar_lista_pacientes_cobro(self):
        for row in self.treeview_pacientes.get_children():
            self.treeview_pacientes.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, telefono FROM pacientes')
        pacientes = cursor.fetchall()
        conn.close()
        for paciente in pacientes:
            self.treeview_pacientes.insert("", "end", values=(paciente[0], paciente[1], paciente[2]))

    def abrir_ventana_cobro_sin_cita(self):
        self.ventana_cobro = ctk.CTkToplevel(self.parent)
        self.ventana_cobro.title("Cobro Sin Cita")
        self.ventana_cobro.geometry("1800x1100")

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

        self.treeview_pacientes = ttk.Treeview(frame_paciente, columns=("ID", "Nombre", "Teléfono"), show='headings', height=6)
        self.treeview_pacientes.heading("ID", text="ID")
        self.treeview_pacientes.heading("Nombre", text="Nombre")
        self.treeview_pacientes.heading("Teléfono", text="Teléfono")
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

        #self.paciente_id = self.treeview_citas.item(seleccionado[0])['values'][0]
        #self.fecha_cita = self.treeview_citas.item(seleccionado[0])['values'][2]

        cita = self.treeview_citas.item(seleccionado[0])['values']
        self.paciente_id = cita[0]  # Asumiendo que el ID del paciente es el primer valor
        self.fecha_cita = cita[2]   # Asumiendo que la fecha es el tercer valor

        print(f"Abriendo ventana de cobro para cita_id: {self.paciente_id}, fecha: {self.fecha_cita}")

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
        self.entry_buscar_producto.pack(side="left", padx=5)

        label_cantidad = ctk.CTkLabel(frame_buscar_producto, text="Cantidad:")
        label_cantidad.pack(side="left", padx=5)
        vcmd_cantidad = (self.parent.register(self.validar_cantidad), '%P')
        self.entry_cantidad_producto = ctk.CTkEntry(frame_buscar_producto, validate="key", validatecommand=vcmd_cantidad)
        self.entry_cantidad_producto.pack(side="left", padx=5)

        self.entry_buscar_producto.bind("<KeyRelease>", self.filtrar_productos)

        self.treeview_productos = ttk.Treeview(self.frame_productos, columns=("ID", "Nombre", "Marca", "Precio", "Cantidad Disponible"), show='headings')
        self.treeview_productos.heading("ID", text="ID")
        self.treeview_productos.heading("Nombre", text="Nombre")
        self.treeview_productos.heading("Marca", text="Marca")
        self.treeview_productos.heading("Precio", text="Precio")
        self.treeview_productos.heading("Cantidad Disponible", text="Cantidad Disponible")
        self.treeview_productos.pack(pady=5, fill="both", expand=True)

        boton_agregar_producto = ctk.CTkButton(self.frame_productos, text="Agregar Producto", command=self.agregar_producto_cobro)
        boton_agregar_producto.pack(pady=10)

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
        self.entry_buscar_material.pack(side="left", padx=5)

        label_cantidad_material = ctk.CTkLabel(frame_buscar_material, text="Cantidad:")
        label_cantidad_material.pack(side="left", padx=5)
        vcmd_cantidad_material = (self.parent.register(self.validar_cantidad), '%P')
        self.entry_cantidad_material = ctk.CTkEntry(frame_buscar_material, validate="key", validatecommand=vcmd_cantidad_material)
        self.entry_cantidad_material.pack(side="left", padx=5)

        self.entry_buscar_material.bind("<KeyRelease>", self.filtrar_materiales)

        self.treeview_materiales = ttk.Treeview(self.frame_materiales, columns=("ID", "Nombre", "Precio", "Cantidad Disponible"), show='headings')
        self.treeview_materiales.heading("ID", text="ID")
        self.treeview_materiales.heading("Nombre", text="Nombre")
        self.treeview_materiales.heading("Precio", text="Precio")
        self.treeview_materiales.heading("Cantidad Disponible", text="Cantidad Disponible")
        self.treeview_materiales.pack(pady=5, fill="both", expand=True)

        boton_agregar_material = ctk.CTkButton(self.frame_materiales, text="Agregar Material", command=self.agregar_material_cobro)
        boton_agregar_material.pack(pady=10)

        # Ocultar el frame de materiales al inicio
        self.frame_materiales.pack_forget()

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
        #self.estado_inicial_cobros = {item["values"][0]: item["values"][1] for item in map(self.treeview_cobros.item, self.treeview_cobros.get_children())}

        # Actualizar el estado de los switches basado en los cobros existentes
        self.actualizar_switches_cobro()

    def cargar_cobros_existentes(self):
        print(f"Cargando cobros para paciente_id: {self.paciente_id}, fecha: {self.fecha_cita}")
        for row in self.treeview_cobros.get_children():
            self.treeview_cobros.delete(row)
        
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        
        # Primero, obtener el paciente_id correcto de la tabla de citas
        cursor.execute('SELECT paciente_id FROM citas WHERE id = ?', (self.paciente_id,))
        resultado = cursor.fetchone()
        if resultado:
            paciente_id_correcto = resultado[0]
        else:
            print(f"No se encontró una cita con id {self.paciente_id}")
            conn.close()
            return

        # Ahora, buscar los cobros con el paciente_id correcto
        cursor.execute('''
            SELECT descripcion, cantidad, total
            FROM cobros
            WHERE paciente_id = ? AND fecha = ?
        ''', (paciente_id_correcto, self.fecha_cita))
        cobros = cursor.fetchall()
        conn.close()
        
        print(f"Cobros encontrados: {cobros}")
        for cobro in cobros:
            self.treeview_cobros.insert("", "end", values=cobro)
        
        self.estado_inicial_cobros = {cobro[0]: cobro[1] for cobro in cobros}
        print(f"Estado inicial de cobros: {self.estado_inicial_cobros}")


    def actualizar_switches_cobro(self):
        print("Actualizando switches de cobro")
        # Resetear todos los switches
        self.cobro_consulta_var.set(False)
        self.mostrar_productos_var.set(False)
        self.mostrar_materiales_var.set(False)

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

        # Actualizar la visibilidad de los frames
        self.mostrar_ocultar_productos()
        self.mostrar_ocultar_materiales()

    def actualizar_cobro_consulta(self):
            if self.cobro_consulta_var.get():
                # Verificar si ya existe el cobro de la consulta en la lista
                for item in self.treeview_cobros.get_children():
                    if self.treeview_cobros.item(item, "values")[0] == "Consulta":
                        messagebox.showwarning("Advertencia", "La consulta ya está agregada a la lista de cobros.")
                        self.cobro_consulta_var.set(False)
                        return
                
                # Pedir al usuario que ingrese el precio de la consulta
                precio_consulta = simpledialog.askfloat("Precio de consulta", "Ingrese el precio de la consulta:", initialvalue=700)
                
                if precio_consulta is not None:
                    self.treeview_cobros.insert("", "end", values=("Consulta", 1, precio_consulta))
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

    def filtrar_productos(self, event):
        filtro = self.entry_buscar_producto.get()
        for row in self.treeview_productos.get_children():
            self.treeview_productos.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, marca, precio, cantidad FROM productos WHERE nombre LIKE ?', ('%' + filtro + '%',))
        productos = cursor.fetchall()
        conn.close()
        for producto in productos:
            self.treeview_productos.insert("", "end", values=(producto[0], producto[1], producto[2], producto[3], producto[4]))

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

            total = float(precio_producto) * cantidad

            # Verificar si el producto ya está en la lista de cobros
            for item in self.treeview_cobros.get_children():
                if self.treeview_cobros.item(item, "values")[0] == nombre_producto:
                    cantidad_actual = int(self.treeview_cobros.item(item, "values")[1])
                    nueva_cantidad = cantidad_actual + cantidad
                    nuevo_total = float(precio_producto) * nueva_cantidad
                    self.treeview_cobros.item(item, values=(nombre_producto, nueva_cantidad, nuevo_total))
                    return

            # Si el producto no está en la lista, agregarlo
            self.treeview_cobros.insert("", "end", values=(nombre_producto, cantidad, total))
        else:
            messagebox.showwarning("Advertencia", "Seleccione un producto y asegúrese de que la cantidad sea un número entero.")

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
        frame_pacientes = ctk.CTkFrame(frame_agenda)
        frame_pacientes.pack(fill='x', pady=5)

        label_buscar_paciente = ctk.CTkLabel(frame_pacientes, text="Buscar Paciente:")
        label_buscar_paciente.pack(side='left', padx=5)
        self.entry_buscar_paciente = ctk.CTkEntry(frame_pacientes)
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

        self.boton_cobro_cita = ctk.CTkButton(frame_agenda, text="Cobro Paciente", state="disabled", command=self.cobro_pacientes, width=20)
        self.boton_cobro_cita.pack(pady=(10,5), padx=5, fill='x')

        # Frame derecho para la lista de citas
        frame_lista_citas = ctk.CTkFrame(main_frame)
        frame_lista_citas.pack(side='right', fill='both', expand=True, padx=(5, 0), pady=5)

        # Añadir el nuevo botón para cobro sin cita justo después del botón de cobro de paciente
        self.boton_cobro_sin_cita = ctk.CTkButton(frame_agenda, text="Nuevo Cobro Sin Cita", state="disabled", command=self.abrir_ventana_cobro_sin_cita, width=20)
        self.boton_cobro_sin_cita.pack(pady=(0,10), padx=5, fill='x')    

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
        filtro = self.entry_buscar_paciente.get()
        for row in self.treeview_pacientes.get_children():
            self.treeview_pacientes.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, telefono FROM pacientes WHERE nombre LIKE ?', ('%' + filtro + '%',))
        pacientes = cursor.fetchall()
        conn.close()
        for paciente in pacientes:
            self.treeview_pacientes.insert("", END, values=(paciente[0], paciente[1], paciente[2]))

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
        seleccionado = self.treeview_pacientes.selection()
        if seleccionado:
            paciente_id = self.treeview_pacientes.item(seleccionado[0])['values'][0]
            fecha = self.calendario.get_date()
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
                    self.actualizar_lista_citas(fecha)
                    self.actualizar_horas_disponibles()
                    
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            else:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
        else:
            messagebox.showwarning("Advertencia", "Seleccione un paciente para agendar la cita.")

    def actualizar_cita(self):
        seleccionado = self.treeview_citas.selection()
        if seleccionado:
            cita_id = self.treeview_citas.item(seleccionado[0])['values'][0]
            fecha = self.calendario.get_date()
            hora = self.combo_hora.get()
            confirmado = self.confirmado_var.get()

            if fecha and hora:
                try:
                    conn = sqlite3.connect('consultorioDB.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE citas
                        SET fecha=?, hora=?, confirmado=?
                        WHERE id=?
                    ''', (fecha, hora, confirmado, cita_id))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Éxito", "Cita actualizada exitosamente.")
                    self.limpiar_campos_cita()
                    self.actualizar_lista_citas(fecha)
                    self.actualizar_horas_disponibles()

                    # Mantener la selección en el calendario
                    self.calendario.selection_set(fecha)
                    
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            else:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
        else:
            messagebox.showwarning("Advertencia", "Seleccione una cita para actualizar.")

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
        for row in self.treeview_pacientes.get_children():
            self.treeview_pacientes.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, telefono FROM pacientes')
        pacientes = cursor.fetchall()
        conn.close()
        for paciente in pacientes:
            self.treeview_pacientes.insert("", END, values=(paciente[0], paciente[1], paciente[2]))

# Ejemplo de cómo instanciar y mostrar la ventana de compra/venta en tu aplicación principal
if __name__ == "__main__":
    root = ctk.CTk()
    app = CompraVenta(root)
    root.mainloop()