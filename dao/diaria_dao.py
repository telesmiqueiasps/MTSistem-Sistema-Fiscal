from database.conexao import garantir_banco
from datetime import datetime


class DiariaDAO:
    def __init__(self):
        self.conn = garantir_banco()

    # =========================
    # DIARISTAS
    def listar_diaristas(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, nome FROM diaristas ORDER BY nome")
        return cur.fetchall()

    def buscar_cpf_diarista(self, diarista_id):
        cur = self.conn.cursor()
        cur.execute("SELECT cpf FROM diaristas WHERE id = ?", (diarista_id,))
        row = cur.fetchone()
        return row[0] if row else ""

    # =========================
    # CENTROS DE CUSTO
    def listar_centros_custo(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, centro FROM centros_custo ORDER BY centro")
        return cur.fetchall()

    # =========================
    # VALORES
    def buscar_valores_diaria(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT valor_padrao, valor_diferente, valor_hora_extra, horas_por_diaria
            FROM valores_diaria
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            return None

        return tuple(float(str(v).replace(",", ".")) for v in row)


    def salvar_diaria(self, dados):
        cur = self.conn.cursor()

        cur.execute("""
            INSERT INTO diarias (
                tipo_diaria,
                diarista,
                cpf,
                qtd_diarias,
                tipo_valor,
                vlr_diaria_hora,
                vlr_horas_extras,
                qtd_horas,
                vlr_unitario,
                centro_custo,
                vlr_total,
                descricao,
                data_emissao,
                caminho_arquivo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dados["tipo_diaria"],
            dados["diarista"],
            dados["cpf"],
            dados["qtd_diarias"],
            dados["tipo_valor"],
            dados["vlr_diaria_hora"],
            dados["vlr_horas_extras"],
            dados["qtd_horas"],
            dados["vlr_unitario"],
            dados["centro_custo"],
            dados["vlr_total"],
            dados["descricao"],
            dados["data_emissao"],
            dados["caminho_arquivo"]
        ))

        self.conn.commit()
        return cur.lastrowid


    def listar_diarias(self, filtro_nome="", data_inicio=None, data_fim=None):
        cur = self.conn.cursor()

        sql = """
            SELECT id, diarista, cpf, qtd_diarias, vlr_total,
                descricao, data_emissao, caminho_arquivo
            FROM diarias
            WHERE 1=1
        """

        params = []

        # 🔎 Filtro por nome ou CPF
        if filtro_nome:
            sql += " AND (diarista LIKE ? OR cpf LIKE ?)"
            params.append(f"%{filtro_nome}%")
            params.append(f"%{filtro_nome}%")

        # 📅 Filtro por período
        if data_inicio and data_fim:
            sql += " AND date(data_emissao) BETWEEN date(?) AND date(?)"
            params.append(data_inicio)
            params.append(data_fim)

        sql += " ORDER BY id DESC"

        cur.execute(sql, params)

        dados = []
        for r in cur.fetchall():
            dados.append({
                "id": r[0],
                "diarista": r[1],
                "cpf": r[2],
                "qtd_diarias": r[3],
                "vlr_total": r[4],
                "descricao": r[5],
                "data_emissao": r[6],
                "caminho_arquivo": r[7]
            })

        return dados



    

    def excluir_diaria(self, id_diaria):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM diarias WHERE id = ?", (id_diaria,))
        self.conn.commit()

    def buscar_diaria_por_id(self, id_diaria):
        cur = self.conn.cursor()

        cur.execute("""
            SELECT
                diarista,
                cpf,
                centro_custo,
                qtd_diarias,
                qtd_horas,
                vlr_unitario,    
                vlr_diaria_hora,
                vlr_horas_extras,
                vlr_total,
                descricao,
                tipo_diaria,
                data_emissao
            FROM diarias
            WHERE id = ?
        """, (id_diaria,))

        r = cur.fetchone()
        if not r:
            return None

        return {
            "nome": r[0],
            "cpf": r[1],
            "centro": r[2],
            "qtd_diarias": r[3],
            "qtd_horas": r[4],
            "vlr_unitario": r[5],
            "vlr_diaria_hora": r[6],
            "vlr_horas_extras": r[7],
            "valor_total": r[8],
            "descricao": r[9],
            "tipo_diaria": r[10],
            "data_emissao": r[11]
        }

    # =========================
    # RELATÓRIOS
    # =========================

    def relatorio_por_diarista(self, data_inicio: str, data_fim: str) -> list:
        """
        Retorna total agrupado por diarista no período
        Retorna: [(diarista, cpf, qtd_lancamentos, total_diarias, total_valor)]
        """

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                diarista,
                cpf,
                COUNT(id)             AS qtd_lancamentos,
                SUM(qtd_diarias)      AS total_diarias,
                SUM(vlr_total)        AS total_valor
            FROM diarias
            WHERE date(data_emissao) BETWEEN date(?) AND date(?)
            GROUP BY diarista, cpf
            ORDER BY total_valor DESC
            """,
            (data_inicio, data_fim)
        )

        return cursor.fetchall()


    def relatorio_resumo_periodo(self, data_inicio: str, data_fim: str) -> tuple:
        """
        Retorna resumo geral do período
        Retorna: (qtd_lancamentos, total_diarias, total_valor)
        """

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(id),
                SUM(qtd_diarias),
                SUM(vlr_total)
            FROM diarias
            WHERE date(data_emissao) BETWEEN date(?) AND date(?)
            """,
            (data_inicio, data_fim)
        )

        return cursor.fetchone()
    
    def relatorio_geral(self, data_inicio: str, data_fim: str) -> list:
        """
        Retorna todas as diárias detalhadas no período
        Retorna:
        [(data, diarista, cpf, qtd_diarias, valor, descricao)]
        """

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                data_emissao,
                diarista,
                cpf,
                qtd_diarias,
                vlr_total,
                descricao
            FROM diarias
            WHERE date(data_emissao) BETWEEN date(?) AND date(?)
            ORDER BY date(data_emissao) DESC
            """,
            (data_inicio, data_fim)
        )

        return cursor.fetchall()


    def relatorio_por_mes(self, data_inicio, data_fim):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                strftime('%m/%Y', data_emissao) as mes,
                SUM(qtd_diarias),
                SUM(vlr_total)
            FROM diarias
            WHERE date(data_emissao) BETWEEN date(?) AND date(?)
            GROUP BY strftime('%Y-%m', data_emissao)
            ORDER BY strftime('%Y-%m', data_emissao)
        """, (data_inicio, data_fim))
        return cursor.fetchall()

    def relatorio_por_centro_custo(self, data_inicio: str, data_fim: str) -> list:
        """
        Retorna total agrupado por centro de custo no período
        Retorna: [(centro_custo, qtd_lancamentos, total_diarias, total_valor)]
        """

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                centro_custo,
                COUNT(id)            AS qtd_lancamentos,
                SUM(qtd_diarias)     AS total_diarias,
                SUM(vlr_total)       AS total_valor
            FROM diarias
            WHERE date(data_emissao) BETWEEN date(?) AND date(?)
            GROUP BY centro_custo
            ORDER BY total_valor DESC
            """,
            (data_inicio, data_fim)
        )

        return cursor.fetchall()
