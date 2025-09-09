import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from src.database.manager import LancamentoData
from datetime import datetime
import collections

if TYPE_CHECKING:
    from main import MainApplication

class BaseScreen(ttk.Frame):
    """Classe base para todas as telas da aplicação."""
    def __init__(self, parent: ttk.Frame, controller: "MainApplication", **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.controller = controller
        self.bind("<<ThemeChanged>>", self._on_theme_changed)

    def _create_label(self, parent: ttk.Frame, text: str, font_size: int = 12, bold: bool = False) -> ttk.Label:
        """Cria e retorna um Label com estilos padronizados."""
        font_style = ("Segoe UI", font_size, "bold") if bold else ("Segoe UI", font_size)
        return ttk.Label(parent, text=text, font=font_style, style="Custom.TLabel")

    def _on_theme_changed(self, event: tk.Event) -> None:
        """Atualiza o tema dos widgets internos da tela."""
        style = ttk.Style()
        bg = style.lookup("TFrame", "background")
        fg = style.lookup("TLabel", "foreground")
        self.config(style="Custom.TFrame")
        style.configure("Custom.TFrame", background=bg)
        style.configure("Custom.TLabel", background=bg, foreground=fg)

class WelcomeScreen(BaseScreen):
    """Tela de boas-vindas do sistema com lançamentos recentes."""

    def __init__(self, parent: ttk.Frame, controller: "MainApplication", **kwargs: Any) -> None:
        super().__init__(parent, controller, **kwargs)
        self._create_widgets()
        self.load_data()

    def _create_widgets(self) -> None:
        """Cria e organiza os widgets da tela."""
        self._create_label(self, "Sistema de Controle de Notas Fiscais", font_size=24, bold=True).pack(pady=(40, 10))
        self._create_label(self, "Últimos Lançamentos", font_size=16).pack(pady=(20, 10))

        cols = ("ID", "Loja", "Fornecedor", "Valor", "Data")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
    def load_data(self) -> None:
        """Carrega e exibe os lançamentos mais recentes."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            entries: List[LancamentoData] = self.controller.db_manager.get_lancamentos(limit=10)
            for entry in entries:
                valor_br = f"R$ {entry['valor']:.2f}".replace('.', ',')
                data_br = datetime.strptime(entry['data_lancamento'], '%Y-%m-%d').strftime('%d/%m/%Y')
                self.tree.insert("", tk.END, values=(
                    entry['id'], entry['loja'], entry['fornecedor'], valor_br, data_br
                ))
        except RuntimeError as e:
            messagebox.showerror("Erro de Banco de Dados", str(e))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar lançamentos: {e}")

class GenericCadastroScreen(BaseScreen):
    """Tela genérica para cadastro de Fornecedores e Lojas."""

    def __init__(self, parent: ttk.Frame, controller: "MainApplication", title: str, table_name: str, **kwargs: Any) -> None:
        super().__init__(parent, controller, **kwargs)
        self.title_text = title
        self.table_name = table_name
        self._create_widgets()
        self.load_data()

    def _create_widgets(self) -> None:
        """Cria e organiza os widgets da tela de cadastro."""
        self._create_label(self, self.title_text, font_size=24, bold=True).pack(pady=(20, 10))

        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10)

        self._create_label(form_frame, "Nome:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.nome_entry = ttk.Entry(form_frame, width=50)
        self.nome_entry.grid(row=0, column=1, padx=5, pady=5)

        self._create_label(form_frame, "CNPJ:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cnpj_entry = ttk.Entry(form_frame, width=50)
        self.cnpj_entry.grid(row=1, column=1, padx=5, pady=5)

        save_button = ttk.Button(form_frame, text="Salvar", command=self._save_data)
        save_button.grid(row=2, column=1, padx=5, pady=10, sticky="e")

        self.tree = ttk.Treeview(self, columns=("Nome", "CNPJ"), show="headings")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("CNPJ", text="CNPJ")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    def _save_data(self) -> None:
        """Salva os dados de um novo registro."""
        nome, cnpj = self.nome_entry.get().strip(), self.cnpj_entry.get().strip()

        if not nome or not cnpj:
            messagebox.showerror("Erro de Validação", "Nome e CNPJ são obrigatórios.")
            return

        try:
            self.controller.db_manager.insert_entity(self.table_name, nome, cnpj)
            messagebox.showinfo("Sucesso", f"{self.title_text} cadastrado com sucesso!")
            self.load_data()
            self.nome_entry.delete(0, tk.END)
            self.cnpj_entry.delete(0, tk.END)
        except RuntimeError as e:
            if "UNIQUE constraint failed" in str(e):
                messagebox.showerror("Erro de Duplicação", "Nome ou CNPJ já existem no banco de dados.")
            else:
                messagebox.showerror("Erro de Banco de Dados", str(e))
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")
            
    def load_data(self) -> None:
        """Carrega e exibe os dados no Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            data = self.controller.db_manager.get_entities(self.table_name)
            for item in data:
                self.tree.insert("", tk.END, values=item)
        except RuntimeError as e:
            messagebox.showerror("Erro de Banco de Dados", str(e))
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Erro ao carregar dados: {e}")

class NotaFiscalEntryScreen(BaseScreen):
    """Tela para o lançamento de notas fiscais."""

    def __init__(self, parent: ttk.Frame, controller: "MainApplication", **kwargs: Any) -> None:
        super().__init__(parent, controller, **kwargs)
        self._fornecedores_map: Dict[str, str] = {}
        self._lojas_map: Dict[str, str] = {}
        self.entries: Dict[str, Any] = {}
        self._create_widgets()
    
    def load_data(self) -> None:
        """Carrega os Comboboxes com os dados do banco."""
        try:
            lojas = self.controller.db_manager.get_entities("lojas")
            fornecedores = self.controller.db_manager.get_entities("fornecedores")

            self._lojas_map = {nome: cnpj for nome, cnpj in lojas}
            self._fornecedores_map = {nome: cnpj for nome, cnpj in fornecedores}

            self.entries["loja"]["values"] = list(self._lojas_map.keys())
            self.entries["fornecedor"]["values"] = list(self._fornecedores_map.keys())
        except RuntimeError as e:
            messagebox.showerror("Erro de Banco de Dados", str(e))
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Não foi possível carregar as listas: {e}")

    def _create_widgets(self) -> None:
        """Cria e organiza os widgets de entrada de notas fiscais."""
        self._create_label(self, "Lançamento de Nota Fiscal", font_size=24, bold=True).pack(pady=(20, 10))

        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10, padx=20)
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)

        fields = [
            ("Loja", "loja", "combo"), ("Fornecedor", "fornecedor", "combo"),
            ("Documento", "documento", "entry"), ("NFE", "nfe", "entry"),
            ("Chave NFE", "chave_nfe", "entry"), ("Valor", "valor", "entry"),
            ("Data Lançamento (DD/MM/AAAA)", "data_lancamento", "entry"),
            ("Vencimento (DD/MM/AAAA)", "vencimento", "entry"),
            ("Observação", "observacao", "entry"), ("Tipo", "tipo", "combo")
        ]
        
        for i, (label, name, type) in enumerate(fields):
            row, col = i // 2, (i % 2) * 2
            self._create_label(form_frame, label).grid(row=row, column=col, padx=5, pady=5, sticky="w")
            if type == "combo":
                self.entries[name] = ttk.Combobox(form_frame, state="readonly", width=40)
            else:
                self.entries[name] = ttk.Entry(form_frame, width=40)
            self.entries[name].grid(row=row, column=col + 1, padx=5, pady=5, sticky="ew")

        self.entries["tipo"]["values"] = ["Entrada", "Saída"]

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=20)
        
        save_button = ttk.Button(button_frame, text="Salvar Lançamento", command=self._save_lancamento)
        save_button.pack(side=tk.LEFT, padx=5)

        import_button = ttk.Button(button_frame, text="Importar XML", command=self._importar_xml_file)
        import_button.pack(side=tk.LEFT, padx=5)

    def _importar_xml_file(self) -> None:
        """Abre uma janela de diálogo para selecionar um arquivo XML e preenche a tela."""
        xml_path = filedialog.askopenfilename(
            title="Selecione o arquivo XML da Nota Fiscal",
            filetypes=(("Arquivos XML", "*.xml"), ("Todos os arquivos", "*.*"))
        )
        if not xml_path:
            return

        try:
            nfe_data = self.controller.xml_importer.import_xml(xml_path)
            if nfe_data:
                self._clear_entries()
                
                data_lancamento_br = datetime.strptime(nfe_data.get('data_lancamento', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if nfe_data.get('data_lancamento') else ''
                valor_br = str(nfe_data.get('valor', '')).replace('.', ',')

                self.entries["loja"].set(nfe_data.get("loja", ""))
                self.entries["fornecedor"].set(nfe_data.get("fornecedor", ""))
                self.entries["documento"].insert(0, nfe_data.get("documento", ""))
                self.entries["nfe"].insert(0, nfe_data.get("nfe", ""))
                self.entries["chave_nfe"].insert(0, nfe_data.get("chave_nfe", ""))
                self.entries["valor"].insert(0, valor_br)
                self.entries["data_lancamento"].insert(0, data_lancamento_br)
                self.entries["tipo"].set(nfe_data.get("tipo", "Entrada"))
                
                messagebox.showinfo("Sucesso", "Dados do XML importados com sucesso!")
            else:
                messagebox.showerror("Erro de Importação", "Não foi possível processar o arquivo XML. Verifique o formato do arquivo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")


    def _save_lancamento(self) -> None:
        """Coleta e salva os dados do formulário."""
        data_to_save: LancamentoData = {
            'loja': self.entries["loja"].get(),
            'cnpj_loja': self._lojas_map.get(self.entries["loja"].get(), ""),
            'fornecedor': self.entries["fornecedor"].get(),
            'cnpj_forn': self._fornecedores_map.get(self.entries["fornecedor"].get(), ""),
            'documento': self.entries["documento"].get(),
            'nfe': self.entries["nfe"].get(),
            'chave_nfe': self.entries["chave_nfe"].get(),
            'valor': 0.0,
            'data_lancamento': "",
            'vencimento': "",
            'observacao': self.entries["observacao"].get(),
            'tipo': self.entries["tipo"].get(),
        }

        # Validação e conversão para o formato internacional para salvar no DB
        try:
            valor_br = self.entries["valor"].get().replace(',', '.')
            data_lancamento_br = self.entries["data_lancamento"].get()
            vencimento_br = self.entries["vencimento"].get()

            data_to_save['valor'] = float(valor_br)
            data_to_save['data_lancamento'] = datetime.strptime(data_lancamento_br, '%d/%m/%Y').strftime('%Y-%m-%d')
            if vencimento_br:
                data_to_save['vencimento'] = datetime.strptime(vencimento_br, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Erro de Formato", "Valor inválido ou formato de data incorreto. Use DD/MM/AAAA.")
            return

        try:
            self.controller.db_manager.insert_lancamento(data_to_save)
            messagebox.showinfo("Sucesso", "Lançamento salvo com sucesso!")
            self._clear_entries()
        except RuntimeError as e:
            messagebox.showerror("Erro de Banco de Dados", str(e))
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")

    def _clear_entries(self) -> None:
        """Limpa os campos do formulário."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
            if isinstance(entry, ttk.Combobox):
                entry.set("")


class RelatorioScreen(BaseScreen):
    """Tela para geração de relatórios de notas fiscais."""

    def __init__(self, parent: ttk.Frame, controller: "MainApplication", **kwargs: Any) -> None:
        super().__init__(parent, controller, **kwargs)
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Cria e organiza os widgets da tela de relatório."""
        self._create_label(self, "Relatório de Notas Fiscais", font_size=24, bold=True).pack(pady=(20, 10))

        filter_frame = ttk.Frame(self)
        filter_frame.pack(pady=10, padx=20)
        
        self._create_label(filter_frame, "Data Início (DD/MM/AAAA):").grid(row=0, column=0, padx=5, pady=5)
        self.start_date_entry = ttk.Entry(filter_frame, width=20)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)
        self.start_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))

        self._create_label(filter_frame, "Data Fim (DD/MM/AAAA):").grid(row=0, column=2, padx=5, pady=5)
        self.end_date_entry = ttk.Entry(filter_frame, width=20)
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=5)
        self.end_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        self._create_label(filter_frame, "Fornecedor:").grid(row=1, column=0, padx=5, pady=5)
        self.fornecedor_combo = ttk.Combobox(filter_frame, state="readonly", width=40)
        self.fornecedor_combo.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self.load_data()

        search_button = ttk.Button(filter_frame, text="Buscar", command=self.carregar)
        search_button.grid(row=1, column=3, padx=5, pady=5, sticky="e")

        cols = [
            "ID", "Loja", "CNPJ Loja", "Fornecedor", "CNPJ Forn.", "Documento",
            "NFE", "Chave NFE", "Valor", "Data", "Vencimento", "Observação", "Tipo"
        ]
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col.replace("_", " ").title())
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.tree.bind("<Double-1>", self._on_double_click)

    def carregar(self) -> None:
        """Carrega e exibe os lançamentos com base nos filtros."""
        start_date_br = self.start_date_entry.get()
        end_date_br = self.end_date_entry.get()
        fornecedor = self.fornecedor_combo.get()

        try:
            start_date_iso = datetime.strptime(start_date_br, '%d/%m/%Y').strftime('%Y-%m-%d')
            end_date_iso = datetime.strptime(end_date_br, '%d/%m/%Y').strftime('%Y-%m-%d')
            
            data = self.controller.db_manager.get_lancamentos(
                start_date=start_date_iso, end_date=end_date_iso, fornecedor=fornecedor
            )
            self._update_treeview(data)
        except ValueError:
            messagebox.showerror("Erro de Formato", "Formato de data inválido. Use DD/MM/AAAA.")
        except RuntimeError as e:
            messagebox.showerror("Erro de Banco de Dados", str(e))
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Erro ao carregar relatório: {e}")

    def load_data(self) -> None:
        """Carrega a lista de fornecedores."""
        try:
            fornecedores = self.controller.db_manager.get_entities("fornecedores")
            self.fornecedor_combo["values"] = [f[0] for f in fornecedores]
        except RuntimeError as e:
            messagebox.showerror("Erro de Banco de Dados", str(e))
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Erro ao carregar fornecedores: {e}")

    def _update_treeview(self, data: List[LancamentoData]) -> None:
        """Atualiza o Treeview com os dados fornecidos."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in data:
            row_values = list(row.values())
            row_values[8] = f"R$ {row_values[8]:.2f}".replace('.', ',')
            row_values[9] = datetime.strptime(row_values[9], '%Y-%m-%d').strftime('%d/%m/%Y')
            row_values[10] = datetime.strptime(row_values[10], '%Y-%m-%d').strftime('%d/%m/%Y') if row_values[10] else ''
            
            self.tree.insert("", tk.END, values=row_values, iid=row["id"])

    def _on_double_click(self, event: tk.Event) -> None:
        """Exclui um lançamento ao dar duplo clique."""
        item_id = self.tree.focus()
        if not item_id:
            return

        record_id = int(self.tree.item(item_id, "values")[0])
        if messagebox.askyesno("Confirmação", f"Deseja realmente excluir o lançamento ID {record_id}?"):
            try:
                self.controller.db_manager.delete_lancamento(record_id)
                self.tree.delete(item_id)
                messagebox.showinfo("Sucesso", "Lançamento excluído.")
            except RuntimeError as e:
                messagebox.showerror("Erro de Banco de Dados", str(e))
            except Exception as e:
                messagebox.showerror("Erro Inesperado", f"Erro ao excluir: {e}")