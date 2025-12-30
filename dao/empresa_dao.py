import sqlite3
from database.conexao import garantir_banco  # ajuste se seu projeto usar outro padrão

class EmpresaDAO:
    def __init__(self):
        self.conn = garantir_banco()

    def buscar_empresa(self):
        cur = self.conn.cursor()

        cur.execute("SELECT * FROM empresa LIMIT 1")
        row = cur.fetchone()


        if not row:
            return None

        colunas = [desc[0] for desc in cur.description]
        return dict(zip(colunas, row))

    def salvar_empresa(self, dados):
        cur = self.conn.cursor()

        cur.execute("""
            INSERT INTO empresa (
                razao_social, nome_fantasia, cnpj, inscricao_estadual,
                endereco, cep, cidade, uf, contato
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dados["razao_social"],
            dados["nome_fantasia"],
            dados["cnpj"],
            dados["inscricao_estadual"],
            dados["endereco"],
            dados["cep"],
            dados["cidade"],
            dados["uf"],
            dados["contato"]
        ))

        self.conn.commit()
    

    def atualizar_empresa(self, dados):
        cur = self.conn.cursor()

        cur.execute("""
            UPDATE empresa SET
                razao_social = ?,
                nome_fantasia = ?,
                cnpj = ?,
                inscricao_estadual = ?,
                endereco = ?,
                cep = ?,
                cidade = ?,
                uf = ?,
                contato = ?
            WHERE id = ?
        """, (
            dados["razao_social"],
            dados["nome_fantasia"],
            dados["cnpj"],
            dados["inscricao_estadual"],
            dados["endereco"],
            dados["cep"],
            dados["cidade"],
            dados["uf"],
            dados["contato"],
            dados["id"]
        ))

        self.conn.commit()
       