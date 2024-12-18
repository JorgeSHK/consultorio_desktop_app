import customtkinter as ctk
from inventario import Inventario
from compraventa import CompraVenta
from resumencobros import ResumenCobros
from historial_pacientes import HistorialPacientes
from database import conectar_db, cerrar_db

class MainApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Sistema de Gestión de Consultorio")
        self.root.geometry("2000x1000")
        
        self.conn = conectar_db()  # Conectar a la base de datos

        self.create_widgets()

    def create_widgets(self):
        self.tab_view = ctk.CTkTabview(self.root)
        self.tab_view.pack(fill='both', expand=True, padx=10, pady=10)

        tab_inventario = self.tab_view.add("Inventario")
        tab_compraventa = self.tab_view.add("Compra/Venta")
        tab_resumen_cobros = self.tab_view.add("Resumen de Cobros")
        tab_historial = self.tab_view.add("Historial de Pacientes")

        self.inventario = Inventario(tab_inventario, self.conn)
        self.compraventa = CompraVenta(tab_compraventa, self.inventario, self.conn)
        self.resumen_cobros = ResumenCobros(tab_resumen_cobros, self.conn)
        self.historial = HistorialPacientes(tab_historial, self.conn)

    def run(self):
        self.root.mainloop()

    def __del__(self):
        if hasattr(self, 'conn'):
            cerrar_db(self.conn) 

if __name__ == "__main__":
    app = MainApp()
    app.run()