from database.conexao import garantir_banco
from typing import List, Dict, Optional


class ServicoDAO:
    def __init__(self):
        self.conn = garantir_banco()

    # ─────────────────────────────────────────────────────────────────────────
    # ESCRITA
    # ─────────────────────────────────────────────────────────────────────────

    def salvar(self, centro_custo_id: int, data_servico: str, valor: float,
               descricao: str, diarista_ids: List[int],
               observacoes: str = "") -> Optional[int]:
        """Salva um novo serviço e distribui o valor igualmente entre os diaristas."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO servicos
                       (centro_custo_id, data_servico, valor, descricao, observacoes)
                   VALUES (?, ?, ?, ?, ?)""",
                (centro_custo_id, data_servico, valor, descricao, observacoes)
            )
            servico_id = cursor.lastrowid

            valor_rateio = round(valor / len(diarista_ids), 2)
            for diarista_id in diarista_ids:
                cursor.execute(
                    """INSERT INTO servico_diaristas (servico_id, diarista_id, valor_rateio)
                       VALUES (?, ?, ?)""",
                    (servico_id, diarista_id, valor_rateio)
                )

            self.conn.commit()
            return servico_id
        except Exception as e:
            print(f"Erro ao salvar serviço: {e}")
            return None

    def atualizar(self, servico_id: int, centro_custo_id: int, data_servico: str,
                  valor: float, descricao: str, diarista_ids: List[int],
                  observacoes: str = "") -> bool:
        """Atualiza o serviço e recalcula os rateios."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """UPDATE servicos
                   SET centro_custo_id = ?, data_servico = ?,
                       valor = ?, descricao = ?, observacoes = ?
                   WHERE id = ?""",
                (centro_custo_id, data_servico, valor, descricao, observacoes, servico_id)
            )

            # Recria participantes
            cursor.execute(
                "DELETE FROM servico_diaristas WHERE servico_id = ?", (servico_id,))

            valor_rateio = round(valor / len(diarista_ids), 2)
            for diarista_id in diarista_ids:
                cursor.execute(
                    """INSERT INTO servico_diaristas (servico_id, diarista_id, valor_rateio)
                       VALUES (?, ?, ?)""",
                    (servico_id, diarista_id, valor_rateio)
                )

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar serviço: {e}")
            return False

    def excluir(self, servico_id: int) -> bool:
        """Exclui serviço (CASCADE remove os rateios automaticamente)."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("DELETE FROM servicos WHERE id = ?", (servico_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao excluir serviço: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # LEITURA
    # ─────────────────────────────────────────────────────────────────────────

    def listar(self, filtro_data_inicio: str = None, filtro_data_fim: str = None,
               filtro_diarista_id: int = None,
               filtro_centro_custo_id: int = None) -> List[Dict]:
        """
        Lista serviços com filtros opcionais.
        Cada item retornado contém os dados do serviço + lista de participantes.
        """
        cursor = self.conn.cursor()

        query = """
            SELECT DISTINCT
                s.id,
                s.data_servico,
                cc.centro      AS centro_custo,
                s.valor,
                s.descricao,
                s.observacoes,
                s.centro_custo_id
            FROM servicos s
            JOIN centros_custo cc      ON cc.id = s.centro_custo_id
            LEFT JOIN servico_diaristas sd ON sd.servico_id = s.id
            LEFT JOIN diaristas d       ON d.id  = sd.diarista_id
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
            query += " AND sd.diarista_id = ?"
            params.append(filtro_diarista_id)

        if filtro_centro_custo_id:
            query += " AND s.centro_custo_id = ?"
            params.append(filtro_centro_custo_id)

        query += " ORDER BY s.data_servico DESC, s.id DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        servicos = []
        for row in rows:
            servico = {
                'id':             row[0],
                'data_servico':   row[1],
                'centro_custo':   row[2],
                'valor':          row[3],
                'descricao':      row[4],
                'observacoes':    row[5],
                'centro_custo_id':row[6],
                'diaristas':      self._get_participantes(row[0])
            }
            servicos.append(servico)

        return servicos

    def buscar(self, servico_id: int) -> Optional[Dict]:
        """Retorna um serviço completo com seus participantes."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT
                   s.id,
                   s.data_servico,
                   cc.centro AS centro_custo,
                   s.valor,
                   s.descricao,
                   s.observacoes,
                   s.centro_custo_id
               FROM servicos s
               JOIN centros_custo cc ON cc.id = s.centro_custo_id
               WHERE s.id = ?""",
            (servico_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        return {
            'id':             row[0],
            'data_servico':   row[1],
            'centro_custo':   row[2],
            'valor':          row[3],
            'descricao':      row[4],
            'observacoes':    row[5],
            'centro_custo_id':row[6],
            'diaristas':      self._get_participantes(row[0])
        }

    def _get_participantes(self, servico_id: int) -> List[Dict]:
        """Retorna lista de diaristas e seus rateios para um serviço."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT d.id, d.nome, d.cpf, sd.valor_rateio
               FROM servico_diaristas sd
               JOIN diaristas d ON d.id = sd.diarista_id
               WHERE sd.servico_id = ?
               ORDER BY d.nome""",
            (servico_id,)
        )
        return [
            {'id': r[0], 'nome': r[1], 'cpf': r[2], 'valor_rateio': r[3]}
            for r in cursor.fetchall()
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # TOTAIS
    # ─────────────────────────────────────────────────────────────────────────

    def total_por_periodo(self, data_inicio: str, data_fim: str) -> float:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(valor), 0) FROM servicos WHERE data_servico BETWEEN ? AND ?",
            (data_inicio, data_fim)
        )
        return cursor.fetchone()[0]

    def total_por_diarista(self, diarista_id: int,
                           data_inicio: str = None, data_fim: str = None) -> float:
        cursor = self.conn.cursor()
        query  = """SELECT COALESCE(SUM(sd.valor_rateio), 0)
                    FROM servico_diaristas sd
                    JOIN servicos s ON s.id = sd.servico_id
                    WHERE sd.diarista_id = ?"""
        params = [diarista_id]
        if data_inicio and data_fim:
            query += " AND s.data_servico BETWEEN ? AND ?"
            params.extend([data_inicio, data_fim])
        cursor.execute(query, params)
        return cursor.fetchone()[0]

    # ─────────────────────────────────────────────────────────────────────────
    # RELATÓRIOS
    # ─────────────────────────────────────────────────────────────────────────

    def relatorio_por_centro_custo(self, data_inicio: str, data_fim: str) -> list:
        """[(centro, qtd_servicos, total_valor), ...]"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT cc.centro,
                      COUNT(s.id)  AS qtd_servicos,
                      SUM(s.valor) AS total_valor
               FROM servicos s
               JOIN centros_custo cc ON cc.id = s.centro_custo_id
               WHERE s.data_servico BETWEEN ? AND ?
               GROUP BY cc.id, cc.centro
               ORDER BY total_valor DESC""",
            (data_inicio, data_fim)
        )
        return cursor.fetchall()

    def relatorio_por_diarista(self, data_inicio: str, data_fim: str) -> list:
        """[(nome, cpf, qtd_servicos, total_valor), ...]"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT d.nome,
                      d.cpf,
                      COUNT(DISTINCT sd.servico_id) AS qtd_servicos,
                      SUM(sd.valor_rateio)          AS total_valor
               FROM servico_diaristas sd
               JOIN diaristas d  ON d.id  = sd.diarista_id
               JOIN servicos s   ON s.id  = sd.servico_id
               WHERE s.data_servico BETWEEN ? AND ?
               GROUP BY d.id, d.nome, d.cpf
               ORDER BY total_valor DESC""",
            (data_inicio, data_fim)
        )
        return cursor.fetchall()

    def relatorio_geral(self, data_inicio: str, data_fim: str) -> list:
        """[(data, diaristas_str, cpf_str, centro, descricao, valor), ...]"""
        cursor = self.conn.cursor()
        # Busca serviços do período
        cursor.execute(
            """SELECT s.id, s.data_servico, cc.centro, s.descricao, s.valor
               FROM servicos s
               JOIN centros_custo cc ON cc.id = s.centro_custo_id
               WHERE s.data_servico BETWEEN ? AND ?
               ORDER BY s.data_servico DESC""",
            (data_inicio, data_fim)
        )
        servicos = cursor.fetchall()

        resultado = []
        for s in servicos:
            partic = self._get_participantes(s[0])
            nomes  = ", ".join(p['nome'] for p in partic)
            cpfs   = ", ".join(p['cpf']  for p in partic)
            resultado.append((s[1], nomes, cpfs, s[2], s[3], s[4]))

        return resultado