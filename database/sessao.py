class Sessao:
    def __init__(self):
        self.usuario_id = None
        self.usuario_nome = None
        self.is_admin = False
        self.empresa_id = None
        self.empresa_nome = None
        self.db_empresa_path = None

# Instância global
sessao = Sessao()
