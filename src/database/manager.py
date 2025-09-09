import sqlite3
from datetime import datetime
from typing import List, Tuple, Any, Dict, TypedDict, Optional
from pathlib import Path

class LancamentoData(TypedDict):
    """Representa a estrutura de dados de um lançamento."""
    id: int
    loja: str
    cnpj_loja: str
    fornecedor: str
    cnpj_forn: str
    documento: str
    nfe: str
    chave_nfe: str
    valor: float
    data_lancamento: str
    vencimento: str
    observacao: str
    tipo: str

DATABASE_DIR = Path("data")
DATABASE_PATH = DATABASE_DIR / "notas.db"

class DatabaseManager:
    """Gerencia as operações de persistência de dados."""

    def __init__(self) -> None:
        DATABASE_DIR.mkdir(exist_ok=True)
        self.db_path = DATABASE_PATH
        self._create_tables()

    def _execute_query(self, query: str, params: Optional[Tuple[Any, ...]] = None, fetch_all: bool = False, fetch_one: bool = False) -> Any:
        """Método utilitário para executar queries de forma segura."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()
                if fetch_all:
                    return cursor.fetchall()
                if fetch_one:
                    return cursor.fetchone()
                return None
        except sqlite3.Error as e:
            raise RuntimeError(f"Erro no banco de dados: {e}") from e

    def _create_tables(self) -> None:
        """Cria as tabelas do banco de dados, se não existirem."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS lojas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                cnpj TEXT NOT NULL UNIQUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                cnpj TEXT NOT NULL UNIQUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS lancamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loja TEXT, cnpj_loja TEXT, fornecedor TEXT, cnpj_forn TEXT,
                documento TEXT, nfe TEXT, chave_nfe TEXT,
                valor REAL NOT NULL, data_lancamento TEXT, vencimento TEXT,
                observacao TEXT, tipo TEXT NOT NULL
            )
            """
        ]
        for query in queries:
            self._execute_query(query)

    def insert_entity(self, table: str, nome: str, cnpj: str) -> None:
        """Insere uma nova loja ou fornecedor."""
        self._execute_query(f"INSERT INTO {table} (nome, cnpj) VALUES (?, ?)", (nome, cnpj))

    def get_entities(self, table: str) -> List[Tuple[str, str]]:
        """Busca todas as entidades de uma tabela (lojas ou fornecedores)."""
        rows = self._execute_query(f"SELECT nome, cnpj FROM {table} ORDER BY nome", fetch_all=True)
        return [(row['nome'], row['cnpj']) for row in rows]

    def insert_lancamento(self, data: LancamentoData) -> None:
        """Insere um novo lançamento de nota fiscal."""
        query = """
            INSERT INTO lancamentos (
                loja, cnpj_loja, fornecedor, cnpj_forn, documento, nfe, chave_nfe,
                valor, data_lancamento, vencimento, observacao, tipo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data['loja'], data['cnpj_loja'], data['fornecedor'], data['cnpj_forn'],
            data['documento'], data['nfe'], data['chave_nfe'], data['valor'],
            data['data_lancamento'], data['vencimento'], data['observacao'], data['tipo']
        )
        self._execute_query(query, params)

    def get_lancamentos(self, limit: int = 0, start_date: str = "", end_date: str = "", fornecedor: str = "") -> List[LancamentoData]:
        """Busca lançamentos com base em filtros e limite."""
        query = "SELECT * FROM lancamentos WHERE 1=1"
        params: List[Any] = []

        if start_date and end_date:
            query += " AND data_lancamento BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        
        if fornecedor:
            query += " AND fornecedor = ?"
            params.append(fornecedor)
            
        if limit:
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
        else:
            query += " ORDER BY id DESC"

        rows = self._execute_query(query, tuple(params), fetch_all=True)
        return [dict(row) for row in rows]

    def delete_lancamento(self, record_id: int) -> None:
        """Exclui um lançamento pelo ID."""
        self._execute_query("DELETE FROM lancamentos WHERE id = ?", (record_id,))

    def corrigir_datas(self) -> None:
        """Converte datas do formato 'DD-MM-YYYY' para 'YYYY-MM-DD'."""
        rows = self._execute_query("SELECT id, data_lancamento FROM lancamentos WHERE data_lancamento LIKE '%-%-%'", fetch_all=True)
        
        updates = []
        for row in rows:
            lanc_id, data_str = row['id'], row['data_lancamento']
            try:
                if len(data_str) == 10 and data_str[4] != '-' and data_str[7] != '-':
                    data_formatada = datetime.strptime(data_str, "%d-%m-%Y").strftime("%Y-%m-%d")
                    updates.append((data_formatada, lanc_id))
            except (ValueError, IndexError):
                continue
        
        if updates:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany("UPDATE lancamentos SET data_lancamento = ? WHERE id = ?", updates)
                conn.commit()