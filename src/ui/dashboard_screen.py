import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from src.ui.screens import BaseScreen
from datetime import datetime
import locale

if TYPE_CHECKING:
    from main import MainApplication

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')


class DashboardScreen(BaseScreen):
    """
    Tela principal da aplicação, exibindo um dashboard com métricas financeiras.
    """
    def __init__(self, parent: ttk.Frame, controller: "MainApplication", **kwargs: Any) -> None:
        super().__init__(parent, controller, **kwargs)
        self.widgets: Dict[str, ttk.Label] = {}
        self._create_widgets()
        
    def _create_widgets(self) -> None:
        """Cria e posiciona os widgets do dashboard."""
        self._create_label(self, "Dashboard Financeiro", font_size=24, bold=True).pack(pady=(40, 10))
        
        metrics_frame = ttk.Frame(self)
        metrics_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Colunas para as métricas
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)
        metrics_frame.columnconfigure(2, weight=1)

        # Total de Entradas
        self.widgets["entradas_label"] = self._create_metric_widget(metrics_frame, "Total de Entradas", row=0, col=0)
        # Total de Saídas
        self.widgets["saidas_label"] = self._create_metric_widget(metrics_frame, "Total de Saídas", row=0, col=1)
        # Saldo Líquido
        self.widgets["saldo_label"] = self._create_metric_widget(metrics_frame, "Saldo Líquido", row=0, col=2)
        
    def _create_metric_widget(self, parent: ttk.Frame, title: str, row: int, col: int) -> ttk.Label:
        """Cria um widget padrão para exibição de métricas."""
        frame = ttk.Frame(parent, relief=tk.RAISED, padding=10)
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        self._create_label(frame, title, font_size=16, bold=True).pack()
        value_label = self._create_label(frame, "...", font_size=20)
        value_label.pack(pady=(10, 0))
        
        return value_label

    def load_data(self, all_lancamentos: Optional[List[Any]] = None) -> None:
        """Carrega e atualiza os dados do dashboard."""
        if all_lancamentos is None:
            all_lancamentos = self.controller.db_manager.get_lancamentos()
            
        summary = self.controller.financial_analytics.get_financial_summary(all_lancamentos)
        
        total_entradas_br = locale.currency(summary['total_entradas'], grouping=True, symbol=True)
        total_saidas_br = locale.currency(summary['total_saidas'], grouping=True, symbol=True)
        saldo_br = locale.currency(summary['saldo_liquido'], grouping=True, symbol=True)
        
        self.widgets["entradas_label"].config(text=total_entradas_br)
        self.widgets["saidas_label"].config(text=total_saidas_br)
        
        saldo = summary['saldo_liquido']
        self.widgets["saldo_label"].config(text=saldo_br)
        
        if saldo > 0:
            self.widgets["saldo_label"].config(foreground="#28a745") # verde
        elif saldo < 0:
            self.widgets["saldo_label"].config(foreground="#dc3545") # vermelho
        else:
            self.widgets["saldo_label"].config(foreground="white" if self.controller.current_theme == "dark" else "black")