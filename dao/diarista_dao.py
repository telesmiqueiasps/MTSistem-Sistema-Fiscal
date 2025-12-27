from database.conexao import garantir_banco


class DiaristaDAO:
    def __init__(self):
        self.conn = garantir_banco()

    def listar(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, nome, cpf FROM diaristas ORDER BY nome"
        )
        return cur.fetchall()

    def buscar(self, diarista_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, nome, cpf FROM diaristas WHERE id = ?",
            (diarista_id,)
        )
        return cur.fetchone()

    def salvar(self, nome, cpf):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO diaristas (nome, cpf) VALUES (?, ?)",
            (nome, cpf)
        )
        self.conn.commit()

    def atualizar(self, diarista_id, nome, cpf):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE diaristas SET nome = ?, cpf = ? WHERE id = ?",
            (nome, cpf, diarista_id)
        )
        self.conn.commit()

    def excluir(self, diarista_id):
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM diaristas WHERE id = ?",
            (diarista_id,)
        )
        self.conn.commit()


    def buscar_por_cpf(self, cpf):
        cur = self.conn.cursor()

        cur.execute(
            "SELECT id, nome FROM diaristas WHERE cpf = ?",
            (cpf,)
        )

        resultado = cur.fetchone()
        return resultado
