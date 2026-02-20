# dao/empresa_central_dao.py

from database.conexao import garantir_banco
import os
import shutil


class EmpresaCentralDAO:
    def __init__(self):
        self.conn = garantir_banco()

    def listar_empresas(self, apenas_ativas=True):
        """Lista todas as empresas cadastradas."""
        cur = self.conn.cursor()
        query = "SELECT id, nome_exibicao, caminho_banco, ativo FROM empresa"
        if apenas_ativas:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome_exibicao"
        
        cur.execute(query)
        colunas = [desc[0] for desc in cur.description]
        return [dict(zip(colunas, row)) for row in cur.fetchall()]

    def buscar_empresa(self, empresa_id):
        """Busca uma empresa específica."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, nome_exibicao, caminho_banco, ativo FROM empresa WHERE id = ?",
            (empresa_id,)
        )
        row = cur.fetchone()
        if row:
            colunas = [desc[0] for desc in cur.description]
            return dict(zip(colunas, row))
        return None

    def cadastrar_empresa(self, nome_exibicao):
        """Cria uma nova empresa copiando do modelo."""
        cur = self.conn.cursor()

        try:
            self.conn.execute("BEGIN")

            # Inserir empresa sem caminho
            cur.execute(
                "INSERT INTO empresa (nome_exibicao, caminho_banco, ativo) VALUES (?, ?, 1)",
                (nome_exibicao, "")
            )
            empresa_id = cur.lastrowid

            # Criar banco físico
            caminho_banco = self._criar_banco_empresa(empresa_id)

            # Atualizar caminho
            cur.execute(
                "UPDATE empresa SET caminho_banco = ? WHERE id = ?",
                (caminho_banco, empresa_id)
            )

            self.conn.commit()
            return empresa_id

        except Exception as e:
            self.conn.rollback()
            raise e

    def atualizar_empresa(self, empresa_id, nome_exibicao):
        """Atualiza nome de exibição da empresa."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE empresa SET nome_exibicao = ? WHERE id = ?",
                (nome_exibicao, empresa_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar empresa: {e}")
            return False

    def inativar_empresa(self, empresa_id):
        """Inativa uma empresa (soft delete)."""
        try:
            cur = self.conn.cursor()
            cur.execute("UPDATE empresa SET ativo = 0 WHERE id = ?", (empresa_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao inativar empresa: {e}")
            return False

    def excluir_empresa(self, empresa_id):
        """Exclui permanentemente uma empresa e seu banco de dados."""
        try:
            cur = self.conn.cursor()
            
            # Busca caminho do banco
            cur.execute("SELECT caminho_banco FROM empresa WHERE id = ?", (empresa_id,))
            row = cur.fetchone()
            
            if not row:
                return False
            
            caminho_banco = row[0]
            
            # Remove permissões de usuários
            cur.execute("DELETE FROM usuario_empresas WHERE empresa_id = ?", (empresa_id,))
            
            # Remove empresa
            cur.execute("DELETE FROM empresa WHERE id = ?", (empresa_id,))
            
            self.conn.commit()
            
            # Remove banco físico se existir
            if caminho_banco and os.path.exists(caminho_banco):
                os.remove(caminho_banco)
            
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao excluir empresa: {e}")
            return False

    def _criar_banco_empresa(self, empresa_id):
        """Cria banco físico copiando do modelo."""
        base_dir = r"T:\MTSistem\db\empresas"
        modelo = r"T:\MTSistem\db\modelo_empresa.db"

        os.makedirs(base_dir, exist_ok=True)

        destino = os.path.join(base_dir, f"{empresa_id}.db")

        if not os.path.exists(modelo):
            raise FileNotFoundError(
                f"Arquivo modelo não encontrado: {modelo}\n\n"
                "Crie o arquivo modelo_empresa.db na pasta db/"
            )

        if os.path.exists(destino):
            raise FileExistsError(f"Banco {empresa_id}.db já existe.")

        shutil.copyfile(modelo, destino)
        return destino

    # ═════════════════════════════════════════════════════════════════════════
    # GERENCIAMENTO DE PERMISSÕES
    # ═════════════════════════════════════════════════════════════════════════

    def listar_usuarios_empresa(self, empresa_id):
        """Lista todos os usuários com acesso à empresa."""
        cur = self.conn.cursor()
        cur.execute(
            """SELECT u.id, u.nome, u.admin
               FROM usuarios u
               JOIN usuario_empresas ue ON ue.usuario_id = u.id
               WHERE ue.empresa_id = ?
               ORDER BY u.nome""",
            (empresa_id,)
        )
        return cur.fetchall()

    def listar_usuarios_sem_acesso(self, empresa_id):
        """Lista usuários que NÃO têm acesso à empresa."""
        cur = self.conn.cursor()
        cur.execute(
            """SELECT u.id, u.nome, u.admin
               FROM usuarios u
               WHERE u.id NOT IN (
                   SELECT usuario_id 
                   FROM usuario_empresas 
                   WHERE empresa_id = ?
               )
               ORDER BY u.nome""",
            (empresa_id,)
        )
        return cur.fetchall()

    def adicionar_usuario_empresa(self, empresa_id, usuario_id):
        """Concede acesso de um usuário à empresa."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO usuario_empresas (empresa_id, usuario_id) VALUES (?, ?)",
                (empresa_id, usuario_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao adicionar usuário: {e}")
            return False

    def remover_usuario_empresa(self, empresa_id, usuario_id):
        """Remove acesso de um usuário à empresa."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "DELETE FROM usuario_empresas WHERE empresa_id = ? AND usuario_id = ?",
                (empresa_id, usuario_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao remover usuário: {e}")
            return False

    def contar_usuarios_empresa(self, empresa_id):
        """Conta quantos usuários têm acesso à empresa."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM usuario_empresas WHERE empresa_id = ?",
            (empresa_id,)
        )
        return cur.fetchone()[0]