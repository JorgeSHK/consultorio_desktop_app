import customtkinter as ctk
import sqlite3
from tkinter import messagebox, END, ttk

class Inventario:
    def __init__(self, parent):
        self.parent = parent
        self.create_widgets()
        self.conectar_db()
        self.actualizar_lista_pacientes()
        self.actualizar_lista_productos()
        self.actualizar_lista_materiales()
        self.mostrar_vista_pacientes()

    def conectar_db(self):
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT NOT NULL
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

    # Función para guardar el paciente en la base de datos
    def guardar_paciente(self):
        nombre = self.entry_nombre.get()
        telefono = self.entry_telefono.get()

        if nombre and telefono:
            try:
                conn = sqlite3.connect('consultorioDB.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO pacientes (nombre, telefono)
                    VALUES (?, ?)
                ''', (nombre, telefono))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Paciente guardado exitosamente.")
                self.limpiar_campos_pacientes()
                self.actualizar_lista_pacientes()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")

    # Función para guardar el producto en la base de datos
    def guardar_producto(self):
        nombre = self.entry_producto_nombre.get()
        marca = self.entry_producto_marca.get()
        precio = self.entry_producto_precio.get()
        cantidad = self.entry_producto_cantidad.get()

        if nombre and marca and precio and cantidad:
            try:
                conn = sqlite3.connect('consultorioDB.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, cantidad FROM productos WHERE nombre=? AND marca=?', (nombre, marca))
                producto = cursor.fetchone()

                if producto:
                    producto_id, cantidad_actual = producto
                    nueva_cantidad = int(cantidad_actual) + int(cantidad)
                    cursor.execute('UPDATE productos SET cantidad=? WHERE id=?', (nueva_cantidad, producto_id))
                else:
                    cursor.execute('''
                        INSERT INTO productos (nombre, marca, precio, cantidad)
                        VALUES (?, ?, ?, ?)
                    ''', (nombre, marca, float(precio), int(cantidad)))

                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Producto guardado exitosamente.")
                self.limpiar_campos_productos()
                self.actualizar_lista_productos()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")

    # Función para guardar el material de cirugía en la base de datos
    def guardar_material(self):
        nombre = self.entry_material_nombre.get()
        precio = self.entry_material_precio.get()
        cantidad = self.entry_material_cantidad.get()

        if nombre and precio and cantidad:
            try:
                conn = sqlite3.connect('consultorioDB.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, cantidad FROM materiales_cirugia WHERE nombre=? AND precio=?', (nombre,precio))
                material = cursor.fetchone()

                if material:
                    material_id, cantidad_actual = material
                    nueva_cantidad = int(cantidad_actual) + int(cantidad)
                    cursor.execute('UPDATE materiales_cirugia SET cantidad=? WHERE id=?',(nueva_cantidad,material_id))
                else:
                    cursor.execute('''
                        INSERT INTO materiales_cirugia (nombre, precio, cantidad)
                        VALUES (?, ?, ?)
                    ''', (nombre, float(precio), int(cantidad)))
                    
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Material guardado exitosamente.")
                self.limpiar_campos_materiales()
                self.actualizar_lista_materiales()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")

    # Función para actualizar un producto en la base de datos
    def actualizar_producto(self):
        seleccionado = self.treeview_productos.selection()
        if seleccionado:
            producto_id = self.treeview_productos.item(seleccionado[0])['values'][0]
            nombre = self.entry_producto_nombre.get()
            marca = self.entry_producto_marca.get()
            precio = self.entry_producto_precio.get()
            cantidad = self.entry_producto_cantidad.get()

            if nombre and marca and precio and cantidad:
                try:
                    conn = sqlite3.connect('consultorioDB.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE productos
                        SET nombre=?, marca=?, precio=?, cantidad=?
                        WHERE id=?
                    ''', (nombre, marca, float(precio), int(cantidad), producto_id))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Éxito", "Producto actualizado exitosamente.")
                    self.limpiar_campos_productos()
                    self.actualizar_lista_productos()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            else:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
        else:
            messagebox.showwarning("Advertencia", "Seleccione un producto para actualizar.")

    # Función para actualizar un material de cirugía en la base de datos
    def actualizar_material(self):
        seleccionado = self.treeview_materiales.selection()
        if seleccionado:
            material_id = self.treeview_materiales.item(seleccionado[0])['values'][0]
            nombre = self.entry_material_nombre.get()
            precio = self.entry_material_precio.get()
            cantidad = self.entry_material_cantidad.get()

            if nombre and precio and cantidad:
                try:
                    conn = sqlite3.connect('consultoriDB.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE materiales_cirugia
                        SET nombre=?, precio=?, cantidad=?
                        WHERE id=?
                    ''', (nombre, float(precio), int(cantidad), material_id))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Éxito", "Material actualizado exitosamente.")
                    self.limpiar_campos_materiales()
                    self.actualizar_lista_materiales()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            else:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
        else:
            messagebox.showwarning("Advertencia", "Seleccione un material para actualizar.")

    # Función para limpiar los campos de entrada de pacientes
    def limpiar_campos_pacientes(self):
        self.entry_nombre.delete(0, ctk.END)
        self.entry_telefono.delete(0, ctk.END)

    # Función para limpiar los campos de entrada de productos
    def limpiar_campos_productos(self):
        self.entry_producto_nombre.delete(0, ctk.END)
        self.entry_producto_marca.delete(0, ctk.END)
        self.entry_producto_precio.delete(0, ctk.END)
        self.entry_producto_cantidad.delete(0, ctk.END)

    # Función para limpiar los campos de entrada de materiales de cirugía
    def limpiar_campos_materiales(self):
        self.entry_material_nombre.delete(0, ctk.END)
        self.entry_material_precio.delete(0, ctk.END)
        self.entry_material_cantidad.delete(0, ctk.END)

    # Función para actualizar la lista de pacientes
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

    # Función para actualizar la lista de productos
    def actualizar_lista_productos(self):
        for row in self.treeview_productos.get_children():
            self.treeview_productos.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, marca, precio, cantidad FROM productos')
        productos = cursor.fetchall()
        conn.close()
        for producto in productos:
            self.treeview_productos.insert("", END, values=(producto[0], producto[1], producto[2], producto[3], producto[4]))

    # Función para actualizar la lista de materiales de cirugía
    def actualizar_lista_materiales(self):
        for row in self.treeview_materiales.get_children():
            self.treeview_materiales.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, precio, cantidad FROM materiales_cirugia')
        materiales = cursor.fetchall()
        conn.close()
        for material in materiales:
            self.treeview_materiales.insert("", END, values=(material[0], material[1], material[2], material[3]))

    # Función para eliminar un paciente seleccionado
    def eliminar_paciente(self):
        seleccionado = self.treeview_pacientes.selection()
        if seleccionado:
            paciente_id = self.treeview_pacientes.item(seleccionado[0])['values'][0]
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM pacientes WHERE id=?', (paciente_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Paciente eliminado exitosamente.")
            self.actualizar_lista_pacientes()
        else:
            messagebox.showwarning("Advertencia", "Seleccione un paciente para eliminar.")

    # Función para eliminar un producto seleccionado
    def eliminar_producto(self):
        seleccionado = self.treeview_productos.selection()
        if seleccionado:
            producto_id = self.treeview_productos.item(seleccionado[0])['values'][0]
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM productos WHERE id=?', (producto_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Producto eliminado exitosamente.")
            self.actualizar_lista_productos()
        else:
            messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar.")

    # Función para eliminar un material seleccionado
    def eliminar_material(self):
        seleccionado = self.treeview_materiales.selection()
        if seleccionado:
            material_id = self.treeview_materiales.item(seleccionado[0])['values'][0]
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM materiales_cirugia WHERE id=?', (material_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Material eliminado exitosamente.")
            self.actualizar_lista_materiales()
        else:
            messagebox.showwarning("Advertencia", "Seleccione un material para eliminar.")

    # Función para cargar los datos del paciente seleccionado en los campos de entrada
    def cargar_datos_paciente(self, event):
        seleccionado = self.treeview_pacientes.selection()
        if seleccionado:
            paciente_id = self.treeview_pacientes.item(seleccionado[0])['values'][0]
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nombre, telefono FROM pacientes WHERE id=?', (paciente_id,))
            paciente = cursor.fetchone()
            conn.close()
            if paciente:
                self.entry_nombre.delete(0, ctk.END)
                self.entry_nombre.insert(0, paciente[0])
                self.entry_telefono.delete(0, ctk.END)
                self.entry_telefono.insert(0, paciente[1])

    # Función para cargar los datos del producto seleccionado en los campos de entrada
    def cargar_datos_producto(self, event):
        seleccionado = self.treeview_productos.selection()
        if seleccionado:
            producto_id = self.treeview_productos.item(seleccionado[0])['values'][0]
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nombre, marca, precio, cantidad FROM productos WHERE id=?', (producto_id,))
            producto = cursor.fetchone()
            conn.close()
            if producto:
                self.entry_producto_nombre.delete(0, ctk.END)
                self.entry_producto_nombre.insert(0, producto[0])
                self.entry_producto_marca.delete(0, ctk.END)
                self.entry_producto_marca.insert(0, producto[1])
                self.entry_producto_precio.delete(0, ctk.END)
                self.entry_producto_precio.insert(0, producto[2])
                self.entry_producto_cantidad.delete(0, ctk.END)
                self.entry_producto_cantidad.insert(0, producto[3])

    # Función para cargar los datos del material seleccionado en los campos de entrada
    def cargar_datos_material(self, event):
        seleccionado = self.treeview_materiales.selection()
        if seleccionado:
            material_id = self.treeview_materiales.item(seleccionado[0])['values'][0]
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nombre, precio, cantidad FROM materiales_cirugia WHERE id=?', (material_id,))
            material = cursor.fetchone()
            conn.close()
            if material:
                self.entry_material_nombre.delete(0, ctk.END)
                self.entry_material_nombre.insert(0, material[0])
                self.entry_material_precio.delete(0, ctk.END)
                self.entry_material_precio.insert(0, material[1])
                self.entry_material_cantidad.delete(0, ctk.END)
                self.entry_material_cantidad.insert(0, material[2])

    # Función para filtrar la lista de productos según la búsqueda
    def filtrar_productos(self, event):
        filtro = self.entry_buscar_producto.get()
        for row in self.treeview_productos.get_children():
            self.treeview_productos.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, marca, precio, cantidad FROM productos WHERE nombre LIKE ? OR marca LIKE ?', ('%' + filtro + '%', '%' + filtro + '%'))
        productos = cursor.fetchall()
        conn.close()
        for producto in productos:
            self.treeview_productos.insert("", END, values=(producto[0], producto[1], producto[2], producto[3], producto[4]))

    #Funcion para filtrar la lista de materiales según la búsqueda
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
            self.treeview_materiales.insert("", END, values=(material[0], material[1], material[2],material[3]))

    # Función para filtrar la lista de pacientes según la búsqueda
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

    # Validar entrada de nombre (solo letras)
    def validar_nombre(self, text):
        return all(char.isalpha() or char.isspace() for char in text) or text == ""

    # Validar entrada de teléfono (solo números)
    def validar_telefono(self, text):
        return text.isdigit() or text == ""

    # Validar entrada de precio (solo números y punto)
    def validar_precio(self, text):
        return text.replace('.', '', 1).isdigit() or text == ""

    # Validar entrada de cantidad (solo números)
    def validar_cantidad(self, text):
        return text.isdigit() or text == ""

    # Función para mostrar la vista de pacientes
    def mostrar_vista_pacientes(self):
        self.frame_pacientes.pack(fill='both', expand=True)
        self.frame_productos.pack_forget()
        self.frame_materiales.pack_forget()

    # Función para mostrar la vista de productos
    def mostrar_vista_productos(self):
        self.frame_productos.pack(fill='both', expand=True)
        self.frame_pacientes.pack_forget()
        self.frame_materiales.pack_forget()

    # Función para mostrar la vista de materiales de cirugía
    def mostrar_vista_materiales(self):
        self.frame_materiales.pack(fill='both', expand=True)
        self.frame_pacientes.pack_forget()
        self.frame_productos.pack_forget()

    def create_widgets(self):
        # Frame para los botones de selección de vista dentro del inventario
        frame_vista = ctk.CTkFrame(self.parent)
        frame_vista.pack(side='left', fill='y', padx=10, pady=10)

        # Botones para cambiar la vista dentro del inventario
        boton_vista_pacientes = ctk.CTkButton(frame_vista, text="Pacientes", command=self.mostrar_vista_pacientes)
        boton_vista_pacientes.pack(pady=5)
        boton_vista_productos = ctk.CTkButton(frame_vista, text="Productos", command=self.mostrar_vista_productos)
        boton_vista_productos.pack(pady=5)
        boton_vista_materiales = ctk.CTkButton(frame_vista, text="Materiales de Cirugía", command=self.mostrar_vista_materiales)
        boton_vista_materiales.pack(pady=5)

        # Frame para la vista de Pacientes
        self.frame_pacientes = ctk.CTkFrame(self.parent)

        # Sección de Pacientes
        frame_form_pacientes = ctk.CTkFrame(self.frame_pacientes)
        frame_form_pacientes.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        label_pacientes = ctk.CTkLabel(frame_form_pacientes, text="Registro de Pacientes")
        label_pacientes.grid(row=0, column=0, columnspan=2, pady=5)

        label_nombre = ctk.CTkLabel(frame_form_pacientes, text="Nombre:")
        label_nombre.grid(row=1, column=0, pady=5, padx=5, sticky='e')
        vcmd_nombre = (self.parent.register(self.validar_nombre), '%P')
        self.entry_nombre = ctk.CTkEntry(frame_form_pacientes, validate="key", validatecommand=vcmd_nombre)
        self.entry_nombre.grid(row=1, column=1, pady=5, padx=5)

        label_telefono = ctk.CTkLabel(frame_form_pacientes, text="Teléfono:")
        label_telefono.grid(row=2, column=0, pady=5, padx=5, sticky='e')
        vcmd_telefono = (self.parent.register(self.validar_telefono), '%P')
        self.entry_telefono = ctk.CTkEntry(frame_form_pacientes, validate="key", validatecommand=vcmd_telefono)
        self.entry_telefono.grid(row=2, column=1, pady=5, padx=5)

        # Botón para guardar el paciente
        boton_guardar_paciente = ctk.CTkButton(frame_form_pacientes, text="Guardar Paciente", command=self.guardar_paciente)
        boton_guardar_paciente.grid(row=3, column=0, columnspan=2, pady=10)

        # Botón para eliminar el paciente seleccionado
        boton_eliminar_paciente = ctk.CTkButton(frame_form_pacientes, text="Eliminar Paciente", command=self.eliminar_paciente)
        boton_eliminar_paciente.grid(row=4, column=0, columnspan=2, pady=10)

        # Treeview para mostrar la lista de pacientes
        frame_lista_pacientes = ctk.CTkFrame(self.frame_pacientes)
        frame_lista_pacientes.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        label_buscar_paciente = ctk.CTkLabel(frame_lista_pacientes, text="Buscar Paciente:")
        label_buscar_paciente.pack(pady=5)
        self.entry_buscar_paciente = ctk.CTkEntry(frame_lista_pacientes)
        self.entry_buscar_paciente.pack(pady=5)
        self.entry_buscar_paciente.bind("<KeyRelease>", self.filtrar_pacientes)

        label_lista_pacientes = ctk.CTkLabel(frame_lista_pacientes, text="Lista de Pacientes:")
        label_lista_pacientes.pack(pady=5)
        self.treeview_pacientes = ttk.Treeview(frame_lista_pacientes, columns=("ID", "Nombre", "Teléfono"), show='headings')
        self.treeview_pacientes.heading("ID", text="ID")
        self.treeview_pacientes.heading("Nombre", text="Nombre")
        self.treeview_pacientes.heading("Teléfono", text="Teléfono")
        self.treeview_pacientes.pack(pady=5, fill='both', expand=True)
        self.treeview_pacientes.bind("<Double-1>", self.cargar_datos_paciente)  # Doble clic para cargar datos

        # Frame para la vista de Productos
        self.frame_productos = ctk.CTkFrame(self.parent)

        # Sección de Productos
        frame_form_productos = ctk.CTkFrame(self.frame_productos)
        frame_form_productos.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        label_productos = ctk.CTkLabel(frame_form_productos, text="Inventario de Productos")
        label_productos.grid(row=0, column=0, columnspan=2, pady=5)

        label_producto_nombre = ctk.CTkLabel(frame_form_productos, text="Nombre del Producto:")
        label_producto_nombre.grid(row=1, column=0, pady=5, padx=5, sticky='e')
        self.entry_producto_nombre = ctk.CTkEntry(frame_form_productos)
        self.entry_producto_nombre.grid(row=1, column=1, pady=5, padx=5)

        label_producto_marca = ctk.CTkLabel(frame_form_productos, text="Marca:")
        label_producto_marca.grid(row=2, column=0, pady=5, padx=5, sticky='e')
        self.entry_producto_marca = ctk.CTkEntry(frame_form_productos)
        self.entry_producto_marca.grid(row=2, column=1, pady=5, padx=5)

        label_producto_precio = ctk.CTkLabel(frame_form_productos, text="Precio:")
        label_producto_precio.grid(row=3, column=0, pady=5, padx=5, sticky='e')
        vcmd_precio = (self.parent.register(self.validar_precio), '%P')
        self.entry_producto_precio = ctk.CTkEntry(frame_form_productos, validate="key", validatecommand=vcmd_precio)
        self.entry_producto_precio.grid(row=3, column=1, pady=5, padx=5)

        label_producto_cantidad = ctk.CTkLabel(frame_form_productos, text="Cantidad:")
        label_producto_cantidad.grid(row=4, column=0, pady=5, padx=5, sticky='e')
        vcmd_cantidad = (self.parent.register(self.validar_cantidad), '%P')
        self.entry_producto_cantidad = ctk.CTkEntry(frame_form_productos, validate="key", validatecommand=vcmd_cantidad)
        self.entry_producto_cantidad.grid(row=4, column=1, pady=5, padx=5)

        # Botón para guardar el producto
        boton_guardar_producto = ctk.CTkButton(frame_form_productos, text="Guardar Producto", command=self.guardar_producto)
        boton_guardar_producto.grid(row=5, column=0, columnspan=2, pady=10)

        # Botón para actualizar el producto
        boton_actualizar_producto = ctk.CTkButton(frame_form_productos, text="Actualizar Producto", command=self.actualizar_producto)
        boton_actualizar_producto.grid(row=6, column=0, columnspan=2, pady=10)

        # Treeview para mostrar la lista de productos
        frame_lista_productos = ctk.CTkFrame(self.frame_productos)
        frame_lista_productos.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Seccion para busqueda de productos.
        label_buscar_producto = ctk.CTkLabel(frame_lista_productos, text="Buscar Producto:")
        label_buscar_producto.pack(pady=5)
        self.entry_buscar_producto = ctk.CTkEntry(frame_lista_productos)
        self.entry_buscar_producto.pack(pady=5)
        self.entry_buscar_producto.bind("<KeyRelease>", self.filtrar_productos)

        label_lista_productos = ctk.CTkLabel(frame_lista_productos, text="Lista de Productos:")
        label_lista_productos.pack(pady=5)
        self.treeview_productos = ttk.Treeview(frame_lista_productos, columns=("ID", "Nombre", "Marca", "Precio", "Cantidad"), show='headings')
        self.treeview_productos.heading("ID", text="ID")
        self.treeview_productos.heading("Nombre", text="Nombre")
        self.treeview_productos.heading("Marca", text="Marca")
        self.treeview_productos.heading("Precio", text="Precio")
        self.treeview_productos.heading("Cantidad", text="Cantidad")
        self.treeview_productos.pack(pady=5, fill='both', expand=True)
        self.treeview_productos.bind("<Double-1>", self.cargar_datos_producto)  # Doble clic para cargar datos

        # Botón para eliminar el producto seleccionado
        boton_eliminar_producto = ctk.CTkButton(frame_form_productos, text="Eliminar Producto", command=self.eliminar_producto)
        boton_eliminar_producto.grid(row=7, column=0, columnspan=2, pady=10)

        # Frame para la vista de Materiales de Cirugía
        self.frame_materiales = ctk.CTkFrame(self.parent)

        # Sección de Materiales de Cirugía
        frame_form_materiales = ctk.CTkFrame(self.frame_materiales)
        frame_form_materiales.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        label_materiales = ctk.CTkLabel(frame_form_materiales, text="Materiales de Cirugía")
        label_materiales.grid(row=0, column=0, columnspan=2, pady=5)

        label_material_nombre = ctk.CTkLabel(frame_form_materiales, text="Nombre del Material:")
        label_material_nombre.grid(row=1, column=0, pady=5, padx=5, sticky='e')
        self.entry_material_nombre = ctk.CTkEntry(frame_form_materiales)
        self.entry_material_nombre.grid(row=1, column=1, pady=5, padx=5)

        label_material_precio = ctk.CTkLabel(frame_form_materiales, text="Precio:")
        label_material_precio.grid(row=2, column=0, pady=5, padx=5, sticky='e')
        vcmd_precio = (self.parent.register(self.validar_precio), '%P')
        self.entry_material_precio = ctk.CTkEntry(frame_form_materiales, validate="key", validatecommand=vcmd_precio)
        self.entry_material_precio.grid(row=2, column=1, pady=5, padx=5)

        label_material_cantidad = ctk.CTkLabel(frame_form_materiales, text="Cantidad:")
        label_material_cantidad.grid(row=3, column=0, pady=5, padx=5, sticky='e')
        vcmd_cantidad = (self.parent.register(self.validar_cantidad), '%P')
        self.entry_material_cantidad = ctk.CTkEntry(frame_form_materiales, validate="key", validatecommand=vcmd_cantidad)
        self.entry_material_cantidad.grid(row=3, column=1, pady=5, padx=5)

        # Botón para guardar el material
        boton_guardar_material = ctk.CTkButton(frame_form_materiales, text="Guardar Material", command=self.guardar_material)
        boton_guardar_material.grid(row=4, column=0, columnspan=2, pady=10)

        # Botón para actualizar el material
        boton_actualizar_material = ctk.CTkButton(frame_form_materiales, text="Actualizar Material", command=self.actualizar_material)
        boton_actualizar_material.grid(row=5, column=0, columnspan=2, pady=10)

        # Botón para eliminar el material seleccionado
        boton_eliminar_material = ctk.CTkButton(frame_form_materiales, text="Eliminar Material", command=self.eliminar_material)
        boton_eliminar_material.grid(row=6, column=0, columnspan=2, pady=10)

        # Treeview para mostrar la lista de materiales
        frame_lista_materiales = ctk.CTkFrame(self.frame_materiales)
        frame_lista_materiales.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Filtro para busqueda en lista de materiales.
        label_buscar_material = ctk.CTkLabel(frame_lista_materiales, text="Buscar Material:")
        label_buscar_material.pack(pady=5)
        self.entry_buscar_material = ctk.CTkEntry(frame_lista_materiales)
        self.entry_buscar_material.pack(pady=5)
        self.entry_buscar_material.bind("<KeyRelease>", self.filtrar_materiales)


        label_lista_materiales = ctk.CTkLabel(frame_lista_materiales, text="Lista de Materiales:")
        label_lista_materiales.pack(pady=5)
        self.treeview_materiales = ttk.Treeview(frame_lista_materiales, columns=("ID", "Nombre", "Precio", "Cantidad"), show='headings')
        self.treeview_materiales.heading("ID", text="ID")
        self.treeview_materiales.heading("Nombre", text="Nombre")
        self.treeview_materiales.heading("Precio", text="Precio")
        self.treeview_materiales.heading("Cantidad", text="Cantidad")
        self.treeview_materiales.pack(pady=5, fill='both', expand=True)
        self.treeview_materiales.bind("<Double-1>", self.cargar_datos_material)  # Doble clic para cargar datos
