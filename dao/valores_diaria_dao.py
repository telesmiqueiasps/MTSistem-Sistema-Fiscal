from database.conexao import garantir_banco


class ValoresDiariaDAO:
    def __init__(self):
        self.conn = garantir_banco()

    def buscar(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, valor_padrao, valor_diferente, valor_hora_extra, horas_por_diaria
            FROM valores_diaria
            ORDER BY id
            LIMIT 1
        """)
        return cur.fetchone()

    def salvar(self, valor_padrao, valor_diferente, valor_hora_extra, horas_por_diaria):
        cur = self.conn.cursor()

        registro = self.buscar()

        if registro:
            cur.execute("""
                UPDATE valores_diaria
                SET valor_padrao = ?,
                    valor_diferente = ?,
                    valor_hora_extra = ?,
                    horas_por_diaria = ?
                WHERE id = ?
            """, (
                valor_padrao,
                valor_diferente,
                valor_hora_extra,
                horas_por_diaria,
                registro[0]
            ))
        else:
            cur.execute("""
                INSERT INTO valores_diaria
                (valor_padrao, valor_diferente, valor_hora_extra, horas_por_diaria)
                VALUES (?, ?, ?, ?)
            """, (
                valor_padrao,
                valor_diferente,
                valor_hora_extra,
                horas_por_diaria
            ))

        self.conn.commit()
