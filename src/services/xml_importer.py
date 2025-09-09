from lxml import etree
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import os
import re

class XMLImporter:
    """
    Serviço responsável por importar e processar arquivos XML de Nota Fiscal.
    """

    def __init__(self):
        # Namespace padrão das notas fiscais eletrônicas (NF-e)
        self.namespace = "{http://www.portalfiscal.inf.br/nfe}"

    def import_xml(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Lê e extrai dados de um arquivo XML de NF-e.
        Retorna um dicionário com os dados extraídos ou None em caso de erro.
        """
        if not Path(file_path).is_file():
            print(f"Erro: Arquivo não encontrado em {file_path}")
            return None

        try:
            tree = etree.parse(file_path)
            root = tree.getroot()

            # Extração dos dados principais do cabeçalho da NF-e
            ide = root.find(f'.//{self.namespace}ide')
            emit = root.find(f'.//{self.namespace}emit')
            dest = root.find(f'.//{self.namespace}dest')
            v_total = root.find(f'.//{self.namespace}ICMSTot')
            
            if not all([ide, emit, dest, v_total]):
                print("Erro: Estrutura XML incompleta. Elementos essenciais não encontrados.")
                return None
            
            # Formata a data para AAAA-MM-DD
            data_emissao_str = ide.find(f'.//{self.namespace}dhEmi').text
            data_emissao = datetime.fromisoformat(data_emissao_str).strftime('%Y-%m-%d')
            
            # Extrai a chave de acesso do atributo 'Id' do elemento 'infNFe'
            chave_nfe = root.find(f'.//{self.namespace}infNFe').attrib['Id'].replace("NFe", "")

            # Converte o valor para float
            try:
                valor_total = float(v_total.find(f'.//{self.namespace}vNF').text)
            except (ValueError, AttributeError):
                valor_total = 0.0

            # Extração dos dados do fornecedor (emitente)
            fornecedor_nome = emit.find(f'.//{self.namespace}xNome').text
            fornecedor_cnpj = emit.find(f'.//{self.namespace}CNPJ').text

            # Extração dos dados da loja (destinatário)
            loja_nome = dest.find(f'.//{self.namespace}xNome').text
            loja_cnpj = dest.find(f'.//{self.namespace}CNPJ').text
            
            # Documento e NFE são geralmente o mesmo número da nota
            nfe_number = ide.find(f'.//{self.namespace}nNF').text

            # Criação do dicionário de dados
            return {
                "chave_nfe": chave_nfe,
                "nfe": nfe_number,
                "documento": nfe_number,
                "data_lancamento": data_emissao,
                "valor": valor_total,
                "fornecedor": fornecedor_nome,
                "cnpj_forn": fornecedor_cnpj,
                "loja": loja_nome,
                "cnpj_loja": loja_cnpj,
                "tipo": "Entrada",  # Presumimos que NF-e importada é de entrada
            }
        
        except etree.XMLSyntaxError as e:
            print(f"Erro de sintaxe no XML: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado ao processar o XML: {e}")
            return None