class Sessao:
    def __init__(self):
        self.usuario_id = None
        self.usuario_nome = None
        self.is_admin = False
        self.empresa_id = None
        self.empresa_nome = None
        self.db_empresa_path = None

        # Preenchidos pela verificação online de licença/versão no startup
        # (services.licenca_online_service). Ficam None se a consulta falhar
        # (sem internet, site fora do ar, etc.) — nesse caso o sistema cai
        # de volta na verificação local de versão (utils.auxiliares).
        self.versao_remota = None
        self.exe_url_remoto = None
        self.mensagem_update_remoto = None

# Instância global
sessao = Sessao()
