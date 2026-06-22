from datetime import datetime
from database.empresa_conexao import get_conn_empresa


def _dict(cur, row):
    if row is None:
        return None
    colunas = [d[0] for d in cur.description]
    return dict(zip(colunas, row))


class NotasFiscaisDAO:
    def __init__(self):
        self.conn = get_conn_empresa()

    # ─────────────────────────────────────────────────────────────────────────
    # FORNECEDORES
    # ─────────────────────────────────────────────────────────────────────────

    def listar_fornecedores(self, busca=None):
        sql = """
            SELECT f.*,
                   COUNT(nf.id) as qtd_notas,
                   SUM(nf.valor) as valor_total,
                   SUM(CASE WHEN nf.pago=0 THEN nf.valor ELSE 0 END) as valor_pendente
            FROM fornecedores f
            LEFT JOIN notas_fiscais nf ON LOWER(TRIM(nf.emitente)) = LOWER(TRIM(f.nome))
            WHERE 1=1
        """
        params = []
        if busca:
            sql += " AND (f.nome LIKE ? OR f.cnpj_cpf LIKE ?)"
            b = f"%{busca}%"
            params += [b, b]
        sql += " GROUP BY f.id ORDER BY f.nome COLLATE NOCASE"
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return [_dict(cur, r) for r in cur.fetchall()]

    def get_fornecedor(self, forn_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM fornecedores WHERE id=?", (forn_id,))
        return _dict(cur, cur.fetchone())

    def inserir_fornecedor(self, dados: dict):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT id FROM fornecedores
               WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))
               AND LOWER(TRIM(COALESCE(cnpj_cpf,''))) = LOWER(TRIM(COALESCE(?,'')))""",
            (dados.get('nome', ''), dados.get('cnpj_cpf', '') or '')
        )
        if cur.fetchone():
            return None, "já_existe"
        cols = ", ".join(dados.keys())
        placeholders = ", ".join(["?"] * len(dados))
        cur.execute(
            f"INSERT INTO fornecedores ({cols}) VALUES ({placeholders})",
            list(dados.values())
        )
        self.conn.commit()
        return cur.lastrowid, "ok"

    def atualizar_fornecedor(self, forn_id, dados: dict):
        dados = dict(dados)
        dados["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.conn.cursor()
        cur.execute(
            """SELECT id FROM fornecedores
               WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))
               AND LOWER(TRIM(COALESCE(cnpj_cpf,''))) = LOWER(TRIM(COALESCE(?,'')))
               AND id != ?""",
            (dados.get('nome', ''), dados.get('cnpj_cpf', '') or '', forn_id)
        )
        if cur.fetchone():
            return "já_existe"
        sets = ", ".join([f"{k} = ?" for k in dados.keys()])
        cur.execute(f"UPDATE fornecedores SET {sets} WHERE id=?",
                    list(dados.values()) + [forn_id])
        self.conn.commit()
        return "ok"

    def excluir_fornecedor(self, forn_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM fornecedores WHERE id=?", (forn_id,))
        self.conn.commit()

    def upsert_fornecedor_auto(self, nome: str, cnpj_cpf: str = "") -> int | None:
        """Insere fornecedor se não existir. Retorna o id (novo ou existente)."""
        nome = (nome or "").strip()
        cnpj_cpf = (cnpj_cpf or "").strip()
        if not nome:
            return None
        cur = self.conn.cursor()
        cur.execute(
            """SELECT id FROM fornecedores
               WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))
               AND LOWER(TRIM(COALESCE(cnpj_cpf,''))) = LOWER(TRIM(COALESCE(?,'')))""",
            (nome, cnpj_cpf)
        )
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "INSERT INTO fornecedores (nome, cnpj_cpf) VALUES (?,?)",
            (nome, cnpj_cpf)
        )
        self.conn.commit()
        return cur.lastrowid

    def listar_fornecedores_select(self):
        """Lista simplificada para dropdowns/autocomplete."""
        cur = self.conn.cursor()
        cur.execute("SELECT id, nome, cnpj_cpf FROM fornecedores ORDER BY nome COLLATE NOCASE")
        return [_dict(cur, r) for r in cur.fetchall()]

    def importar_emitentes_das_notas(self):
        """Migra emitentes das notas existentes para a tabela de fornecedores."""
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT emitente, cnpj_cpf FROM notas_fiscais WHERE emitente != ''")
        notas = cur.fetchall()
        for emitente, cnpj_cpf in notas:
            try:
                cur.execute(
                    "INSERT OR IGNORE INTO fornecedores (nome, cnpj_cpf) VALUES (?, ?)",
                    (emitente.strip(), (cnpj_cpf or '').strip())
                )
            except Exception:
                pass
        self.conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # NOTAS FISCAIS
    # ─────────────────────────────────────────────────────────────────────────

    def listar_notas(self, filtro_status=None, busca=None,
                     emitente_id=None, data_ini=None, data_fim=None):
        """filtro_status: None (todos) | "pendente" (sem recibo e sem pagamento)
        | "ok" (recibo anexado, ainda não marcada como paga) | "pago"."""
        sql = """
            SELECT nf.*,
                   COUNT(r.id) as qtd_recibos
            FROM notas_fiscais nf
            LEFT JOIN recibos r ON r.nota_id = nf.id
            WHERE 1=1
        """
        params = []
        if filtro_status in ("pendente", "ok"):
            sql += " AND nf.pago = 0"
        elif filtro_status == "pago":
            sql += " AND nf.pago = 1"
        if busca:
            sql += " AND (nf.numero LIKE ? OR nf.emitente LIKE ? OR nf.descricao_servico LIKE ?)"
            b = f"%{busca}%"
            params += [b, b, b]
        if emitente_id:
            sql += """ AND LOWER(TRIM(nf.emitente)) = (
                SELECT LOWER(TRIM(nome)) FROM fornecedores WHERE id=?)"""
            params.append(emitente_id)
        if data_ini:
            sql += " AND nf.data_emissao >= ?"
            params.append(data_ini)
        if data_fim:
            sql += " AND nf.data_emissao <= ?"
            params.append(data_fim)
        sql += " GROUP BY nf.id"
        if filtro_status == "pendente":
            sql += " HAVING qtd_recibos = 0"
        elif filtro_status == "ok":
            sql += " HAVING qtd_recibos > 0"
        sql += " ORDER BY nf.data_emissao DESC, nf.id DESC"
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return [_dict(cur, r) for r in cur.fetchall()]

    def get_nota(self, nota_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM notas_fiscais WHERE id = ?", (nota_id,))
        return _dict(cur, cur.fetchone())

    def buscar_nota_duplicada(self, numero, emitente, chave_acesso=None):
        """Evita cadastrar a mesma NFS-e duas vezes. Prioriza a chave de
        acesso (única por natureza); sem ela, cai para número + emitente."""
        cur = self.conn.cursor()
        if chave_acesso:
            cur.execute(
                "SELECT * FROM notas_fiscais WHERE chave_acesso = ? AND chave_acesso != ''",
                (chave_acesso,)
            )
            row = cur.fetchone()
            if row:
                return _dict(cur, row)
        if numero and emitente:
            cur.execute(
                """SELECT * FROM notas_fiscais
                   WHERE LOWER(TRIM(numero)) = LOWER(TRIM(?))
                   AND LOWER(TRIM(emitente)) = LOWER(TRIM(?))""",
                (numero, emitente)
            )
            row = cur.fetchone()
            if row:
                return _dict(cur, row)
        return None

    def inserir_nota(self, dados: dict):
        cur = self.conn.cursor()
        cols = ", ".join(dados.keys())
        placeholders = ", ".join(["?"] * len(dados))
        cur.execute(
            f"INSERT INTO notas_fiscais ({cols}) VALUES ({placeholders})",
            list(dados.values())
        )
        self.conn.commit()
        return cur.lastrowid

    def atualizar_nota(self, nota_id, dados: dict):
        dados = dict(dados)
        dados["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sets = ", ".join([f"{k} = ?" for k in dados.keys()])
        cur = self.conn.cursor()
        cur.execute(f"UPDATE notas_fiscais SET {sets} WHERE id = ?",
                    list(dados.values()) + [nota_id])
        self.conn.commit()

    def excluir_nota(self, nota_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM notas_fiscais WHERE id = ?", (nota_id,))
        self.conn.commit()

    def marcar_pago(self, nota_id, data_pagamento=None):
        dp = data_pagamento or datetime.now().strftime("%Y-%m-%d")
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE notas_fiscais SET pago=1, data_pagamento=?, atualizado_em=datetime('now','localtime') WHERE id=?",
            (dp, nota_id)
        )
        self.conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # RECIBOS
    # ─────────────────────────────────────────────────────────────────────────

    def inserir_recibo(self, nota_id, arquivo, nome_arquivo):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO recibos (nota_id, arquivo, nome_arquivo) VALUES (?, ?, ?)",
            (nota_id, arquivo, nome_arquivo)
        )
        self.conn.commit()
        return cur.lastrowid

    def listar_recibos(self, nota_id=None):
        sql = """
            SELECT r.*, nf.numero, nf.emitente, nf.valor
            FROM recibos r
            JOIN notas_fiscais nf ON nf.id = r.nota_id
        """
        params = []
        if nota_id:
            sql += " WHERE r.nota_id = ?"
            params.append(nota_id)
        sql += " ORDER BY r.criado_em DESC"
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return [_dict(cur, r) for r in cur.fetchall()]

    def excluir_recibo(self, recibo_id):
        cur = self.conn.cursor()
        cur.execute("SELECT arquivo FROM recibos WHERE id=?", (recibo_id,))
        row = cur.fetchone()
        if row:
            cur.execute("DELETE FROM recibos WHERE id=?", (recibo_id,))
            self.conn.commit()
            return row[0]
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # ESTATÍSTICAS
    # ─────────────────────────────────────────────────────────────────────────

    def get_stats(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN pago=0 AND qtd_recibos=0 THEN 1 ELSE 0 END) as pendentes,
                SUM(CASE WHEN pago=0 AND qtd_recibos>0 THEN 1 ELSE 0 END) as ok,
                SUM(CASE WHEN pago=1 THEN 1 ELSE 0 END) as pagos,
                SUM(CASE WHEN pago=0 AND qtd_recibos=0 THEN valor ELSE 0 END) as valor_pendente,
                SUM(CASE WHEN pago=0 AND qtd_recibos>0 THEN valor ELSE 0 END) as valor_ok,
                SUM(CASE WHEN pago=1 THEN valor ELSE 0 END) as valor_pago,
                SUM(valor) as valor_total
            FROM (
                SELECT nf.*, COUNT(r.id) as qtd_recibos
                FROM notas_fiscais nf
                LEFT JOIN recibos r ON r.nota_id = nf.id
                GROUP BY nf.id
            )
        """)
        return _dict(cur, cur.fetchone())
