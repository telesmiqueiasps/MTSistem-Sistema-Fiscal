
from typing import Optional, List, Tuple
from database.empresa_conexao import get_conn_empresa


class DiaristaDAO:
    def __init__(self):
        self.conn = get_conn_empresa()

    # ─────────────────────────────────────────────────────────────────────────
    # LISTAGEM
    # ─────────────────────────────────────────────────────────────────────────

    def listar(self, apenas_ativos: bool = True) -> List[Tuple]:
        """Lista diaristas. Por padrão retorna apenas os ativos."""
        cur = self.conn.cursor()
        query = "SELECT id, nome, cpf, ativo, data_admissao FROM diaristas"
        if apenas_ativos:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome"
        cur.execute(query)
        return cur.fetchall()

    def buscar(self, diarista_id: int) -> Optional[Tuple]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, nome, cpf, ativo, data_admissao FROM diaristas WHERE id = ?",
            (diarista_id,)
        )
        return cur.fetchone()

    def buscar_por_cpf(self, cpf: str) -> Optional[Tuple]:
        """Retorna (id, nome) se CPF já existir, independente do status."""
        cur = self.conn.cursor()
        cur.execute("SELECT id, nome FROM diaristas WHERE cpf = ?", (cpf,))
        return cur.fetchone()

    # ─────────────────────────────────────────────────────────────────────────
    # ESCRITA
    # ─────────────────────────────────────────────────────────────────────────

    def salvar(self, nome: str, cpf: str, data_admissao: str) -> int:
        """Cria um novo diarista ativo. Retorna o id gerado."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO diaristas (nome, cpf, ativo, data_admissao) VALUES (?, ?, 1, ?)",
            (nome, cpf, data_admissao)
        )
        self.conn.commit()
        return cur.lastrowid

    def atualizar(self, diarista_id: int, nome: str, cpf: str,
                  data_admissao: str) -> bool:
        """Atualiza dados cadastrais. Não altera o status ativo/inativo."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE diaristas SET nome = ?, cpf = ?, data_admissao = ? WHERE id = ?",
                (nome, cpf, data_admissao, diarista_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar diarista: {e}")
            return False

    def reativar(self, diarista_id: int, nova_data_admissao: str) -> bool:
        """Reativa um diarista inativo com nova data de admissão."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE diaristas SET ativo = 1, data_admissao = ? WHERE id = ?",
                (nova_data_admissao, diarista_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao reativar diarista: {e}")
            return False

    def inativar(self, diarista_id: int, data_inativacao: str) -> bool:
        """Inativa um diarista."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE diaristas SET ativo = 0 WHERE id = ?",
                (diarista_id,)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao inativar diarista: {e}")
            return False

    def excluir(self, diarista_id: int) -> bool:
        """Remove permanentemente. Use inativar() para desligamentos normais."""
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM diaristas WHERE id = ?", (diarista_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao excluir diarista: {e}")
            return False