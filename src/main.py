import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
from src.database.manager import DatabaseManager
from src.ui.screens import WelcomeScreen, GenericCadastroScreen, NotaFiscalEntryScreen, RelatorioScreen
from src.ui.dashboard_screen import DashboardScreen
from src.analysis.analytics import FinancialAnalytics

class MainApplication(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Sistema de Controle de Notas Fiscais")
        self.geometry("1400x900")
        
        self.db_manager = DatabaseManager()
        self.db_manager.corrigir_datas()
        self.financial_analytics = FinancialAnalytics(self.db_manager)
        
        self.current_theme = "dark"
        self.style = ttk.Style()
        
        self._configure_styles()
        self._create_main_container_frame()
        self.screens: Dict[str, ttk.Frame] = self._initialize_screens()
        
        self.set_theme(self.current_theme)
        self._create_menu()
        
        self.show_screen("Dashboard")

    def _configure_styles(self) -> None:
        """Configura os estilos globais da aplicação."""
        self.style.theme_use('clam')
        
    def _create_menu(self) -> None:
        """Cria e configura a barra de menu."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        menu_dash = tk.Menu(menubar, tearoff=0)
        menu_dash.add_command(label="Dashboard", command=lambda: self.show_screen("Dashboard"))
        menubar.add_cascade(label="Dashboard", menu=menu_dash)

        menu_cad = tk.Menu(menubar, tearoff=0)
        menu_cad.add_command(label="Fornecedor", command=lambda: self.show_screen("CadastroFornecedor"))
        menu_cad.add_command(label="Loja", command=lambda: self.show_screen("CadastroLoja"))
        menubar.add_cascade(label="Cadastros", menu=menu_cad)

        menu_mov = tk.Menu(menubar, tearoff=0)
        menu_mov.add_command(label="Lançamento de NF", command=lambda: self.show_screen("EntradaNotaFiscal"))
        menu_mov.add_command(label="Relatório", command=lambda: self.show_screen("RelatorioNotas"))
        menubar.add_cascade(label="Movimentações", menu=menu_mov)
        
        menu_tema = tk.Menu(menubar, tearoff=0)
        menu_tema.add_command(label="Tema Claro", command=lambda: self.set_theme("light"))
        menu_tema.add_command(label="Tema Escuro", command=lambda: self.set_theme("dark"))
        menubar.add_cascade(label="Tema", menu=menu_tema)

    def _create_main_container_frame(self) -> None:
        """Cria o frame principal para as telas."""
        self.container = ttk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def _initialize_screens(self) -> Dict[str, ttk.Frame]:
        """Instancia as telas e as posiciona na grade, retornando-as em um dicionário."""
        screens = {
            "Dashboard": DashboardScreen(self.container, self),
            "Welcome": WelcomeScreen(self.container, self),
            "CadastroFornecedor": GenericCadastroScreen(self.container, self, "Cadastro de Fornecedor", "fornecedores"),
            "CadastroLoja": GenericCadastroScreen(self.container, self, "Cadastro de Loja", "lojas"),
            "EntradaNotaFiscal": NotaFiscalEntryScreen(self.container, self),
            "RelatorioNotas": RelatorioScreen(self.container, self),
        }
        
        for screen in screens.values():
            screen.grid(row=0, column=0, sticky="nsew")

        return screens

    def show_screen(self, screen_name: str) -> None:
        if frame := self.screens.get(screen_name):
            all_lancamentos = self.db_manager.get_lancamentos()
            
            if screen_name == "Dashboard" and hasattr(frame, 'load_data'):
                frame.load_data(all_lancamentos)
            elif hasattr(frame, 'load_data'):
                frame.load_data()
            
            frame.tkraise()

    def set_theme(self, theme_name: str) -> None:
        """Define o tema da aplicação e propaga a mudança."""
        self.current_theme = theme_name
        
        self.config(bg="#2b2b2b" if theme_name == "dark" else "#F0F0F0")
        
        base_style = {
            "TFrame": {"background": "#333333" if theme_name == "dark" else "#F0F0F0"},
            "TLabel": {"background": "#333333" if theme_name == "dark" else "#F0F0F0", "foreground": "white" if theme_name == "dark" else "black"},
            "TButton": {"background": "#555555" if theme_name == "dark" else "#007bff", "foreground": "white"},
            "Treeview": {"background": "#555555" if theme_name == "dark" else "white", "foreground": "white" if theme_name == "dark" else "black", "fieldbackground": "#555555" if theme_name == "dark" else "white"},
            "Treeview.Heading": {"background": "#666666" if theme_name == "dark" else "#e0e0e0", "foreground": "white" if theme_name == "dark" else "black"},
            "TCombobox": {"fieldbackground": "#555555" if theme_name == "dark" else "white", "foreground": "white" if theme_name == "dark" else "black"},
        }

        for style_name, conf in base_style.items():
            self.style.configure(style_name, **conf)
        
        self.style.map("TButton", background=[('active', '#777777' if theme_name == "dark" else '#0056b3')])
        self.style.map("Treeview", background=[("selected", "grey" if theme_name == "dark" else "#a0a0a0")], foreground=[("selected", "white" if theme_name == "dark" else "black")])

        self.event_generate("<<ThemeChanged>>")

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()