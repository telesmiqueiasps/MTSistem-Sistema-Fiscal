from database.conexao import garantir_banco


class CentroCustoDAO:
    def __init__(self):
        self.conn = garantir_banco()

    def listar(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, centro FROM centros_custo ORDER BY centro"
        )
        return cur.fetchall()

    def salvar(self, centro):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO centros_custo (centro) VALUES (?)",
            (centro,)
        )
        self.conn.commit()

    def atualizar(self, centro_id, centro):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE centros_custo SET centro = ? WHERE id = ?",
            (centro, centro_id)
        )
        self.conn.commit()

    def excluir(self, centro_id):
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM centros_custo WHERE id = ?",
            (centro_id,)
        )
        self.conn.commit()
