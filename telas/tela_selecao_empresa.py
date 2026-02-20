import tkinter as tk
from tkinter import messagebox
from dao.usuario_dao import UsuarioDAO
from database.sessao import sessao
from database.empresa_conexao import conectar_empresa
import os
from utils.auxiliares import resource_path
from utils.constantes import CORES, VERSAO_ATUAL


class TelaSelecaoEmpresa:
    def __init__(self, root):
        self.root = root
        self.dao = UsuarioDAO()

        self.root.title("Selecionar Empresa")
        self.root.configure(bg='#fafbfc')

        largura = 540
        altura = 580
        self.root.geometry(f"{largura}x{altura}")
        self.root.resizable(False, False)

        try:
            caminho_icone = resource_path("Icones/logo.ico")
            self.root.iconbitmap(caminho_icone)
        except Exception:
            pass

        self.centralizar_janela()
        self.criar_interface()

    def centralizar_janela(self):
        self.root.update_idletasks()
        w, h = 540, 580
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def criar_interface(self):
        container = tk.Frame(self.root, bg='#fafbfc')
        container.pack(fill="both", expand=True, padx=45, pady=45)

        # ══════════════════════════════════════════════════════════════════════
        # HEADER CLEAN
        # ══════════════════════════════════════════════════════════════════════
        tk.Label(container, text=f"Olá, {sessao.usuario_nome}",
                 font=('Segoe UI', 18, 'normal'),
                 foreground='#1a1a1a',
                 bg='#fafbfc').pack(anchor="w")

        tk.Label(container, text="Escolha uma empresa para continuar",
                 font=('Segoe UI', 10),
                 foreground='#6c757d',
                 bg='#fafbfc').pack(anchor="w", pady=(4, 35))

        # ══════════════════════════════════════════════════════════════════════
        # CARD ELEVADO
        # ══════════════════════════════════════════════════════════════════════
        shadow = tk.Frame(container, bg='#e9ecef', height=2)
        shadow.pack(fill="x")

        card = tk.Frame(container, bg='white')
        card.pack(fill="both", expand=True)

        card_inner = tk.Frame(card, bg='white')
        card_inner.pack(fill="both", expand=True, padx=28, pady=24)

        # Grid de empresas
        empresas = self.dao.empresas_do_usuario(sessao.usuario_id)

        if not empresas:
            empty_frame = tk.Frame(card_inner, bg='white')
            empty_frame.pack(expand=True)

            tk.Label(empty_frame, text="⚠",
                     font=('Segoe UI', 32),
                     foreground='#dee2e6',
                     bg='white').pack()

            tk.Label(empty_frame, text="Nenhuma empresa disponível",
                     font=('Segoe UI', 11),
                     foreground='#adb5bd',
                     bg='white').pack(pady=(10, 5))

            tk.Label(empty_frame, text="Contate o administrador para solicitar acesso",
                     font=('Segoe UI', 9),
                     foreground='#ced4da',
                     bg='white').pack()
        else:
            # Layout em grid 2 colunas se mais de 2 empresas, senão lista vertical
            if len(empresas) > 2:
                self._criar_grid_empresas(card_inner, empresas)
            else:
                self._criar_lista_empresas(card_inner, empresas)

        # ══════════════════════════════════════════════════════════════════════
        # FOOTER
        # ══════════════════════════════════════════════════════════════════════
        footer = tk.Frame(container, bg='#fafbfc')
        footer.pack(fill="x", pady=(20, 0))

        # Link minimalista para voltar
        link = tk.Label(footer, text="← Voltar",
                       font=('Segoe UI', 9),
                       foreground='#6c757d',
                       bg='#fafbfc',
                       cursor='hand2')
        link.pack(side="left")
        link.bind("<Enter>", lambda e: link.config(foreground=CORES['primary']))
        link.bind("<Leave>", lambda e: link.config(foreground='#6c757d'))
        link.bind("<Button-1>", lambda e: self.voltar_login())

        tk.Label(footer, text=f"v{VERSAO_ATUAL}",
                 font=('Segoe UI', 8),
                 foreground='#adb5bd',
                 bg='#fafbfc').pack(side="right")

    def _criar_lista_empresas(self, parent, empresas):
        """Lista vertical para poucas empresas."""
        for empresa_id, nome in empresas:
            self._criar_card_empresa_lista(parent, empresa_id, nome)

    def _criar_grid_empresas(self, parent, empresas):
        """Grid 2 colunas para múltiplas empresas."""
        grid = tk.Frame(parent, bg='white')
        grid.pack(fill="both", expand=True)

        for idx, (empresa_id, nome) in enumerate(empresas):
            row = idx // 2
            col = idx % 2
            self._criar_card_empresa_grid(grid, empresa_id, nome, row, col)

    def _criar_card_empresa_lista(self, parent, empresa_id, nome):
        """Card horizontal minimalista."""
        item = tk.Frame(parent, bg='white', cursor='hand2')
        item.pack(fill="x", pady=5)

        # Barra lateral
        barra = tk.Frame(item, bg='white', width=3)
        barra.pack(side="left", fill="y")

        # Conteúdo
        content = tk.Frame(item, bg='white')
        content.pack(side="left", fill="both", expand=True,
                    padx=(12, 0), pady=14)

        # Ícone sutil
        tk.Label(content, text="■",
                font=('Segoe UI', 8),
                foreground='#dee2e6',
                bg='white').pack(side="left", padx=(0, 10))

        # Nome
        lbl_nome = tk.Label(content, text=nome,
                           font=('Segoe UI', 11),
                           foreground='#212529',
                           bg='white',
                           anchor='w')
        lbl_nome.pack(side="left", fill="x", expand=True)

        # ID sutil
        lbl_id = tk.Label(content, text=f"#{empresa_id}",
                         font=('Segoe UI', 9),
                         foreground='#adb5bd',
                         bg='white')
        lbl_id.pack(side="right")

        sep = tk.Frame(parent, bg='#f1f3f5', height=1)
        sep.pack(fill="x")

        # Hover
        def on_enter(e):
            barra.config(bg=CORES['primary'])
            item.config(bg='#f8f9fa')
            content.config(bg='#f8f9fa')
            lbl_nome.config(bg='#f8f9fa', foreground=CORES['primary'])
            lbl_id.config(bg='#f8f9fa')

        def on_leave(e):
            barra.config(bg='white')
            item.config(bg='white')
            content.config(bg='white')
            lbl_nome.config(bg='white', foreground='#212529')
            lbl_id.config(bg='white')

        for w in [item, content, lbl_nome, lbl_id, barra]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>",
                  lambda e, i=empresa_id, n=nome: self.selecionar(i, n))

    def _criar_card_empresa_grid(self, parent, empresa_id, nome, row, col):
        """Card compacto para grid."""
        card = tk.Frame(parent, bg='#f8f9fa',
                       cursor='hand2',
                       highlightthickness=1,
                       highlightbackground='#dee2e6')
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(col, weight=1)

        inner = tk.Frame(card, bg='#f8f9fa')
        inner.pack(fill="both", expand=True, padx=18, pady=18)

        # Ícone
        tk.Label(inner, text="■",
                font=('Segoe UI', 14),
                foreground='#ced4da',
                bg='#f8f9fa').pack(pady=(0, 10))

        # Nome
        lbl_nome = tk.Label(inner, text=nome,
                           font=('Segoe UI', 10, 'bold'),
                           foreground='#212529',
                           bg='#f8f9fa',
                           wraplength=140)
        lbl_nome.pack()

        # ID
        lbl_id = tk.Label(inner, text=f"ID {empresa_id}",
                         font=('Segoe UI', 8),
                         foreground='#adb5bd',
                         bg='#f8f9fa')
        lbl_id.pack(pady=(6, 0))

        # Hover
        def on_enter(e):
            card.config(bg='white', highlightbackground=CORES['primary'])
            inner.config(bg='white')
            lbl_nome.config(bg='white', foreground=CORES['primary'])
            lbl_id.config(bg='white')

        def on_leave(e):
            card.config(bg='#f8f9fa', highlightbackground='#dee2e6')
            inner.config(bg='#f8f9fa')
            lbl_nome.config(bg='#f8f9fa', foreground='#212529')
            lbl_id.config(bg='#f8f9fa')

        for w in [card, inner, lbl_nome, lbl_id]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>",
                  lambda e, i=empresa_id, n=nome: self.selecionar(i, n))

    def selecionar(self, empresa_id, nome):
        db_path = os.path.join(
            r"T:\MTSistem\db\empresas",
            f"{empresa_id}.db"
        )

        if not os.path.exists(db_path):
            messagebox.showerror(
                "Erro",
                f"Banco de dados não encontrado:\n{db_path}",
                parent=self.root
            )
            return

        try:
            sessao.empresa_id = empresa_id
            sessao.empresa_nome = nome
            sessao.db_empresa_path = db_path

            conectar_empresa(db_path)

            self.root.destroy()

            from telas.tela_inicial import SistemaFiscal
            root = tk.Tk()
            SistemaFiscal(root)
            root.mainloop()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar:\n{str(e)}",
                                parent=self.root)

    def voltar_login(self):
        from database.sessao import sessao
        sessao.usuario_id = None
        sessao.usuario_nome = None
        sessao.is_admin = False

        self.root.destroy()

        from telas.tela_login import TelaLogin
        root = tk.Tk()
        TelaLogin(root)
        root.mainloop()