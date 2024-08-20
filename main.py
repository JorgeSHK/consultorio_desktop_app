import customtkinter as ctk
from inventario import Inventario
from compraventa import CompraVenta
from resumencobros import ResumenCobros

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Consultorio")
        self.root.geometry("1800x1000")
        self.create_widgets()

    def create_widgets(self):
        self.tab_view = ctk.CTkTabview(self.root)
        self.tab_view.pack(fill='both', expand=True, padx=10, pady=10)

        tab_inventario = self.tab_view.add("Inventario")
        tab_compraventa = self.tab_view.add("Compra/Venta")
        tab_resumen_cobros = self.tab_view.add("Resumen de Cobros")  # Nueva pestaña

        self.inventario = Inventario(tab_inventario)
        self.compraventa = CompraVenta(tab_compraventa, self.inventario)
        self.resumen_cobros = ResumenCobros(tab_resumen_cobros)  # Instanciar la nueva clase

if __name__ == "__main__":
    root = ctk.CTk()
    app = MainApp(root)
    root.mainloop()
