import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
from dao.usuario_dao import UsuarioDAO
from utils.constantes import CORES, VERSAO_ATUAL
from utils.auxiliares import resource_path, configurar_estilo

class TelaLogin:
    def __init__(self, root, versao_remota):
        self.root = root
        self.versao_remota = versao_remota
        self.dao = UsuarioDAO()


        self.root.title("MTSistem - Login")
        self.root.configure(bg=CORES['bg_main'])

        # Tamanho responsivo
        largura = int(self.root.winfo_screenwidth() * 0.35)
        altura = int(self.root.winfo_screenheight() * 0.55)
        self.root.geometry(f"{largura}x{altura}")
        self.root.minsize(500, 450)
        self.root.resizable(True, True)

        # ÍCONE
        caminho_icone = resource_path("Icones/logo.ico")
        self.root.iconbitmap(caminho_icone)

        self.centralizar_janela()
        configurar_estilo()
        self.criar_interface()

    def centralizar_janela(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def criar_interface(self):
        # =========================
        # FRAME PRINCIPAL
        # =========================
        main_frame = ttk.Frame(self.root, style="Main.TFrame", padding=30)
        main_frame.pack(fill="both", expand=True)

        # =========================
        # LOGO
        # =========================
        caminho_logo = resource_path("Icones/logo.png")
        img = Image.open(caminho_logo)
        img = img.resize((80, 80), Image.LANCZOS)
        self.logo_img = ImageTk.PhotoImage(img)

        ttk.Label(
            main_frame,
            image=self.logo_img,
            background=CORES['bg_main']
        ).pack(pady=(0, 15))

        ttk.Label(
            main_frame,
            text="Sistema Fiscal",
            font=('Segoe UI', 20, 'bold'),
            foreground=CORES['text_dark'],
            background=CORES['bg_main']
        ).pack()

        ttk.Label(
            main_frame,
            text="Selecione o usuário para entrar",
            font=('Segoe UI', 10),
            foreground=CORES['text_light'],
            background=CORES['bg_main']
        ).pack(pady=(5, 25))

        # =========================
        # CARD DE USUÁRIOS
        # =========================
        card = ttk.Frame(main_frame, style="Card.TFrame", padding=25)
        card.pack(fill="x")

        for user_id, nome, admin in self.dao.listar_usuarios():
            texto = f"{nome} {'(Admin)' if admin else ''}"

            btn = ttk.Button(
                card,
                text=texto,
                command=lambda i=user_id, n=nome: self.pedir_senha(i, n)
            )
            btn.pack(fill="x", pady=6)

        # =========================
        # RODAPÉ
        # =========================
        ttk.Label(
            main_frame,
            text="© MTSistem • Desenvolvido por Miquéias Teles - Versão " + VERSAO_ATUAL,
            font=('Segoe UI', 8),
            foreground=CORES['text_light'],
            background=CORES['bg_main']
        ).pack(pady=(30, 0))

    def pedir_senha(self, usuario_id, nome):
        from telas.tela_inicial import SistemaFiscal
        senha = simpledialog.askstring(
            "Senha",
            f"Digite a senha do usuário {nome}:",
            show="*",
            parent=self.root
        )

        if not senha:
            return

        auth = self.dao.autenticar(nome, senha)

        # ❌ Usuário ou senha inválidos
        if auth is None:
            messagebox.showerror(
                "Erro",
                "Usuário ou senha inválidos.",
                parent=self.root
            )
            return

        # 🔒 Sistema bloqueado
        if auth == "BLOQUEADO":
            messagebox.showwarning(
                "Sistema bloqueado",
                "O acesso está temporariamente bloqueado.\n\n"
                "Consulte o administrador.",
                parent=self.root
            )
            return

        # ✅ Login permitido
        usuario_id, is_admin = auth

        self.root.destroy()
        root = tk.Tk()
        SistemaFiscal(
            root,
            usuario_id=usuario_id,
            usuario_nome=nome,
            versao_remota=self.versao_remota
        )
        root.mainloop()
