import sqlite3
from database.empresa_conexao import get_conn_empresa # ajuste se seu projeto usar outro padrão
import os
import shutil
class EmpresaDAO:
    def __init__(self):
        self.conn = get_conn_empresa()

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

        # 🔥 Pega o ID recém criado
        empresa_id = cur.lastrowid

        # 🔥 Cria banco físico da empresa
        self._criar_banco_empresa(empresa_id)

        return empresa_id

    

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
       

    def _criar_banco_empresa(self, empresa_id):
        base_dir = r"T:\MTSistem\db\empresas"
        os.makedirs(base_dir, exist_ok=True)

        destino = os.path.join(base_dir, f"{empresa_id}.db")
        modelo = r"T:\MTSistem\db\modelo_empresa.db"

        shutil.copyfile(modelo, destino)
   