import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
from dao.usuario_dao import UsuarioDAO
from utils.constantes import CORES, VERSAO_ATUAL
from utils.auxiliares import resource_path, configurar_estilo


class TelaLogin:
    def __init__(self, root, versao_remota=None):
        self.root = root
        self.versao_remota = versao_remota
        self.dao = UsuarioDAO()

        self.root.title("MTSistem")
        self.root.configure(bg='#fafbfc')

        largura = 480
        altura = 620
        self.root.geometry(f"{largura}x{altura}")
        self.root.resizable(False, False)

        try:
            caminho_icone = resource_path("Icones/logo.ico")
            self.root.iconbitmap(caminho_icone)
        except Exception:
            pass

        self.centralizar_janela()
        configurar_estilo()
        self.criar_interface()

    def centralizar_janela(self):
        self.root.update_idletasks()
        w, h = 480, 620
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def criar_interface(self):
        # Container principal
        container = tk.Frame(self.root, bg='#fafbfc')
        container.pack(fill="both", expand=True, padx=50, pady=50)

        # ══════════════════════════════════════════════════════════════════════
        # LOGO MINIMALISTA
        # ══════════════════════════════════════════════════════════════════════
        try:
            caminho_logo = resource_path("Icones/logo.png")
            img = Image.open(caminho_logo)
            img = img.resize((56, 56), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            tk.Label(container, image=self.logo_img,
                     bg='#fafbfc').pack(pady=(0, 12))
        except Exception:
            pass

        # Título clean
        tk.Label(container, text="MTSistem",
                 font=('Segoe UI', 22, 'normal'),
                 foreground='#1a1a1a',
                 bg='#fafbfc').pack()

        tk.Label(container, text="Sistema Fiscal",
                 font=('Segoe UI', 10),
                 foreground='#6c757d',
                 bg='#fafbfc').pack(pady=(2, 40))

        # ══════════════════════════════════════════════════════════════════════
        # CARD ELEVADO
        # ══════════════════════════════════════════════════════════════════════
        # Shadow layer (simula elevação)
        shadow = tk.Frame(container, bg='#e9ecef', height=2)
        shadow.pack(fill="x")

        card = tk.Frame(container, bg='white')
        card.pack(fill="both", expand=True)

        card_inner = tk.Frame(card, bg='white')
        card_inner.pack(fill="both", expand=True, padx=32, pady=28)

        # Label sutil
        tk.Label(card_inner, text="Selecione seu usuário",
                 font=('Segoe UI', 11),
                 foreground='#495057',
                 bg='white').pack(anchor="w", pady=(0, 20))

        # Lista de usuários
        usuarios = self.dao.listar_usuarios()

        if not usuarios:
            tk.Label(card_inner, text="Nenhum usuário cadastrado",
                     font=('Segoe UI', 9, 'italic'),
                     foreground='#adb5bd',
                     bg='white').pack(pady=30)
        else:
            for user_id, nome, admin in usuarios:
                self._criar_item_usuario(card_inner, user_id, nome, admin)

        # ══════════════════════════════════════════════════════════════════════
        # FOOTER
        # ══════════════════════════════════════════════════════════════════════
        tk.Label(container,
                 text=f"v{VERSAO_ATUAL} • © 2024 MTSistem",
                 font=('Segoe UI', 8),
                 foreground='#adb5bd',
                 bg='#fafbfc').pack(pady=(20, 0))

    def _criar_item_usuario(self, parent, user_id, nome, admin):
        """Item minimalista de usuário com hover sutil."""
        # Container do item
        item = tk.Frame(parent, bg='white', cursor='hand2')
        item.pack(fill="x", pady=4)

        # Barra lateral (aparece no hover)
        barra = tk.Frame(item, bg='white', width=3)
        barra.pack(side="left", fill="y")

        # Conteúdo
        content = tk.Frame(item, bg='white')
        content.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=10)

        # Nome
        lbl_nome = tk.Label(content, text=nome,
                           font=('Segoe UI', 11),
                           foreground='#212529',
                           bg='white',
                           anchor='w')
        lbl_nome.pack(side="left", fill="x", expand=True)

        # Badge minimalista (se admin)
        if admin:
            badge = tk.Label(content, text="admin",
                            font=('Segoe UI', 8),
                            foreground='#6c757d',
                            bg='#f8f9fa',
                            padx=8, pady=2)
            badge.pack(side="right")

        # Separador inferior
        sep = tk.Frame(parent, bg='#f1f3f5', height=1)
        sep.pack(fill="x")

        # Hover minimalista
        def on_enter(e):
            barra.config(bg=CORES['primary'])
            item.config(bg='#f8f9fa')
            content.config(bg='#f8f9fa')
            lbl_nome.config(bg='#f8f9fa', foreground=CORES['primary'])
            if admin:
                badge.config(bg='#e9ecef')

        def on_leave(e):
            barra.config(bg='white')
            item.config(bg='white')
            content.config(bg='white')
            lbl_nome.config(bg='white', foreground='#212529')
            if admin:
                badge.config(bg='#f8f9fa')

        # Bind
        widgets = [item, content, lbl_nome, barra]
        if admin:
            widgets.append(badge)

        for w in widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", lambda e, i=user_id, n=nome: self.pedir_senha(i, n))

    def pedir_senha(self, usuario_id, nome):
        # Dialog customizado minimalista
        dialog = tk.Toplevel(self.root)
        dialog.title("Autenticação")
        dialog.configure(bg='white')
        dialog.geometry("340x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Centralizar
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 340) // 2
        y = (dialog.winfo_screenheight() - 180) // 2
        dialog.geometry(f"340x180+{x}+{y}")

        container = tk.Frame(dialog, bg='white')
        container.pack(fill="both", expand=True, padx=30, pady=25)

        tk.Label(container, text=f"Senha de {nome}",
                 font=('Segoe UI', 11),
                 foreground='#212529',
                 bg='white').pack(anchor="w", pady=(0, 15))

        # Entry minimalista
        senha_var = tk.StringVar()
        entry = tk.Entry(container, textvariable=senha_var,
                        font=('Segoe UI', 11), show='•',
                        relief='solid', bd=1,
                        highlightthickness=1,
                        highlightbackground='#dee2e6',
                        highlightcolor=CORES['primary'])
        entry.pack(fill="x", ipady=8)
        entry.focus_set()

        # Botões minimalistas
        btn_frame = tk.Frame(container, bg='white')
        btn_frame.pack(fill="x", pady=(20, 0))

        btn_cancelar = tk.Button(btn_frame, text="Cancelar",
                                 font=('Segoe UI', 9),
                                 bg='white', fg='#6c757d',
                                 relief='flat', cursor='hand2',
                                 padx=18, pady=8,
                                 command=dialog.destroy)
        btn_cancelar.pack(side="right", padx=(8, 0))

        def entrar():
            senha = senha_var.get()
            dialog.destroy()

            if not senha:
                return

            auth = self.dao.autenticar(nome, senha)

            if auth is None:
                messagebox.showerror("Erro", "Usuário ou senha inválidos.",
                                    parent=self.root)
                return

            if auth == "BLOQUEADO":
                messagebox.showwarning("Bloqueado",
                                      "Acesso temporariamente bloqueado.\n"
                                      "Contate o administrador.",
                                      parent=self.root)
                return

            usuario_id, is_admin = auth

            from database.sessao import sessao
            from telas.tela_selecao_empresa import TelaSelecaoEmpresa

            sessao.usuario_id = usuario_id
            sessao.usuario_nome = nome
            sessao.is_admin = is_admin

            self.root.destroy()
            root = tk.Tk()
            TelaSelecaoEmpresa(root)
            root.mainloop()

        btn_entrar = tk.Button(btn_frame, text="Entrar",
                              font=('Segoe UI', 9, 'bold'),
                              bg=CORES['primary'], fg='white',
                              relief='flat', cursor='hand2',
                              padx=22, pady=8,
                              command=entrar)
        btn_entrar.pack(side="right")

        entry.bind("<Return>", lambda e: entrar())
        dialog.bind("<Escape>", lambda e: dialog.destroy())