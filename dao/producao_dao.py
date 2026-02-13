import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from database.conexao import garantir_banco


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
            cursor.execute("UPDATE valor_saco SET ativo = 0")
            cursor.execute(
                "INSERT INTO valor_saco (valor, ativo) VALUES (?, 1)",
                (novo_valor,)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar valor do saco: {e}")
            return False


    # ==================== CENTRO DE CUSTO ====================

    def listar_centros_custo(self) -> List[Dict]:
        """Retorna todos os centros de custo disponíveis"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, centro FROM centros_custo ORDER BY centro")
        return [{"id": row[0], "centro": row[1]} for row in cursor.fetchall()]


    # ==================== PRODUÇÕES ====================

    def criar_producao(self, centro_custo_id: int, data_inicio: str,
                       observacoes: str = "") -> Optional[int]:
        """Cria uma nova produção vinculada a um centro de custo"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO producoes (centro_custo_id, data_inicio, status, observacoes)
                   VALUES (?, ?, 'aberta', ?)""",
                (centro_custo_id, data_inicio, observacoes)
            )
            producao_id = cursor.lastrowid
            self.conn.commit()
            return producao_id
        except Exception as e:
            print(f"Erro ao criar produção: {e}")
            return None

    def listar_producoes(self, apenas_abertas: bool = False) -> List[Dict]:
        """Lista todas as produções com o nome do centro de custo"""
        cursor = self.conn.cursor()

        query = """
            SELECT
                p.id,
                cc.centro        AS nome,
                cc.id            AS centro_custo_id,
                p.data_inicio,
                p.data_fim,
                p.status,
                p.total_sacos,
                p.valor_total,
                p.observacoes,
                p.created_at
            FROM producoes p
            JOIN centros_custo cc ON cc.id = p.centro_custo_id
        """
        if apenas_abertas:
            query += " WHERE p.status = 'aberta'"
        query += " ORDER BY p.created_at DESC"

        cursor.execute(query)
        colunas = [desc[0] for desc in cursor.description]
        return [dict(zip(colunas, row)) for row in cursor.fetchall()]

    def get_producao(self, producao_id: int) -> Optional[Dict]:
        """Retorna detalhes de uma produção com o nome do centro de custo"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT
                   p.id,
                   cc.centro        AS nome,
                   cc.id            AS centro_custo_id,
                   p.data_inicio,
                   p.data_fim,
                   p.status,
                   p.total_sacos,
                   p.valor_total,
                   p.observacoes,
                   p.created_at
               FROM producoes p
               JOIN centros_custo cc ON cc.id = p.centro_custo_id
               WHERE p.id = ?""",
            (producao_id,)
        )
        colunas = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        return dict(zip(colunas, row)) if row else None

    def excluir_producao(self, producao_id: int) -> bool:
        """Exclui uma produção e todos os seus dados relacionados"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")

            cursor.execute("SELECT id FROM producao_dias WHERE producao_id = ?", (producao_id,))
            dias = cursor.fetchall()

            for dia_row in dias:
                dia_id = dia_row[0]
                cursor.execute(
                    "SELECT id FROM producao_divisoes WHERE producao_dia_id = ?", (dia_id,))
                divisoes = cursor.fetchall()

                for divisao_row in divisoes:
                    divisao_id = divisao_row[0]
                    cursor.execute(
                        "DELETE FROM producao_participantes WHERE producao_divisao_id = ?",
                        (divisao_id,))

                cursor.execute(
                    "DELETE FROM producao_divisoes WHERE producao_dia_id = ?", (dia_id,))

            cursor.execute("DELETE FROM producao_dias WHERE producao_id = ?", (producao_id,))
            cursor.execute(
                "DELETE FROM producao_totais_diarista WHERE producao_id = ?", (producao_id,))
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

            cursor.execute(
                """SELECT SUM(pd.total_sacos_dia), SUM(pd.total_sacos_dia * pd.valor_saco)
                   FROM producao_dias pd
                   WHERE pd.producao_id = ?""",
                (producao_id,)
            )
            total_sacos, valor_total = cursor.fetchone()
            total_sacos = total_sacos or 0
            valor_total = valor_total or 0.0

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
        Adiciona um dia de produção com suas divisões.
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

            cursor.execute(
                """INSERT INTO producao_dias
                   (producao_id, data_producao, total_sacos_dia, valor_saco)
                   VALUES (?, ?, ?, ?)""",
                (producao_id, data_producao, total_sacos, valor_saco)
            )
            dia_id = cursor.lastrowid

            for divisao in divisoes:
                cursor.execute(
                    """INSERT INTO producao_divisoes
                       (producao_dia_id, quantidade_sacos, descricao)
                       VALUES (?, ?, ?)""",
                    (dia_id, divisao['quantidade_sacos'], divisao.get('descricao', ''))
                )
                divisao_id = cursor.lastrowid

                for participante in divisao['participantes']:
                    qtd_sacos_participante = participante['quantidade_sacos']
                    valor_receber = qtd_sacos_participante * valor_saco

                    cursor.execute(
                        """INSERT INTO producao_participantes
                           (producao_divisao_id, diarista_id, quantidade_sacos, valor_receber)
                           VALUES (?, ?, ?, ?)""",
                        (divisao_id, participante['diarista_id'],
                         qtd_sacos_participante, valor_receber)
                    )

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
        return [dict(zip(colunas, row)) for row in cursor.fetchall()]


    # ==================== RELATÓRIOS ====================

    def get_totais_diaristas(self, producao_id: int) -> List[Dict]:
        """Retorna totais por diarista em uma produção"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT
                   d.id        AS id,
                   d.nome      AS nome,
                   d.cpf       AS cpf,
                   COALESCE(ptd.total_sacos, 0)   AS total_sacos,
                   COALESCE(ptd.valor_total, 0.0)  AS valor_total
               FROM producao_totais_diarista ptd
               JOIN diaristas d ON d.id = ptd.diarista_id
               WHERE ptd.producao_id = ?
               ORDER BY d.nome""",
            (producao_id,)
        )
        return [
            {
                'id': row[0], 'nome': row[1], 'cpf': row[2],
                'total_sacos': row[3], 'valor_total': row[4]
            }
            for row in cursor.fetchall()
        ]

    def get_detalhamento_dia(self, dia_id: int) -> Optional[Dict]:
        """Retorna detalhamento completo de um dia de produção"""
        cursor = self.conn.cursor()

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

        cursor.execute(
            """SELECT id, quantidade_sacos, descricao
               FROM producao_divisoes WHERE producao_dia_id = ?""",
            (dia_id,)
        )
        for divisao in cursor.fetchall():
            divisao_dict = {
                'id': divisao[0],
                'quantidade_sacos': divisao[1],
                'descricao': divisao[2],
                'participantes': []
            }

            cursor.execute(
                """SELECT d.id, d.nome, d.cpf, pp.quantidade_sacos, pp.valor_receber
                   FROM producao_participantes pp
                   JOIN diaristas d ON d.id = pp.diarista_id
                   WHERE pp.producao_divisao_id = ?""",
                (divisao[0],)
            )
            for p in cursor.fetchall():
                divisao_dict['participantes'].append({
                    'diarista_id': p[0], 'nome': p[1], 'cpf': p[2],
                    'quantidade_sacos': p[3], 'valor_receber': p[4]
                })

            resultado['divisoes'].append(divisao_dict)

        return resultado

    def deletar_dia_producao(self, dia_id: int) -> bool:
        """Remove um dia de produção e recalcula totais"""
        try:
            cursor = self.conn.cursor()

            cursor.execute("SELECT producao_id FROM producao_dias WHERE id = ?", (dia_id,))
            result = cursor.fetchone()
            if not result:
                return False
            producao_id = result[0]

            cursor.execute("DELETE FROM producao_dias WHERE id = ?", (dia_id,))

            cursor.execute(
                "DELETE FROM producao_totais_diarista WHERE producao_id = ?", (producao_id,))

            cursor.execute(
                """INSERT INTO producao_totais_diarista
                       (producao_id, diarista_id, total_sacos, valor_total)
                   SELECT ?, pp.diarista_id,
                          SUM(pp.quantidade_sacos), SUM(pp.valor_receber)
                   FROM producao_participantes pp
                   JOIN producao_divisoes pd   ON pd.id   = pp.producao_divisao_id
                   JOIN producao_dias pdia     ON pdia.id = pd.producao_dia_id
                   WHERE pdia.producao_id = ?
                   GROUP BY pp.diarista_id""",
                (producao_id, producao_id)
            )

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao deletar dia de produção: {e}")
            return False

    # ─── Relatórios ───────────────────────────────────────────────────────────

    def relatorio_por_centro_custo(self,
                                   data_inicio: str,
                                   data_fim: str,
                                   apenas_fechadas: bool = False) -> List[Dict]:
        """
        Totais agrupados por centro de custo no período.
        Filtra por data_inicio/data_fim da produção.
        Retorna: [{'centro', 'qtd_producoes', 'total_sacos', 'valor_total'}, ...]
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                cc.centro,
                COUNT(p.id)          AS qtd_producoes,
                SUM(p.total_sacos)   AS total_sacos,
                SUM(p.valor_total)   AS valor_total
            FROM producoes p
            JOIN centros_custo cc ON cc.id = p.centro_custo_id
            WHERE p.data_inicio >= ?
              AND p.data_inicio <= ?
        """
        params = [data_inicio, data_fim]

        if apenas_fechadas:
            query += " AND p.status = 'fechada'"

        query += " GROUP BY cc.id, cc.centro ORDER BY valor_total DESC"

        cursor.execute(query, params)
        return [
            {
                'centro':        row[0],
                'qtd_producoes': row[1],
                'total_sacos':   row[2] or 0,
                'valor_total':   row[3] or 0.0
            }
            for row in cursor.fetchall()
        ]

    def relatorio_por_diarista(self,
                               data_inicio: str,
                               data_fim: str,
                               centro_custo_id: int = None) -> List[Dict]:
        """
        Totais agrupados por diarista no período, com filtro opcional de centro de custo.
        Retorna: [{'nome', 'cpf', 'total_sacos', 'valor_total'}, ...]
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                d.nome,
                d.cpf,
                SUM(ptd.total_sacos)  AS total_sacos,
                SUM(ptd.valor_total)  AS valor_total
            FROM producao_totais_diarista ptd
            JOIN diaristas d   ON d.id  = ptd.diarista_id
            JOIN producoes p   ON p.id  = ptd.producao_id
            WHERE p.data_inicio >= ?
              AND p.data_inicio <= ?
        """
        params = [data_inicio, data_fim]

        if centro_custo_id:
            query += " AND p.centro_custo_id = ?"
            params.append(centro_custo_id)

        query += " GROUP BY d.id, d.nome, d.cpf ORDER BY valor_total DESC"

        cursor.execute(query, params)
        return [
            {
                'nome':        row[0],
                'cpf':         row[1],
                'total_sacos': row[2] or 0,
                'valor_total': row[3] or 0.0
            }
            for row in cursor.fetchall()
        ]

    def relatorio_geral(self,
                        data_inicio: str,
                        data_fim: str,
                        centro_custo_id: int = None,
                        apenas_fechadas: bool = False) -> List[Dict]:
        """
        Listagem detalhada de todas as produções no período.
        Filtros opcionais: centro de custo e status.
        Retorna: [{'centro', 'status', 'data_inicio', 'data_fim',
                   'total_sacos', 'valor_total'}, ...]
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                cc.centro,
                p.status,
                p.data_inicio,
                p.data_fim,
                p.total_sacos,
                p.valor_total
            FROM producoes p
            JOIN centros_custo cc ON cc.id = p.centro_custo_id
            WHERE p.data_inicio >= ?
              AND p.data_inicio <= ?
        """
        params = [data_inicio, data_fim]

        if centro_custo_id:
            query += " AND p.centro_custo_id = ?"
            params.append(centro_custo_id)

        if apenas_fechadas:
            query += " AND p.status = 'fechada'"

        query += " ORDER BY p.data_inicio DESC"

        cursor.execute(query, params)
        return [
            {
                'centro':      row[0],
                'status':      row[1],
                'data_inicio': row[2],
                'data_fim':    row[3],
                'total_sacos': row[4] or 0,
                'valor_total': row[5] or 0.0
            }
            for row in cursor.fetchall()
        ]