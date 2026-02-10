import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from database.conexao import garantir_banco  # ajuste se seu projeto usar outro padrão



class ProducaoDAO:
    def __init__(self):
        self.conn = garantir_banco()
    
    def _get_connection(self):
        return self.conn
    
    
    # ==================== VALOR DO SACO ====================
    
    def get_valor_saco_atual(self) -> float:
        """Retorna o valor atual do saco"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT valor FROM valor_saco WHERE ativo = 1 ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else 0.0
    
    def atualizar_valor_saco(self, novo_valor: float) -> bool:
        """Atualiza o valor do saco"""
        try:
            cursor = self.conn.cursor()
            # Desativa todos os valores anteriores
            cursor.execute("UPDATE valor_saco SET ativo = 0")
            # Insere novo valor
            cursor.execute(
                "INSERT INTO valor_saco (valor, ativo) VALUES (?, 1)",
                (novo_valor,)
            )
            self.conn.commit()
           
            return True
        except Exception as e:
            print(f"Erro ao atualizar valor do saco: {e}")
            return False
    
    # ==================== PRODUÇÕES ====================
    
    def criar_producao(self, nome: str, data_inicio: str, observacoes: str = "") -> Optional[int]:
        """Cria uma nova produção"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO producoes (nome, data_inicio, status, observacoes)
                   VALUES (?, ?, 'aberta', ?)""",
                (nome, data_inicio, observacoes)
            )
            producao_id = cursor.lastrowid
            self.conn.commit()
    
            return producao_id
        except Exception as e:
            print(f"Erro ao criar produção: {e}")
            return None
    
    def listar_producoes(self, apenas_abertas: bool = False) -> List[Dict]:
        """Lista todas as produções"""
        
        cursor = self.conn.cursor()
        
        query = """
            SELECT id, nome, data_inicio, data_fim, status, 
                   total_sacos, valor_total, observacoes, created_at
            FROM producoes
        """
        if apenas_abertas:
            query += " WHERE status = 'aberta'"
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query)
        colunas = [desc[0] for desc in cursor.description]
        producoes = [dict(zip(colunas, row)) for row in cursor.fetchall()]
        return producoes
    
    def get_producao(self, producao_id: int) -> Optional[Dict]:
        """Retorna detalhes de uma produção"""
        
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, nome, data_inicio, data_fim, status, 
                      total_sacos, valor_total, observacoes, created_at
               FROM producoes WHERE id = ?""",
            (producao_id,)
        )
        colunas = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        return dict(zip(colunas, row)) if row else None
    
    def excluir_producao(self, producao_id: int) -> bool:
        """Exclui uma produção e todos os seus dados relacionados"""
        try:
            cursor = self.conn.cursor()
            
            # Ativa foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Busca todos os dias da produção
            cursor.execute("SELECT id FROM producao_dias WHERE producao_id = ?", (producao_id,))
            dias = cursor.fetchall()
            
            # Para cada dia, busca e deleta as divisões e participantes
            for dia_row in dias:
                dia_id = dia_row[0]
                
                # Busca divisões do dia
                cursor.execute("SELECT id FROM producao_divisoes WHERE producao_dia_id = ?", (dia_id,))
                divisoes = cursor.fetchall()
                
                # Deleta participantes de cada divisão
                for divisao_row in divisoes:
                    divisao_id = divisao_row[0]
                    cursor.execute("DELETE FROM producao_participantes WHERE producao_divisao_id = ?", (divisao_id,))
                
                # Deleta as divisões
                cursor.execute("DELETE FROM producao_divisoes WHERE producao_dia_id = ?", (dia_id,))
            
            # Deleta os dias
            cursor.execute("DELETE FROM producao_dias WHERE producao_id = ?", (producao_id,))
            
            # Deleta os totais dos diaristas
            cursor.execute("DELETE FROM producao_totais_diarista WHERE producao_id = ?", (producao_id,))
            
            # Por fim, deleta a produção
            cursor.execute("DELETE FROM producoes WHERE id = ?", (producao_id,))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao excluir produção: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def fechar_producao(self, producao_id: int, data_fim: str) -> bool:
        """Fecha uma produção e calcula totais"""
        try:
            cursor = self.conn.cursor()
            
            # Calcula totais
            cursor.execute(
                """SELECT SUM(pd.total_sacos_dia), SUM(pd.total_sacos_dia * pd.valor_saco)
                   FROM producao_dias pd
                   WHERE pd.producao_id = ?""",
                (producao_id,)
            )
            total_sacos, valor_total = cursor.fetchone()
            total_sacos = total_sacos or 0
            valor_total = valor_total or 0.0
            
            # Atualiza produção
            cursor.execute(
                """UPDATE producoes 
                   SET status = 'fechada', data_fim = ?, 
                       total_sacos = ?, valor_total = ?
                   WHERE id = ?""",
                (data_fim, total_sacos, valor_total, producao_id)
            )
            
            self.conn.commit()
        
            return True
        except Exception as e:
            print(f"Erro ao fechar produção: {e}")
            return False
    
    # ==================== DIAS DE PRODUÇÃO ====================
    
    def adicionar_dia_producao(self, producao_id: int, data_producao: str, 
                               total_sacos: int, divisoes: List[Dict]) -> bool:
        """
        Adiciona um dia de produção com suas divisões
        divisoes = [
            {
                'quantidade_sacos': 100,
                'descricao': 'Turno manhã',
                'participantes': [
                    {'diarista_id': 1, 'quantidade_sacos': 50},
                    {'diarista_id': 2, 'quantidade_sacos': 50}
                ]
            }
        ]
        """
        try:
            
            cursor = self.conn.cursor()
            
            valor_saco = self.get_valor_saco_atual()
            
            # Cria o dia de produção
            cursor.execute(
                """INSERT INTO producao_dias 
                   (producao_id, data_producao, total_sacos_dia, valor_saco)
                   VALUES (?, ?, ?, ?)""",
                (producao_id, data_producao, total_sacos, valor_saco)
            )
            dia_id = cursor.lastrowid
            
            # Processa cada divisão
            for divisao in divisoes:
                cursor.execute(
                    """INSERT INTO producao_divisoes 
                       (producao_dia_id, quantidade_sacos, descricao)
                       VALUES (?, ?, ?)""",
                    (dia_id, divisao['quantidade_sacos'], divisao.get('descricao', ''))
                )
                divisao_id = cursor.lastrowid
                
                # Calcula valor por participante
                participantes = divisao['participantes']
                qtd_sacos_divisao = divisao['quantidade_sacos']
                
                for participante in participantes:
                    qtd_sacos_participante = participante['quantidade_sacos']
                    valor_receber = qtd_sacos_participante * valor_saco
                    
                    # Insere participante
                    cursor.execute(
                        """INSERT INTO producao_participantes 
                           (producao_divisao_id, diarista_id, quantidade_sacos, valor_receber)
                           VALUES (?, ?, ?, ?)""",
                        (divisao_id, participante['diarista_id'], 
                         qtd_sacos_participante, valor_receber)
                    )
                    
                    # Atualiza totais do diarista na produção
                    cursor.execute(
                        """INSERT INTO producao_totais_diarista 
                           (producao_id, diarista_id, total_sacos, valor_total)
                           VALUES (?, ?, ?, ?)
                           ON CONFLICT(producao_id, diarista_id) 
                           DO UPDATE SET 
                               total_sacos = total_sacos + ?,
                               valor_total = valor_total + ?""",
                        (producao_id, participante['diarista_id'], 
                         qtd_sacos_participante, valor_receber,
                         qtd_sacos_participante, valor_receber)
                    )
            
            self.conn.commit()
        
            return True
        except Exception as e:
            print(f"Erro ao adicionar dia de produção: {e}")
            return False
    
    def listar_dias_producao(self, producao_id: int) -> List[Dict]:
        """Lista todos os dias de uma produção"""
        
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, data_producao, total_sacos_dia, valor_saco, observacoes
               FROM producao_dias
               WHERE producao_id = ?
               ORDER BY data_producao DESC""",
            (producao_id,)
        )
        colunas = [desc[0] for desc in cursor.description]
        dias = [dict(zip(colunas, row)) for row in cursor.fetchall()]
        
        return dias
    
    # ==================== RELATÓRIOS ====================
    
    def get_totais_diaristas(self, producao_id: int) -> List[Dict]:
        """Retorna totais por diarista em uma produção"""
        
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT 
                   d.id as id, 
                   d.nome as nome, 
                   d.cpf as cpf,
                   COALESCE(ptd.total_sacos, 0) as total_sacos, 
                   COALESCE(ptd.valor_total, 0.0) as valor_total
               FROM producao_totais_diarista ptd
               JOIN diaristas d ON d.id = ptd.diarista_id
               WHERE ptd.producao_id = ?
               ORDER BY d.nome""",
            (producao_id,)
        )
        
        # Converte para dicionários
        totais = []
        for row in cursor.fetchall():
            totais.append({
                'id': row[0],
                'nome': row[1],
                'cpf': row[2],
                'total_sacos': row[3],
                'valor_total': row[4]
            })
        
        
        return totais
    
    def get_detalhamento_dia(self, dia_id: int) -> Dict:
        """Retorna detalhamento completo de um dia de produção"""
        
        cursor = self.conn.cursor()
        
        # Busca informações do dia
        cursor.execute(
            """SELECT id, data_producao, total_sacos_dia, valor_saco
               FROM producao_dias WHERE id = ?""",
            (dia_id,)
        )
        dia = cursor.fetchone()
        
        if not dia:
            
            return None
        
        resultado = {
            'id': dia[0],
            'data_producao': dia[1],
            'total_sacos_dia': dia[2],
            'valor_saco': dia[3],
            'divisoes': []
        }
        
        # Busca divisões
        cursor.execute(
            """SELECT id, quantidade_sacos, descricao
               FROM producao_divisoes WHERE producao_dia_id = ?""",
            (dia_id,)
        )
        divisoes = cursor.fetchall()
        
        for divisao in divisoes:
            divisao_dict = {
                'id': divisao[0],
                'quantidade_sacos': divisao[1],
                'descricao': divisao[2],
                'participantes': []
            }
            
            # Busca participantes da divisão
            cursor.execute(
                """SELECT 
                       d.id, d.nome, d.cpf,
                       pp.quantidade_sacos, pp.valor_receber
                   FROM producao_participantes pp
                   JOIN diaristas d ON d.id = pp.diarista_id
                   WHERE pp.producao_divisao_id = ?""",
                (divisao[0],)
            )
            participantes = cursor.fetchall()
            
            for p in participantes:
                divisao_dict['participantes'].append({
                    'diarista_id': p[0],
                    'nome': p[1],
                    'cpf': p[2],
                    'quantidade_sacos': p[3],
                    'valor_receber': p[4]
                })
            
            resultado['divisoes'].append(divisao_dict)
        
        
        return resultado
    
    def deletar_dia_producao(self, dia_id: int) -> bool:
        """Remove um dia de produção e recalcula totais"""
        try:
            
            cursor = self.conn.cursor()
            
            # Busca producao_id antes de deletar
            cursor.execute("SELECT producao_id FROM producao_dias WHERE id = ?", (dia_id,))
            result = cursor.fetchone()
            if not result:
                
                return False
            
            producao_id = result[0]
            
            # Deleta o dia (cascade vai deletar divisões e participantes)
            cursor.execute("DELETE FROM producao_dias WHERE id = ?", (dia_id,))
            
            # Recalcula totais dos diaristas
            cursor.execute("DELETE FROM producao_totais_diarista WHERE producao_id = ?", (producao_id,))
            
            cursor.execute(
                """INSERT INTO producao_totais_diarista (producao_id, diarista_id, total_sacos, valor_total)
                   SELECT ?, pp.diarista_id, SUM(pp.quantidade_sacos), SUM(pp.valor_receber)
                   FROM producao_participantes pp
                   JOIN producao_divisoes pd ON pd.id = pp.producao_divisao_id
                   JOIN producao_dias pdia ON pdia.id = pd.producao_dia_id
                   WHERE pdia.producao_id = ?
                   GROUP BY pp.diarista_id""",
                (producao_id, producao_id)
            )
            
            self.conn.commit()
            
            return True
        except Exception as e:
            print(f"Erro ao deletar dia de produção: {e}")
            return False    
    