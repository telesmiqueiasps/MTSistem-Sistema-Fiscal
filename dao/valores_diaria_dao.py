from database.conexao import garantir_banco


class ValoresDiariaDAO:
    def __init__(self):
        self.conn = garantir_banco()

    def buscar(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, valor_padrao, valor_diferente, valor_hora_extra
            FROM valores_diaria
            ORDER BY id
            LIMIT 1
        """)
        return cur.fetchone()

    def salvar(self, valor_padrao, valor_diferente, valor_hora_extra):
        cur = self.conn.cursor()

        registro = self.buscar()

        if registro:
            cur.execute("""
                UPDATE valores_diaria
                SET valor_padrao = ?,
                    valor_diferente = ?,
                    valor_hora_extra = ?
                WHERE id = ?
            """, (
                valor_padrao,
                valor_diferente,
                valor_hora_extra,
                registro[0]
            ))
        else:
            cur.execute("""
                INSERT INTO valores_diaria
                (valor_padrao, valor_diferente, valor_hora_extra)
                VALUES (?, ?, ?)
            """, (
                valor_padrao,
                valor_diferente,
                valor_hora_extra
            ))

        self.conn.commit()
