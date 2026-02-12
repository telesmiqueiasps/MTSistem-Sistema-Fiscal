from database.conexao import garantir_banco
from typing import List, Dict, Optional

class ServicoDAO:
    def __init__(self):
        self.conn = garantir_banco()
    
    def salvar(self, diarista_id: int, centro_custo_id: int, data_servico: str,
               valor: float, descricao: str, observacoes: str = "") -> Optional[int]:
        """Salva um novo serviço"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO servicos 
                   (diarista_id, centro_custo_id, data_servico, valor, descricao, observacoes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (diarista_id, centro_custo_id, data_servico, valor, descricao, observacoes)
            )
            servico_id = cursor.lastrowid
            self.conn.commit()
            return servico_id
        except Exception as e:
            print(f"Erro ao salvar serviço: {e}")
            return None
    
    def atualizar(self, servico_id: int, diarista_id: int, centro_custo_id: int,
                  data_servico: str, valor: float, descricao: str, observacoes: str = "") -> bool:
        """Atualiza um serviço existente"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """UPDATE servicos 
                   SET diarista_id = ?, centro_custo_id = ?, data_servico = ?,
                       valor = ?, descricao = ?, observacoes = ?
                   WHERE id = ?""",
                (diarista_id, centro_custo_id, data_servico, valor, descricao, observacoes, servico_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar serviço: {e}")
            return False
    
    def excluir(self, servico_id: int) -> bool:
        """Exclui um serviço"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM servicos WHERE id = ?", (servico_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao excluir serviço: {e}")
            return False
    
    def listar(self, filtro_data_inicio: str = None, filtro_data_fim: str = None,
               filtro_diarista_id: int = None, filtro_centro_custo_id: int = None) -> List[tuple]:
        """Lista serviços com filtros opcionais"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                s.id,
                s.data_servico,
                d.nome as diarista_nome,
                d.cpf as diarista_cpf,
                cc.centro as centro_custo,
                s.valor,
                s.descricao,
                s.observacoes,
                s.diarista_id,
                s.centro_custo_id
            FROM servicos s
            JOIN diaristas d ON d.id = s.diarista_id
            JOIN centros_custo cc ON cc.id = s.centro_custo_id
            WHERE 1=1
        """
        params = []
        
        if filtro_data_inicio:
            query += " AND s.data_servico >= ?"
            params.append(filtro_data_inicio)
        
        if filtro_data_fim:
            query += " AND s.data_servico <= ?"
            params.append(filtro_data_fim)
        
        if filtro_diarista_id:
            query += " AND s.diarista_id = ?"
            params.append(filtro_diarista_id)
        
        if filtro_centro_custo_id:
            query += " AND s.centro_custo_id = ?"
            params.append(filtro_centro_custo_id)
        
        query += " ORDER BY s.data_servico DESC, s.id DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def buscar(self, servico_id: int) -> Optional[tuple]:
        """Busca um serviço específico"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT 
                   s.id,
                   s.data_servico,
                   d.nome as diarista_nome,
                   d.cpf as diarista_cpf,
                   cc.centro as centro_custo,
                   s.valor,
                   s.descricao,
                   s.observacoes,
                   s.diarista_id,
                   s.centro_custo_id
               FROM servicos s
               JOIN diaristas d ON d.id = s.diarista_id
               JOIN centros_custo cc ON cc.id = s.centro_custo_id
               WHERE s.id = ?""",
            (servico_id,)
        )
        return cursor.fetchone()
    
    def total_por_periodo(self, data_inicio: str, data_fim: str) -> float:
        """Retorna o total de serviços em um período"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT COALESCE(SUM(valor), 0) 
               FROM servicos 
               WHERE data_servico BETWEEN ? AND ?""",
            (data_inicio, data_fim)
        )
        result = cursor.fetchone()
        return result[0] if result else 0.0
    
    def total_por_diarista(self, diarista_id: int, data_inicio: str = None, data_fim: str = None) -> float:
        """Retorna o total de serviços de um diarista"""
        cursor = self.conn.cursor()
        
        query = "SELECT COALESCE(SUM(valor), 0) FROM servicos WHERE diarista_id = ?"
        params = [diarista_id]
        
        if data_inicio and data_fim:
            query += " AND data_servico BETWEEN ? AND ?"
            params.extend([data_inicio, data_fim])
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else 0.0
    

    # ==================== RELATÓRIOS ====================
    # Adicione esses métodos dentro da classe ServicoDAO

    def relatorio_por_centro_custo(self, data_inicio: str, data_fim: str) -> list:
        """
        Retorna total pago agrupado por centro de custo no período
        Retorna: [(centro, qtd_servicos, total_valor), ...]
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                cc.centro,
                COUNT(s.id)       AS qtd_servicos,
                SUM(s.valor)      AS total_valor
            FROM servicos s
            JOIN centros_custo cc ON cc.id = s.centro_custo_id
            WHERE s.data_servico BETWEEN ? AND ?
            GROUP BY cc.id, cc.centro
            ORDER BY total_valor DESC
            """,
            (data_inicio, data_fim)
        )
        return cursor.fetchall()

    def relatorio_por_diarista(self, data_inicio: str, data_fim: str) -> list:
        """
        Retorna total pago agrupado por diarista no período
        Retorna: [(nome, cpf, qtd_servicos, total_valor), ...]
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                d.nome,
                d.cpf,
                COUNT(s.id)       AS qtd_servicos,
                SUM(s.valor)      AS total_valor
            FROM servicos s
            JOIN diaristas d ON d.id = s.diarista_id
            WHERE s.data_servico BETWEEN ? AND ?
            GROUP BY d.id, d.nome, d.cpf
            ORDER BY total_valor DESC
            """,
            (data_inicio, data_fim)
        )
        return cursor.fetchall()

    def relatorio_geral(self, data_inicio: str, data_fim: str) -> list:
        """
        Retorna todos os serviços detalhados no período para exportação
        Retorna: [(data, diarista, cpf, centro, descricao, valor), ...]
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                s.data_servico,
                d.nome,
                d.cpf,
                cc.centro,
                s.descricao,
                s.valor
            FROM servicos s
            JOIN diaristas d    ON d.id  = s.diarista_id
            JOIN centros_custo cc ON cc.id = s.centro_custo_id
            WHERE s.data_servico BETWEEN ? AND ?
            ORDER BY s.data_servico DESC
            """,
            (data_inicio, data_fim)
        )
        return cursor.fetchall()