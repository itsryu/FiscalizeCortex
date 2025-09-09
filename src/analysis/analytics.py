from src.database.manager import DatabaseManager, LancamentoData
from typing import Dict, Any, List, Optional, Protocol, TypeAlias
from datetime import datetime
import collections
from itertools import groupby

LancamentoList: TypeAlias = List[LancamentoData]

class FinancialAnalyticsProtocol(Protocol):
    """
    Protocolo que define a interface pública do serviço de análise financeira.
    Garante que qualquer implementação siga este contrato.
    """
    def get_financial_summary(self, lancamentos: LancamentoList) -> Dict[str, Any]:
        ...

    def get_monthly_totals(self, lancamentos: LancamentoList) -> Dict[str, Dict[str, float]]:
        ...

    def get_supplier_analysis(self, lancamentos: LancamentoList) -> Dict[str, float]:
        ...

class FinancialAnalytics(FinancialAnalyticsProtocol):
    """
    Serviço de análise de dados financeiros.
    Sua única responsabilidade é processar dados brutos e gerar relatórios analíticos.
    """
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def get_financial_summary(self, lancamentos: Optional[LancamentoList] = None) -> Dict[str, Any]:
        """
        Gera um resumo financeiro com totais por tipo e valor.
        """
        if lancamentos is None:
            lancamentos = self.db_manager.get_lancamentos()

        # Otimização: usa um único loop para calcular todos os totais.
        totals: collections.defaultdict[str, Any] = collections.defaultdict(float)
        counts: collections.defaultdict[str, int] = collections.defaultdict(int)

        for lancamento in lancamentos:
            tipo = lancamento.get('tipo', 'Outro')
            valor = lancamento.get('valor', 0.0)
            
            totals[tipo] += valor
            counts[tipo] += 1
        
        return {
            "total_entradas": totals['Entrada'],
            "total_saidas": totals['Saída'],
            "saldo_liquido": totals['Entrada'] - totals['Saída'],
            "count_entradas": counts['Entrada'],
            "count_saidas": counts['Saída']
        }

    def get_monthly_totals(self, lancamentos: Optional[LancamentoList] = None) -> Dict[str, Dict[str, float]]:
        """
        Calcula os totais de entrada e saída por mês.
        Retorna um dicionário no formato: {"YYYY-MM": {"Entrada": total, "Saída": total}}.
        """
        if lancamentos is None:
            lancamentos = self.db_manager.get_lancamentos()
        
        # Otimização: ordena a lista para usar groupby.
        # A ordenação é um pré-requisito para o groupby.
        sorted_lancamentos = sorted(lancamentos, key=lambda l: l['data_lancamento'])
        
        monthly_data: Dict[str, Dict[str, float]] = collections.defaultdict(lambda: collections.defaultdict(float))

        # Agrupa os lançamentos por mês e ano
        for mes_ano, group in groupby(sorted_lancamentos, key=lambda l: l['data_lancamento'][:7]):
            for lancamento in group:
                if (tipo := lancamento.get('tipo')) and (valor := lancamento.get('valor')) is not None:
                    monthly_data[mes_ano][tipo] += valor
        
        return {mes: dict(valores) for mes, valores in monthly_data.items()}

    def get_supplier_analysis(self, lancamentos: Optional[LancamentoList] = None) -> Dict[str, float]:
        """
        Calcula o total de valor por fornecedor.
        Retorna um dicionário no formato: {"Fornecedor": total_valor}.
        """
        if lancamentos is None:
            lancamentos = self.db_manager.get_lancamentos()

        supplier_totals: collections.defaultdict[str, float] = collections.defaultdict(float)
        
        for lancamento in lancamentos:
            if (fornecedor := lancamento.get('fornecedor')) and (valor := lancamento.get('valor')) is not None:
                supplier_totals[fornecedor] += valor

        return dict(supplier_totals)