import hashlib
from utils.constantes import VERSAO_ATUAL, CAMINHO_EXE_ATUALIZADO
from database.conexao import garantir_banco

class UsuarioDAO:
    def __init__(self):
        self.conn = garantir_banco()
        self.criar_tabelas()
        self.criar_admin_inicial()
        self.criar_configuracoes_padrao()

    # ==========================
    # TABELAS
    # ==========================
    def criar_tabelas(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                admin INTEGER DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS permissoes (
                usuario_id INTEGER,
                modulo TEXT,
                permitido INTEGER DEFAULT 0,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS empresa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                razao_social TEXT NOT NULL,
                nome_fantasia TEXT,
                cnpj TEXT NOT NULL UNIQUE,
                inscricao_estadual TEXT,
                endereco TEXT,
                cep TEXT,
                cidade TEXT,
                uf TEXT,
                contato TEXT
            )
        """)


        cur.execute("""
            CREATE TABLE IF NOT EXISTS diaristas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf TEXT NOT NULL UNIQUE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS centros_custo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                centro TEXT NOT NULL UNIQUE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS valores_diaria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                valor_padrao REAL NOT NULL,
                valor_diferente REAL,
                valor_hora_extra REAL,
                horas_por_diaria REAL NOT NULL   
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS diarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_diaria TEXT NOT NULL,
                diarista TEXT NOT NULL,
                cpf TEXT NOT NULL,
                qtd_diarias INTEGER DEFAULT 0,
                tipo_valor TEXT NOT NULL,
                vlr_diaria_hora REAL DEFAULT 0,
                vlr_horas_extras REAL DEFAULT 0,
                qtd_horas REAL DEFAULT 0,
                vlr_unitario REAL NOT NULL,
                centro_custo TEXT NOT NULL,
                vlr_total REAL NOT NULL,
                descricao TEXT,
                data_emissao TEXT NOT NULL,
                caminho_arquivo TEXT NOT NULL
            )
        """)


        self.conn.commit()

    # ==========================
    # Configurações padrão
    # ==========================
    def criar_configuracoes_padrao(self):
        configs = {
            "versao_atual": VERSAO_ATUAL,
            "atualizacao_liberada": "NAO",
            "sistema_bloqueado": "NAO",
            "mensagem_update": "Atualização disponível",
            "exe_atualizacao": CAMINHO_EXE_ATUALIZADO
        }

        cur = self.conn.cursor()

        for chave, valor in configs.items():
            cur.execute("""
                INSERT INTO configuracoes (chave, valor)
                VALUES (?, ?)
                ON CONFLICT(chave) DO NOTHING
            """, (chave, valor))

        self.conn.commit()


    def get_config(self, chave, default=None):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT valor FROM configuracoes WHERE chave=?",
            (chave,)
        )
        row = cur.fetchone()
        return row[0] if row else default

    
    def set_config(self, chave, valor):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO configuracoes (chave, valor)
            VALUES (?, ?)
            ON CONFLICT(chave)
            DO UPDATE SET valor = excluded.valor
        """, (chave, str(valor)))
        self.conn.commit()

    def get_versao_atual_sistema(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT valor FROM configuracoes WHERE chave = 'versao_atual'"
        )
        row = cur.fetchone()
        return row[0] if row else None

    # ==========================
    # HASH
    # ==========================
    def hash_senha(self, senha):
        return hashlib.sha256(senha.encode("utf-8")).hexdigest()

    # ==========================
    # ADMIN PADRÃO
    # ==========================
    def criar_admin_inicial(self):
        cur = self.conn.cursor()

        # Verifica se já existe algum admin
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE admin = 1")
        existe_admin = cur.fetchone()[0]

        if existe_admin == 0:
            senha_hash = self.hash_senha("123456")

            cur.execute("""
                INSERT INTO usuarios (nome, senha, admin)
                VALUES (?, ?, 1)
            """, ("admin", senha_hash))

            admin_id = cur.lastrowid

            # Concede todas as permissões
            modulos = [
                "abrir_extrator",
                "abrir_comparador",
                "abrir_triagem",
                "abrir_extrator_pdf",
                "abrir_diaristas",
                "abrir_centros_custo",
                "abrir_diarias",
                "usuarios_admin"
            ]

            for modulo in modulos:
                cur.execute("""
                    INSERT INTO permissoes (usuario_id, modulo, permitido)
                    VALUES (?, ?, 1)
                """, (admin_id, modulo))

            self.conn.commit()

    # ==========================
    # AUTENTICAÇÃO
    # ==========================
    def autenticar(self, nome, senha):
        cur = self.conn.cursor()

        # 1️⃣ Valida usuário e senha
        cur.execute(
            "SELECT id, admin FROM usuarios WHERE nome=? AND senha=?",
            (nome, self.hash_senha(senha))
        )
        usuario = cur.fetchone()

        if not usuario:
            return None  # usuário ou senha inválidos

        usuario_id, is_admin = usuario

        # 2️⃣ Verifica se o sistema está bloqueado
        cur.execute(
            "SELECT valor FROM configuracoes WHERE chave='sistema_bloqueado'"
        )
        row = cur.fetchone()

        sistema_bloqueado = row and row[0] == "SIM"

        # 3️⃣ Se bloqueado e NÃO for admin → bloqueia acesso
        if sistema_bloqueado and not is_admin:
            return "BLOQUEADO"

        # 4️⃣ Login permitido
        return usuario_id, is_admin



    def listar_usuarios(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, nome, admin FROM usuarios")
        return cur.fetchall()

    def permissoes_usuario(self, usuario_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT modulo FROM permissoes WHERE usuario_id=? AND permitido=1",
            (usuario_id,)
        )
        return [r[0] for r in cur.fetchall()]
    
    def is_admin(self, usuario_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT admin FROM usuarios WHERE id=?",
            (usuario_id,)
        )
        row = cur.fetchone()
        return row and row[0] == 1
    
    def criar_usuario(self, nome, senha, admin):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (nome, senha, admin) VALUES (?, ?, ?)",
            (nome, self.hash_senha(senha), admin)
        )
        self.conn.commit()
        return cur.lastrowid



    def salvar_permissoes(self, usuario_id, permissoes):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM permissoes WHERE usuario_id=?", (usuario_id,))
        
        for modulo, permitido in permissoes.items():
            cur.execute(
                "INSERT INTO permissoes (usuario_id, modulo, permitido) VALUES (?, ?, ?)",
                (usuario_id, modulo, int(permitido))
            )
        self.conn.commit()

    def buscar_usuario(self, usuario_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, nome, admin FROM usuarios WHERE id=?",
            (usuario_id,)
        )
        return cur.fetchone()


    def atualizar_usuario(self, usuario_id, nome, admin):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE usuarios SET nome=?, admin=? WHERE id=?",
            (nome, admin, usuario_id)
        )
        self.conn.commit()



    def atualizar_senha(self, usuario_id, senha):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE usuarios SET senha=? WHERE id=?",
            (self.hash_senha(senha), usuario_id)
        )
        self.conn.commit()


    def excluir_usuario(self, usuario_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM permissoes WHERE usuario_id=?", (usuario_id,))
        cur.execute("DELETE FROM usuarios WHERE id=?", (usuario_id,))
        self.conn.commit()
    
    def usuario_admin(self, usuario_id):
        cur = self.conn.cursor()
        cur.execute("SELECT admin FROM usuarios WHERE id=?", (usuario_id,))
        row = cur.fetchone()
        return bool(row and row[0])