import customtkinter as ctk
import sqlite3
from typing import List, Tuple
from tkinter import messagebox, END, ttk
from datetime import datetime
from database import conectar_db


class AutocompleteEntry(ctk.CTkEntry):
    def __init__(self, master, completions: List[Tuple[int, str]], **kwargs):
        super().__init__(master, **kwargs)
        
        self.completions = completions
        self.popup_menu = None
        self.bind("<KeyRelease>", self._on_keyrelease)

    def _on_keyrelease(self, event):
        if self.popup_menu:
            self.popup_menu.destroy()
        
        value = self.get().lower()
        if not value:
            return

        matches = [item for item in self.completions if value in item[1].lower()]
        if not matches:
            return

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()

        self.popup_menu = ctk.CTkToplevel(self)
        self.popup_menu.wm_overrideredirect(True)
        self.popup_menu.wm_geometry(f"+{x}+{y}")

        listbox = ctk.CTkScrollableFrame(self.popup_menu)
        listbox.pack(expand=True, fill="both")

        for patient_id, name in matches[:10]:  # Limitar a 10 sugerencias
            btn = ctk.CTkButton(listbox, text=name, anchor="w", 
                                command=lambda n=name, i=patient_id: self._on_select(n, i))
            btn.pack(fill="x", padx=2, pady=2)

    def _on_select(self, name: str, patient_id: int):
        self.delete(0, "end")
        self.insert(0, name)
        self.selected_id = patient_id
        if self.popup_menu:
            self.popup_menu.destroy()

    def get_selected(self):
        return getattr(self, 'selected_id', None), self.get()


class Inventario:
    def __init__(self, parent,conn):
        print("Estructura de la tabla plantillas después de la actualización:")
        print(self.imprimir_estructura_plantillas())

        self.parent = parent
        self.conn = conn
        self.filtro_plantillas = ctk.StringVar(value="Todas")
        self.actualizar_estructura_plantillas()
        
        print("Estructura de la tabla plantillas después de la actualización:")
        print(self.imprimir_estructura_plantillas())
        
        self.precios = {
        "Plantillas o Taloneras": [
            ((12, 15), 300), ((15.5, 18), 320), ((18.5, 21), 350),
            ((21.5, 24), 370), ((24.5, 30), 400)
        ],
        "Virones y Cuñas": [
            ((12, 15), 300), ((15.5, 18), 320), ((18.5, 21), 350),
            ((21.5, 24), 370), ((24.5, 30), 400)
        ],
        "Virones Corridos": [
            ((12, 15), 360), ((15.5, 18), 390), ((18.5, 21), 400),
            ((21.5, 24), 440), ((24.5, 27), 470), ((27.5, 30), 500)
        ],
        "Adaptaciones": 80,
        "Mangueras Derrotadoras": 2470,
        "Aumento a calzado hasta 1 CM": 380,
        "Centímetro extra": 320,
        "Plantilla o Talonera aumento de 1 CM": 330,
        "Por cada CM extra C/U": 220,
        "Plantilla o Talonera para espolón C/U": 350,
        "Cambio de calzado a manguera": 410
        }

        self.estados_plantilla = {
            'PENDIENTE DE PAGO': 'Pendiente de pago',
            'PAGADA': 'Pagada'
        }

        self.create_widgets()
        self.actualizar_lista_pacientes()
        self.actualizar_lista_productos()
        self.actualizar_lista_materiales()
        self.actualizar_lista_plantillas()

        self.mostrar_vista_pacientes()

    def guardar_paciente(self):
        nombre = self.entry_nombre.get()
        telefono = self.entry_telefono.get()
        es_distribuidor = self.var_es_distribuidor.get()

        if nombre and telefono:
            try:
                conn = sqlite3.connect('consultorioDB.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO pacientes (nombre, telefono, es_distribuidor)
                    VALUES (?, ?, ?)
                ''', (nombre, telefono, es_distribuidor))
                conn.commit()
                nuevo_id = cursor.lastrowid
                conn.close()
                messagebox.showinfo("Éxito", "Paciente guardado exitosamente.")
                self.limpiar_campos_pacientes()
                self.actualizar_lista_pacientes()
                
                # Notificar a todas las instancias de CompraVenta
                for widget in self.parent.winfo_children():
                    if isinstance(widget, ctk.CTkTabview):
                        for tab in widget._tab_dict.values():
                            for child in tab.winfo_children():
                                if hasattr(child, 'actualizar_lista_pacientes'):
                                    child.actualizar_lista_pacientes()
                                if hasattr(child, 'entry_buscar_paciente'):
                                    child.entry_buscar_paciente.delete(0, 'end')
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")

    def actualizar_paciente(self):
        seleccionado = self.treeview_pacientes.selection()
        if not seleccionado:
            messagebox.showwarning("Advertencia","Seleccione un paciente para actualizar")
            return

        #Obtener Id del paciente seleccionado
        paciente_id = self.treeview_pacientes.item(seleccionado[0])['values'][0]
        nombre = self.entry_nombre.get()
        telefono = self.entry_telefono.get()
        es_distribuidor = self.var_es_distribuidor.get()

        if nombre and telefono:
            try:
                conn = sqlite3.connect('consultorioDB.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE pacientes
                    SET nombre=?, telefono=?,es_distribuidor=?
                    WHERE id=?
                ''', (nombre, telefono, es_distribuidor, paciente_id))
                conn.commit()
                conn.close()

                messagebox.showinfo("Éxito","Paciente actualizado exitosamente")
                self.limpiar_campos_pacientes()
                self.actualizar_lista_pacientes()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Advertencia","Todos los campos son obligatorios")

    def actualizar_lista_pacientes_plantillas(self, nuevo_id, nuevo_nombre):
        if hasattr(self, 'entry_paciente'):
            self.entry_paciente.completions.append((nuevo_id, nuevo_nombre))
            self.entry_paciente.completions.sort(key=lambda x: x[1])  # Ordenar por nombre

    # Función para guardar el producto en la base de datos
    def guardar_producto(self):
        nombre = self.entry_producto_nombre.get()
        marca = self.entry_producto_marca.get()
        precio = self.entry_producto_precio.get()
        precio_distribuidor = self.entry_producto_precio_distribuidor.get()
        cantidad = self.entry_producto_cantidad.get()

        if nombre and marca and precio and precio_distribuidor and cantidad:
            try:
                conn = sqlite3.connect('consultorioDB.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, cantidad FROM productos WHERE nombre=? AND marca=?', (nombre, marca))
                producto = cursor.fetchone()

                if producto:
                    producto_id, cantidad_actual = producto
                    nueva_cantidad = int(cantidad_actual) + int(cantidad)
                    cursor.execute('''
                        UPDATE productos 
                        SET cantidad=?, precio=?, precio_distribuidor=? 
                        WHERE id=?
                    ''', (nueva_cantidad, float(precio), float(precio_distribuidor), producto_id))
                else:
                    cursor.execute('''
                        INSERT INTO productos (nombre, marca, precio, precio_distribuidor, cantidad)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (nombre, marca, float(precio), float(precio_distribuidor), int(cantidad)))

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
            precio_distribuidor = self.entry_producto_precio_distribuidor.get()
            cantidad = self.entry_producto_cantidad.get()

            if nombre and marca and precio and precio_distribuidor and cantidad:
                try:
                    conn = sqlite3.connect('consultorioDB.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE productos
                        SET nombre=?, marca=?, precio=?, precio_distribuidor=?, cantidad=?
                        WHERE id=?
                    ''', (nombre, marca, float(precio), float(precio_distribuidor), int(cantidad), producto_id))
                    conn.commit()
                    conn.close()
                    
                    # Actualizar el item en el treeview
                    self.treeview_productos.item(seleccionado[0], values=(producto_id, nombre, marca, precio, precio_distribuidor, cantidad))
                    
                    messagebox.showinfo("Éxito", "Producto actualizado exitosamente.")
                    self.limpiar_campos_productos()
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
                    conn = sqlite3.connect('consultorioDB.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE materiales_cirugia
                        SET nombre=?, precio=?, cantidad=?
                        WHERE id=?
                    ''', (nombre, float(precio), int(cantidad), material_id))
                    conn.commit()
                    conn.close()
                    
                    # Actualizar el item en el treeview
                    self.treeview_materiales.item(seleccionado[0], values=(material_id, nombre, precio, cantidad))
                    
                    messagebox.showinfo("Éxito", "Material actualizado exitosamente.")
                    self.limpiar_campos_materiales()
                except sqlite3.Error as e:
                    messagebox.showerror("Error de base de datos", f"No se pudo actualizar el material: {str(e)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Ocurrió un error inesperado: {str(e)}")
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
        self.entry_producto_precio_distribuidor.delete(0, ctk.END)
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
        cursor.execute('SELECT id, nombre, telefono, es_distribuidor FROM pacientes')
        pacientes = cursor.fetchall()
        conn.close()
        for paciente in pacientes:
            es_distribuidor = "Sí" if paciente[3] else "No"
            self.treeview_pacientes.insert("", END, values=(paciente[0], paciente[1], paciente[2], es_distribuidor))

    def actualizar_lista_productos(self):
        for row in self.treeview_productos.get_children():
            self.treeview_productos.delete(row)
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        
        # Primero, verifica si la columna precio_distribuidor existe
        cursor.execute("PRAGMA table_info(productos)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'precio_distribuidor' in columnas:
            cursor.execute('SELECT id, nombre, marca, precio, precio_distribuidor, cantidad FROM productos')
        else:
            cursor.execute('SELECT id, nombre, marca, precio, cantidad FROM productos')
        
        productos = cursor.fetchall()
        conn.close()
        
        for producto in productos:
            if len(producto) == 6:  # Si tiene precio_distribuidor
                self.treeview_productos.insert("", END, values=producto)
            else:  # Si no tiene precio_distribuidor
                self.treeview_productos.insert("", END, values=(producto[0], producto[1], producto[2], producto[3], "N/A", producto[4]))

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

    def eliminar_paciente(self):
        seleccionado = self.treeview_pacientes.selection()
        if seleccionado:
            paciente_id = self.treeview_pacientes.item(seleccionado[0])['values'][0]
            nombre_paciente = self.treeview_pacientes.item(seleccionado[0])['values'][1]
            
            print(f"Intentando eliminar paciente: ID={paciente_id}, Nombre={nombre_paciente}")  # Debug
            
            # Verificar relaciones
            try:
                relaciones = self.verificar_relaciones_paciente(paciente_id)
                
                if relaciones['citas'] > 0 or relaciones['cobros'] > 0:
                    mensaje = f"El paciente {nombre_paciente} tiene:\n"
                    if relaciones['citas'] > 0:
                        mensaje += f"- {relaciones['citas']} citas registradas\n"
                    if relaciones['cobros'] > 0:
                        mensaje += f"- {relaciones['cobros']} cobros registrados\n"
                    mensaje += "\n¿Está seguro que desea eliminar al paciente?"
                    
                    if messagebox.askyesno("Advertencia", mensaje):
                        self.realizar_eliminacion_paciente(paciente_id)
                else:
                    # Si no tiene relaciones, preguntar normal
                    if messagebox.askyesno("Confirmar", 
                        f"¿Está seguro que desea eliminar al paciente {nombre_paciente}?"):
                        self.realizar_eliminacion_paciente(paciente_id)
                
                        
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar la eliminación: {str(e)}")
                
        else:
            messagebox.showwarning("Advertencia", "Seleccione un paciente para eliminar.")

    def realizar_eliminacion_paciente(self, paciente_id):
        """Función auxiliar para realizar la eliminación del paciente"""
        try:
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM pacientes WHERE id=?', (paciente_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Paciente eliminado exitosamente.")
            self.actualizar_lista_pacientes()

            from compraventa import CompraVenta
            for widget in self.parent.winfo_children():
                if isinstance(widget, CompraVenta):
                    widget.actualizar_lista_citas(None)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el paciente: {str(e)}")



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

    def verificar_relaciones_paciente(self, paciente_id):
        try:
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            
            print(f"Verificando relaciones para paciente_id: {paciente_id}")  # Debug
            
            # Verificar citas
            cursor.execute('SELECT COUNT(*) FROM citas WHERE paciente_id = ?', (paciente_id,))
            num_citas = cursor.fetchone()[0]
            print(f"Número de citas encontradas: {num_citas}")  # Debug
            
            # Verificar cobros
            cursor.execute('SELECT COUNT(*) FROM cobros WHERE paciente_id = ?', (paciente_id,))
            num_cobros = cursor.fetchone()[0]
            print(f"Número de cobros encontrados: {num_cobros}")  # Debug
            
            conn.close()
            
            return {
                'citas': num_citas,
                'cobros': num_cobros
            }
            
        except Exception as e:
            print(f"Error al verificar relaciones: {str(e)}")
            # En lugar de retornar None, retornamos un diccionario con valores 0
            return {
                'citas': 0,
                'cobros': 0
            }
        
        except Exception as e:
            print(f"Error al verificar relaciones: {str(e)}")
            return None

    # Función para cargar los datos del paciente seleccionado en los campos de entrada
    def cargar_datos_paciente(self, event):
        seleccionado = self.treeview_pacientes.selection()
        if seleccionado:
            paciente_id = self.treeview_pacientes.item(seleccionado[0])['values'][0]
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nombre, telefono, es_distribuidor FROM pacientes WHERE id=?', (paciente_id,))
            paciente = cursor.fetchone()
            conn.close()
            if paciente:
                self.entry_nombre.delete(0, ctk.END)
                self.entry_nombre.insert(0, paciente[0])
                self.entry_telefono.delete(0, ctk.END)
                self.entry_telefono.insert(0, paciente[1])
                self.var_es_distribuidor.set(paciente[2])

    # Función para cargar los datos del producto seleccionado en los campos de entrada
    def cargar_datos_producto(self, event):
        seleccionado = self.treeview_productos.selection()
        if seleccionado:
            producto_id = self.treeview_productos.item(seleccionado[0])['values'][0]
            conn = sqlite3.connect('consultorioDB.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nombre, marca, precio, precio_distribuidor, cantidad FROM productos WHERE id=?', (producto_id,))
            producto = cursor.fetchone()
            conn.close()
            if producto:
                self.entry_producto_nombre.delete(0, ctk.END)
                self.entry_producto_nombre.insert(0, producto[0])
                self.entry_producto_marca.delete(0, ctk.END)
                self.entry_producto_marca.insert(0, producto[1])
                self.entry_producto_precio.delete(0, ctk.END)
                self.entry_producto_precio.insert(0, producto[2])
                self.entry_producto_precio_distribuidor.delete(0, ctk.END)
                self.entry_producto_precio_distribuidor.insert(0, producto[3])
                self.entry_producto_cantidad.delete(0, ctk.END)
                self.entry_producto_cantidad.insert(0, producto[4])

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
        self.frame_plantillas.pack_forget()

    # Función para mostrar la vista de productos
    def mostrar_vista_productos(self):
        self.frame_productos.pack(fill='both', expand=True)
        self.frame_pacientes.pack_forget()
        self.frame_materiales.pack_forget()
        self.frame_plantillas.pack_forget()

    # Función para mostrar la vista de materiales de cirugía
    def mostrar_vista_materiales(self):
        self.frame_materiales.pack(fill='both', expand=True)
        self.frame_pacientes.pack_forget()
        self.frame_productos.pack_forget()
        self.frame_plantillas.pack_forget()
    
    #Funcion para mostrar la vista de plantillas
    def mostrar_vista_plantillas(self):
        self.frame_plantillas.pack(fill='both', expand=True)
        self.frame_pacientes.pack_forget()
        self.frame_productos.pack_forget()
        self.frame_materiales.pack_forget()

    def toggle_entry_state(self, entry, var):
        if var.get():
            entry.configure(state='normal')
        else:
            entry.configure(state='disabled')
            entry.delete(0, 'end')
    
    def calcular_precio(self):
        patient_id, patient_name = self.entry_paciente.get_selected()
        numero_calzado = self.entry_calzado.get()

        print(f"Calculando precio para paciente: {patient_name}, calzado: {numero_calzado}")

        if not patient_name or patient_name.strip() == "":
            messagebox.showwarning("Advertencia", "El nombre del paciente es obligatorio.")
            return None

        if not numero_calzado or numero_calzado.strip() == "":
            messagebox.showwarning("Advertencia", "El número de calzado es obligatorio.")
            return None

        try:
            numero_calzado = float(numero_calzado)
            total = 0
            productos_seleccionados = []
            
            for producto, widgets in self.entries.items():
                if widgets['check'].get():
                    cantidad = widgets['entry'].get()
                    if not cantidad.isdigit():
                        messagebox.showwarning("Advertencia", 
                                            f"Cantidad inválida para {producto}. Se ignorará en el cálculo.")
                        continue
                        
                    cantidad = int(cantidad)
                    if producto in ["Plantillas o Taloneras", "Virones y Cuñas", "Virones Corridos"]:
                        precio = self.obtener_precio(producto, numero_calzado)
                    else:
                        precio = self.precios.get(producto, 0)
                        
                    subtotal = cantidad * precio
                    total += subtotal
                    productos_seleccionados.append(f"{producto}: ${subtotal:.2f}")
                    
            print(f"Productos seleccionados: {productos_seleccionados}")
            print(f"Total calculado: ${total:.2f}")
            
            self.label_precio_total.configure(text=f"Precio Total: ${total:.2f}")
            return total
            
        except ValueError as e:
            print(f"Error al calcular precio: {e}")
            messagebox.showerror("Error", "Por favor, ingrese un número de calzado válido.")
            return None
        except Exception as e:
            print(f"Error inesperado al calcular precio: {e}")
            messagebox.showerror("Error", f"Error al calcular el precio: {str(e)}")
            return None

    def obtener_precio(self, producto, numero_calzado):
        """Obtiene el precio según el producto y número de calzado"""
        try:
            if producto not in self.precios:
                print(f"Producto no encontrado en la lista de precios: {producto}")
                return 0
            
            precios_producto = self.precios[producto]
            if isinstance(precios_producto, list):
                for (min_num, max_num), precio in precios_producto:
                    if min_num <= numero_calzado <= max_num:
                        return precio
                # Si no encuentra rango, usa el último precio
                return precios_producto[-1][1]
            else:
                return precios_producto
                
        except Exception as e:
            print(f"Error al obtener precio para {producto}: {e}")
            return 0
        
    def actualizar_estructura_plantillas(self):
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()
    
    def imprimir_estructura_plantillas(self):
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(plantillas)")
        columns = cursor.fetchall()
        estructura = "Estructura de la tabla plantillas:\n"
        for column in columns:
            estructura += f"{column}\n"
        conn.close()
        return estructura

    def guardar_plantilla(self):
        patient_id, patient_name = self.entry_paciente.get_selected()
        numero_calzado = self.entry_calzado.get()
        
        if not patient_name or not numero_calzado:
            messagebox.showwarning("Advertencia", "El nombre del paciente y el número de calzado son obligatorios.")
            return

        if not patient_id:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un paciente válido de la lista.")
            return

        if not numero_calzado.isdigit():
            messagebox.showwarning("Advertencia", "El número de calzado debe ser un número entero.")
            return

        # Recopilar información de productos seleccionados
        productos_seleccionados = []
        for producto, widgets in self.entries.items():
            if widgets['check'].get():
                cantidad = widgets['entry'].get()
                if cantidad and cantidad.isdigit():
                    productos_seleccionados.append(f"{producto}: {cantidad}")

        if not productos_seleccionados:
            messagebox.showwarning("Advertencia", "Por favor, seleccione al menos un producto y especifique su cantidad.")
            return

        precio = self.calcular_precio()
        if precio is None:
            messagebox.showwarning("Advertencia", "Por favor, calcule el precio antes de guardar.")
            return
        
        fecha_pedido = datetime.now().strftime('%Y-%m-%d')
        estado = self.estados_plantilla['PENDIENTE DE PAGO']
        resumen_plantilla = f"{patient_name} - {', '.join(productos_seleccionados)}"
        
        try:
            with sqlite3.connect('consultorioDB.db', timeout=20) as conn:
                cursor = conn.cursor()
                
                # Verificar la estructura de la tabla
                cursor.execute("PRAGMA table_info(plantillas)")
                columns = [column[1] for column in cursor.fetchall()]
                print(f"Columnas en la tabla plantillas: {columns}")
                
                # Insertar la nueva plantilla
                cursor.execute('''
                    INSERT INTO plantillas (
                        paciente_id, nombre, numero_calzado, precio, 
                        cantidad_pagada, fecha_pedido, estado, productos
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    patient_id, resumen_plantilla, numero_calzado, precio,
                    0, fecha_pedido, estado, ', '.join(productos_seleccionados)
                ))
                
                conn.commit()
                print("Plantilla guardada exitosamente en la base de datos")
                
                messagebox.showinfo("Éxito", "Plantilla guardada exitosamente.")
                self.limpiar_campos_plantillas()
                self.actualizar_lista_plantillas()
                
        except sqlite3.Error as e:
            print(f"Error de SQLite: {e}")
            messagebox.showerror("Error", f"Error al guardar la plantilla: {str(e)}")
        except Exception as e:
            print(f"Error inesperado: {e}")
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
        print("Función guardar_plantilla completada")

    def validar_entero(self, P, *args):
        if P.isdigit() or P == "":
            return True
        else:
            return False

    def abrir_ventana_editar_precios(self):
        ventana_precios = ctk.CTkToplevel(self.parent)
        ventana_precios.title("Editar Precios")
        ventana_precios.geometry("500x600")

        ventana_precios.transient(self.parent)
        ventana_precios.grab_set()
        ventana_precios.focus_set()

        frame_principal = ctk.CTkScrollableFrame(ventana_precios)
        frame_principal.pack(fill="both", expand=True)

        entries = {}

        for producto, valor in self.precios.items():
            ctk.CTkLabel(frame_principal, text=producto, font=("Arial", 14, "bold")).pack(pady=(20,10))
            if isinstance(valor, list):
                for i, (rango, precio) in enumerate(valor):
                    frame_rango = ctk.CTkFrame(frame_principal)
                    frame_rango.pack(fill="x", padx=10, pady=5)
                    ctk.CTkLabel(frame_rango, text=f"De {rango[0]} a {rango[1]}:").pack(side="left", padx=(0,10))
                    entry = ctk.CTkEntry(frame_rango, width=100)
                    entry.insert(0, str(precio))
                    entry.pack(side="right")
                    entries[(producto, i)] = entry
            else:
                frame_rango = ctk.CTkFrame(frame_principal)
                frame_rango.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(frame_rango, text="Precio:").pack(side="left", padx=(0,10))
                entry = ctk.CTkEntry(frame_rango, width=100)
                entry.insert(0, str(valor))
                entry.pack(side="right")
                entries[producto] = entry

        def guardar_cambios():
            for key, entry in entries.items():
                try:
                    nuevo_precio = int(entry.get())
                    if isinstance(key, tuple):
                        producto, indice = key
                        self.precios[producto][indice] = (self.precios[producto][indice][0], nuevo_precio)
                    else:
                        self.precios[key] = nuevo_precio
                except ValueError:
                    messagebox.showerror("Error", f"Precio inválido para {key}")
                    return
            messagebox.showinfo("Éxito", "Precios actualizados correctamente")
            ventana_precios.destroy()

        ctk.CTkButton(ventana_precios, text="Guardar Cambios", command=guardar_cambios).pack(pady=20)

        ventana_precios.update_idletasks()
        width = ventana_precios.winfo_width()
        height = ventana_precios.winfo_height()
        x = (ventana_precios.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana_precios.winfo_screenheight() // 2) - (height // 2)
        ventana_precios.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    # def limpiar_campos_plantillas(self):
    #     self.entry_paciente.delete(0, ctk.END)
    #     self.entry_calzado.delete(0, ctk.END)
    #     for widgets in self.entries.values():
    #         widgets['check'].set(False)
    #         widgets['entry'].configure(state='normal')
    #         widgets['entry'].delete(0, ctk.END)
    #         widgets['entry'].configure(state='disabled')
    #     self.label_precio_total.configure(text="Precio Total: $0")
    #     self.parent.update_idletasks()

    def limpiar_campos_plantillas(self):
        try:
            self.entry_paciente.delete(0, 'end')
            self.entry_calzado.delete(0, 'end')
            
            # Limpiar los checkboxes y entries
            for widgets in self.entries.values():
                widgets['check'].set(False)
                entry = widgets['entry']
                entry.configure(state='normal')
                entry.delete(0, 'end')
                entry.configure(state='disabled')
            
            # Resetear el precio total
            self.label_precio_total.configure(text="Precio Total: $0.00")
            
            print("Campos de plantillas limpiados")
            
            # Forzar actualización de la interfaz
            self.parent.update_idletasks()
            
        except Exception as e:
            print(f"Error al limpiar campos: {e}")


    def actualizar_lista_plantillas(self, event=None):
        for row in self.treeview_plantillas.get_children():
            self.treeview_plantillas.delete(row)
        
        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        
        filtro = self.filtro_plantillas.get()
        where_clause = ""
        
        if filtro == "Pendientes de pago":
            where_clause = f"WHERE p.estado = '{self.estados_plantilla['PENDIENTE DE PAGO']}'"
        elif filtro == "Pagadas":
            where_clause = f"WHERE p.estado = '{self.estados_plantilla['PAGADA']}'"
        
        query = f"""
            SELECT pac.nombre as nombre_paciente, p.numero_calzado, p.precio, p.cantidad_pagada, 
                p.productos, p.estado, p.fecha_pedido
            FROM plantillas p
            JOIN pacientes pac ON p.paciente_id = pac.id
            {where_clause}
            ORDER BY p.fecha_pedido DESC
        """
        
        cursor.execute(query)
        plantillas = cursor.fetchall()
        conn.close()
        
        for plantilla in plantillas:
            item = self.treeview_plantillas.insert("", END, values=plantilla)
            if plantilla[5] == self.estados_plantilla['PAGADA']:
                self.treeview_plantillas.item(item, tags=('pagada',))
            else:
                self.treeview_plantillas.item(item, tags=('pendiente',))

        self.treeview_plantillas.tag_configure('pagada', background='light green')
        self.treeview_plantillas.tag_configure('pendiente', background='light yellow')


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
        boton_vista_plantillas = ctk.CTkButton(frame_vista, text="Plantillas", command=self.mostrar_vista_plantillas)
        boton_vista_plantillas.pack(pady=5)
        boton_ayuda = ctk.CTkButton(frame_vista, text="Ayuda", command=self.mostrar_ayuda)
        boton_ayuda.pack(pady=20) 


        # Frame para la vista de Pacientes
        self.frame_pacientes = ctk.CTkFrame(self.parent)
        # Frame para la vista de Productos
        self.frame_productos = ctk.CTkFrame(self.parent)
        # Frame para la vista de Materiales de Cirugía
        self.frame_materiales = ctk.CTkFrame(self.parent)
        # Frame para la vista de Plantillas
        self.frame_plantillas = ctk.CTkFrame(self.parent)

        self.setup_frame_pacientes()
        self.setup_frame_productos()
        self.setup_frame_materiales()
        self.setup_frame_plantillas()

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
        Guía de Uso - Módulo de Inventario

        PANEL IZQUIERDO - NAVEGACIÓN PRINCIPAL
        -------------------------------------
        En el lado izquierdo encontrará los botones de navegación:
        • Pacientes: Gestión de información de pacientes
        • Productos: Control de inventario de productos
        • Materiales de Cirugía: Gestión de materiales quirúrgicos
        • Plantillas: Gestión y cálculo de plantillas ortopédicas

        1. SECCIÓN DE PACIENTES
        ----------------------
        Panel Izquierdo - Registro:
        • Campo "Nombre": Ingrese el nombre del paciente
        • Campo "Teléfono": Ingrese el número telefónico
        • Casilla "Es Distribuidor": Marque si el paciente es distribuidor
        
        Botones de Acción:
        • "Guardar Paciente": Registra un nuevo paciente
        • "Actualizar Paciente": Guarda cambios en paciente existente
        • "Eliminar Paciente": Elimina el registro seleccionado

        Panel Derecho - Lista de Pacientes:
        • Barra de búsqueda: Filtra pacientes por nombre
        • Tabla: Muestra ID, Nombre, Teléfono y estado de distribuidor
        • Doble clic: Carga datos del paciente para edición

        2. SECCIÓN DE PRODUCTOS
        ----------------------
        Panel Izquierdo - Registro:
        • Campo "Nombre": Nombre del producto
        • Campo "Marca": Marca del producto
        • Campo "Precio": Precio de venta regular
        • Campo "Precio Distribuidor": Precio especial para distribuidores
        • Campo "Cantidad": Unidades disponibles

        Botones de Acción:
        • "Guardar Producto": Registra nuevo producto
        • "Actualizar Producto": Guarda cambios en producto existente
        • "Eliminar Producto": Elimina el producto seleccionado

        Panel Derecho - Inventario:
        • Barra de búsqueda: Filtra productos por nombre
        • Tabla: Muestra todos los detalles del producto
        • Doble clic: Carga datos del producto para edición

        3. SECCIÓN DE MATERIALES DE CIRUGÍA
        ---------------------------------
        Panel Izquierdo - Registro:
        • Campo "Nombre": Nombre del material
        • Campo "Precio": Precio del material
        • Campo "Cantidad": Unidades disponibles

        Botones de Acción:
        • "Guardar Material": Registra nuevo material
        • "Actualizar Material": Guarda cambios en material existente
        • "Eliminar Material": Elimina el material seleccionado

        Panel Derecho - Inventario:
        • Barra de búsqueda: Filtra materiales por nombre
        • Tabla: Muestra detalles de los materiales
        • Doble clic: Carga datos del material para edición

        4. SECCIÓN DE PLANTILLAS
        ----------------------
        Panel Izquierdo - Calculadora:
        • Campo "Nombre del Paciente": Seleccione o busque paciente
        • Campo "Número de calzado": Ingrese el número
        • Lista de productos y servicios con casillas de verificación
        • Campo de cantidad para cada ítem seleccionado

        Botones de Acción:
        • "Calcular Precio": Muestra el total según selecciones
        • "Guardar Plantilla": Registra la plantilla calculada
        • "Editar Precios": Modifica precios base del sistema

        Panel Derecho - Historial:
        • Filtro de estado: Todas/Pendientes/Pagadas
        • Tabla: Muestra historial de plantillas
        • Información detallada de cada registro

        CONSEJOS GENERALES
        -----------------
        • Use la barra de búsqueda para encontrar registros rápidamente
        • Doble clic en cualquier tabla carga los datos para edición
        • Todos los montos se muestran en pesos mexicanos
        • Verifique los datos antes de guardar o actualizar
        • El sistema actualiza automáticamente los inventarios al realizar ventas
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
        
    def setup_frame_pacientes(self):
        frame_form_pacientes = ctk.CTkFrame(self.frame_pacientes)
        frame_form_pacientes.pack(side='left', fill='both', expand=True, padx=20, pady=20)

        label_pacientes = ctk.CTkLabel(frame_form_pacientes, text="Registro de Pacientes", font=("Arial", 18, "bold"))
        label_pacientes.pack(pady=(0, 20))

        # Campos de entrada
        campos = [("Nombre:", "entry_nombre"), ("Teléfono:", "entry_telefono")]
        for label_text, entry_name in campos:
            frame = ctk.CTkFrame(frame_form_pacientes)
            frame.pack(fill='x', pady=5)
            label = ctk.CTkLabel(frame, text=label_text, font=("Arial", 12))
            label.pack(side='left', padx=(0, 10))
            
            if entry_name == "entry_telefono":
                vcmd = self.parent.register(self.validar_telefono)
                setattr(self, entry_name, ctk.CTkEntry(
                    frame, 
                    width=200,
                    validate='key',
                    validatecommand=(vcmd, '%P'),
                    placeholder_text="Ingrese solo números"
                ))
            else:
                setattr(self, entry_name, ctk.CTkEntry(frame, width=200))
            
            getattr(self, entry_name).pack(side='left', expand=True, fill='x')
            
        # Checkbox para distribuidor
        frame_distribuidor = ctk.CTkFrame(frame_form_pacientes)
        frame_distribuidor.pack(fill='x', pady=5)
        self.var_es_distribuidor = ctk.BooleanVar()
        self.check_es_distribuidor = ctk.CTkCheckBox(frame_distribuidor, text="Es Distribuidor", variable=self.var_es_distribuidor)
        self.check_es_distribuidor.pack(side='left')

        # Botones
        frame_botones = ctk.CTkFrame(frame_form_pacientes)
        frame_botones.pack(fill='x', pady=20)
        ctk.CTkButton(frame_botones, text="Guardar Paciente", command=self.guardar_paciente).pack(side='left', padx=(0, 10))
        ctk.CTkButton(frame_botones, text="Actualizar Paciente", command=self.actualizar_paciente).pack(side='left', padx=(0, 10))
        ctk.CTkButton(frame_botones, text="Eliminar Paciente", command=self.eliminar_paciente).pack(side='left')

        # Lista de pacientes
        frame_lista_pacientes = ctk.CTkFrame(self.frame_pacientes)
        frame_lista_pacientes.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        label_lista_pacientes = ctk.CTkLabel(frame_lista_pacientes, text="Lista de Pacientes", font=("Arial", 16, "bold"))
        label_lista_pacientes.pack(pady=(0, 10))

        # Búsqueda
        frame_busqueda = ctk.CTkFrame(frame_lista_pacientes)
        frame_busqueda.pack(fill='x', pady=5)
        ctk.CTkLabel(frame_busqueda, text="Buscar:").pack(side='left', padx=(0, 10))
        self.entry_buscar_paciente = ctk.CTkEntry(frame_busqueda)
        self.entry_buscar_paciente.pack(side='left', expand=True, fill='x')
        self.entry_buscar_paciente.bind("<KeyRelease>", self.filtrar_pacientes)

        # Treeview
        self.treeview_pacientes = ttk.Treeview(frame_lista_pacientes, columns=("ID", "Nombre", "Teléfono", "Es Distribuidor"), show='headings')
        for col in self.treeview_pacientes['columns']:
            self.treeview_pacientes.heading(col, text=col)
        self.treeview_pacientes.pack(pady=5, fill='both', expand=True)
        self.treeview_pacientes.bind("<Double-1>", self.cargar_datos_paciente)

    def validar_numero(self, char):
        if char == "":
            return True    # Permitir borrar
        return char.isdigit()   # Retornar True solo si es número

    def setup_frame_productos(self):
        frame_form_productos = ctk.CTkFrame(self.frame_productos)
        frame_form_productos.pack(side='left', fill='both', expand=True, padx=20, pady=20)

        label_productos = ctk.CTkLabel(frame_form_productos, text="Inventario de Productos", font=("Arial", 18, "bold"))
        label_productos.pack(pady=(0, 20))

        # Campos de entrada
        campos = [("Nombre:", "entry_producto_nombre"), ("Marca:", "entry_producto_marca"),
                ("Precio:", "entry_producto_precio"), ("Precio Distribuidor:", "entry_producto_precio_distribuidor"),
                ("Cantidad:", "entry_producto_cantidad")]
        for label_text, entry_name in campos:
            frame = ctk.CTkFrame(frame_form_productos)
            frame.pack(fill='x', pady=5)
            label = ctk.CTkLabel(frame, text=label_text, font=("Arial", 12))
            label.pack(side='left', padx=(0, 10))
            setattr(self, entry_name, ctk.CTkEntry(frame, width=200))
            getattr(self, entry_name).pack(side='left', expand=True, fill='x')

        # Botones
        frame_botones = ctk.CTkFrame(frame_form_productos)
        frame_botones.pack(fill='x', pady=20)
        ctk.CTkButton(frame_botones, text="Guardar Producto", command=self.guardar_producto).pack(side='left', padx=(0, 10))
        ctk.CTkButton(frame_botones, text="Actualizar Producto", command=self.actualizar_producto).pack(side='left', padx=(0, 10))
        ctk.CTkButton(frame_botones, text="Eliminar Producto", command=self.eliminar_producto).pack(side='left')

        # Lista de productos
        frame_lista_productos = ctk.CTkFrame(self.frame_productos)
        frame_lista_productos.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        label_lista_productos = ctk.CTkLabel(frame_lista_productos, text="Lista de Productos", font=("Arial", 16, "bold"))
        label_lista_productos.pack(pady=(0, 10))

        # Búsqueda
        frame_busqueda = ctk.CTkFrame(frame_lista_productos)
        frame_busqueda.pack(fill='x', pady=5)
        ctk.CTkLabel(frame_busqueda, text="Buscar:").pack(side='left', padx=(0, 10))
        self.entry_buscar_producto = ctk.CTkEntry(frame_busqueda)
        self.entry_buscar_producto.pack(side='left', expand=True, fill='x')
        self.entry_buscar_producto.bind("<KeyRelease>", self.filtrar_productos)

        # Treeview
        self.treeview_productos = ttk.Treeview(frame_lista_productos, columns=("ID", "Nombre", "Marca", "Precio", "Precio Distribuidor", "Cantidad"), show='headings')
        for col in self.treeview_productos['columns']:
            self.treeview_productos.heading(col, text=col)
        self.treeview_productos.pack(pady=5, fill='both', expand=True)
        self.treeview_productos.bind("<Double-1>", self.cargar_datos_producto)

    def setup_frame_materiales(self):
        frame_form_materiales = ctk.CTkFrame(self.frame_materiales)
        frame_form_materiales.pack(side='left', fill='both', expand=True, padx=20, pady=20)

        label_materiales = ctk.CTkLabel(frame_form_materiales, text="Materiales de Cirugía", font=("Arial", 18, "bold"))
        label_materiales.pack(pady=(0, 20))

        # Campos de entrada
        campos = [("Nombre:", "entry_material_nombre"), ("Precio:", "entry_material_precio"), ("Cantidad:", "entry_material_cantidad")]
        for label_text, entry_name in campos:
            frame = ctk.CTkFrame(frame_form_materiales)
            frame.pack(fill='x', pady=5)
            label = ctk.CTkLabel(frame, text=label_text, font=("Arial", 12))
            label.pack(side='left', padx=(0, 10))
            setattr(self, entry_name, ctk.CTkEntry(frame, width=200))
            getattr(self, entry_name).pack(side='left', expand=True, fill='x')

        # Botones
        frame_botones = ctk.CTkFrame(frame_form_materiales)
        frame_botones.pack(fill='x', pady=20)
        ctk.CTkButton(frame_botones, text="Guardar Material", command=self.guardar_material).pack(side='left', padx=(0, 10))
        ctk.CTkButton(frame_botones, text="Actualizar Material", command=self.actualizar_material).pack(side='left', padx=(0, 10))
        ctk.CTkButton(frame_botones, text="Eliminar Material", command=self.eliminar_material).pack(side='left')

        # Lista de materiales
        frame_lista_materiales = ctk.CTkFrame(self.frame_materiales)
        frame_lista_materiales.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        label_lista_materiales = ctk.CTkLabel(frame_lista_materiales, text="Lista de Materiales", font=("Arial", 16, "bold"))
        label_lista_materiales.pack(pady=(0, 10))

        # Búsqueda
        frame_busqueda = ctk.CTkFrame(frame_lista_materiales)
        frame_busqueda.pack(fill='x', pady=5)
        ctk.CTkLabel(frame_busqueda, text="Buscar:").pack(side='left', padx=(0, 10))
        self.entry_buscar_material = ctk.CTkEntry(frame_busqueda)
        self.entry_buscar_material.pack(side='left', expand=True, fill='x')
        self.entry_buscar_material.bind("<KeyRelease>", self.filtrar_materiales)

        # Treeview
        self.treeview_materiales = ttk.Treeview(frame_lista_materiales, columns=("ID", "Nombre", "Precio", "Cantidad"), show='headings')
        for col in self.treeview_materiales['columns']:
            self.treeview_materiales.heading(col, text=col)
        self.treeview_materiales.pack(pady=5, fill='both', expand=True)
        self.treeview_materiales.bind("<Double-1>", self.cargar_datos_material)
    
    def setup_frame_plantillas(self):
        self.frame_plantillas = ctk.CTkFrame(self.parent)
        self.frame_plantillas.pack(fill='both', expand=True, padx=10, pady=10)

        # Frame izquierdo para el calculador de precio
        frame_calculador = ctk.CTkFrame(self.frame_plantillas)
        frame_calculador.pack(side='left', fill='both', expand=True, padx=(0, 5), pady=5)

        label_plantillas = ctk.CTkLabel(frame_calculador, text="Calculador de Precio para Productos Ortopédicos", font=("Arial", 18, "bold"))
        label_plantillas.pack(pady=(0, 10))

        # Campos obligatorios
        frame_obligatorio = ctk.CTkFrame(frame_calculador)
        frame_obligatorio.pack(fill='x', pady=5)
        
        label_paciente = ctk.CTkLabel(frame_obligatorio, text="Nombre del Paciente:", font=("Arial", 12, "bold"))
        label_paciente.pack(side='left', padx=(0, 5))

        conn = sqlite3.connect('consultorioDB.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM pacientes")
        pacientes = cursor.fetchall()
        conn.close()

        # Crear el campo de autocompletado
        self.entry_paciente = AutocompleteEntry(frame_obligatorio, completions=pacientes, width=150)
        self.entry_paciente.pack(side='left', padx=(0,10))

        label_calzado = ctk.CTkLabel(frame_obligatorio, text="Número de calzado:", font=("Arial", 12, "bold"))
        label_calzado.pack(side='left', padx=(0, 5))

        vcmd = (self.parent.register(self.validar_entero), '%P', '%d', '%i', '%s', '%S', '%v', '%V', '%W')
        self.entry_calzado = ctk.CTkEntry(frame_obligatorio, width=50, validate="key", validatecommand=vcmd)
        self.entry_calzado.pack(side='left')

        # Campos opcionales
        label_opcionales = ctk.CTkLabel(frame_calculador, text="Productos y Servicios (opcional)", font=("Arial", 14, "bold"))
        label_opcionales.pack(pady=(10, 5))

        self.entries = {}
        productos = [
            "Plantillas o Taloneras", "Virones y Cuñas", "Virones Corridos", "Mangueras Derrotadoras",
            "Adaptaciones adicionales", "Aumento a calzado hasta 1 CM", "Centímetro extra",
            "Plantilla o Talonera aumento de 1 CM", "CM extra", "Plantilla o Talonera para espolón",
            "Cambio de calzado a manguera"
        ]

        for producto in productos:
            frame_producto = ctk.CTkFrame(frame_calculador)
            frame_producto.pack(fill='x', pady=2)
            
            var = ctk.BooleanVar()
            check = ctk.CTkCheckBox(frame_producto, text=producto, variable=var)
            check.pack(side='left', padx=(0, 5))
            
            entry = ctk.CTkEntry(frame_producto, width=70, placeholder_text="Cantidad")
            entry.pack(side='right', padx=(5, 0))
            entry.configure(state='disabled')
            
            self.entries[producto] = {'check': var, 'entry': entry}
            
            var.trace('w', lambda *args, e=entry, v=var: self.toggle_entry_state(e, v))

        # Botones y etiqueta de precio
        frame_botones = ctk.CTkFrame(frame_calculador)
        frame_botones.pack(fill='x', pady=10)
        
        boton_calcular = ctk.CTkButton(frame_botones, text="Calcular Precio", command=self.calcular_precio, width=100)
        boton_calcular.pack(side='left', padx=(0, 5))
        
        self.label_precio_total = ctk.CTkLabel(frame_botones, text="Precio Total: $0", font=("Arial", 12, "bold"))
        self.label_precio_total.pack(side='left', padx=(0, 5))
        
        boton_guardar_plantilla = ctk.CTkButton(frame_botones, text="Guardar Plantilla", command=self.guardar_plantilla, width=100)
        boton_guardar_plantilla.pack(side='left', padx=(0, 5))
        
        boton_editar_precios = ctk.CTkButton(frame_botones, text="Editar Precios", command=self.abrir_ventana_editar_precios, width=100)
        boton_editar_precios.pack(side='left')

        # Frame derecho para la lista de plantillas
        frame_lista_plantillas = ctk.CTkFrame(self.frame_plantillas)
        frame_lista_plantillas.pack(side='right', fill='both', expand=True, padx=(5, 0), pady=5)

        label_lista_plantillas = ctk.CTkLabel(frame_lista_plantillas, text="Lista de Plantillas:", font=("Arial", 16, "bold"))
        label_lista_plantillas.pack(pady=(0, 5))

        # Frame para el filtro
        frame_filtro = ctk.CTkFrame(frame_lista_plantillas)
        frame_filtro.pack(fill='x', pady=5)

        ctk.CTkLabel(frame_filtro, text="Mostrar:").pack(side='left', padx=5)
        self.filtro_plantillas = ctk.StringVar(value="Todas")
        filtro_combo = ctk.CTkComboBox(frame_filtro, values=["Todas", "Pendientes de pago", "Pagadas"], 
                                    variable=self.filtro_plantillas, command=self.actualizar_lista_plantillas)
        filtro_combo.pack(side='left', padx=5)

        # Treeview para la lista de plantillas
        self.treeview_plantillas = ttk.Treeview(frame_lista_plantillas, columns=(
            "Paciente", "Número de Calzado", "Precio", "Cantidad Pagada", "Productos", "Estado", "Fecha de Pedido"
        ), show='headings')

        # Configurar las columnas del Treeview
        for col in self.treeview_plantillas['columns']:
            self.treeview_plantillas.heading(col, text=col)
            self.treeview_plantillas.column(col, width=100)  # Ajusta el ancho según sea necesario

        self.treeview_plantillas.pack(pady=5, fill='both', expand=True)





