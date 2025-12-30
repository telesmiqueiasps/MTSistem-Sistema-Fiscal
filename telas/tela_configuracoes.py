import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from dao.usuario_dao import UsuarioDAO
from utils.constantes import CORES, VERSAO_ATUAL
from utils.auxiliares import resource_path


class TelaConfiguracoesSistema:
    def __init__(self, parent):
        self.dao = UsuarioDAO()

        self.janela = tk.Toplevel(parent)
        self.janela.title("Configurações do Sistema")
        self.janela.geometry("720x600")
        self.janela.configure(bg=CORES['bg_main'])

        caminho_icone = resource_path("Icones/logo.ico")
        self.janela.iconbitmap(caminho_icone)

        self.centralizar()
        self.criar_interface()

    def centralizar(self):
        self.janela.update_idletasks()
        w = self.janela.winfo_width()
        h = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

    def criar_interface(self):
        container = ttk.Frame(self.janela, padding=30, style="Main.TFrame")
        container.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(container, style='Main.TFrame')
        header_frame.pack(fill="x", pady=(0, 30))

        header_container = ttk.Frame(header_frame, style='Main.TFrame')
        header_container.pack(fill="x")

        # Ícone e título
        left_header = ttk.Frame(header_container, style='Main.TFrame')
        left_header.pack(side="left")

        caminho_icone = resource_path("Icones/config_azul.png")
        img = Image.open(caminho_icone)
        img = img.resize((32, 32), Image.LANCZOS)
        self.icon_header = ImageTk.PhotoImage(img)  # manter referência!


        ttk.Label(
            left_header,
            image=self.icon_header,
            background=CORES['bg_main']
        ).pack(side="left", padx=(0, 15))

        title_frame = ttk.Frame(left_header, style='Main.TFrame')
        title_frame.pack(side="left")

        ttk.Label(
            title_frame,
            text="Configurações do Sistema",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")

    

        # ==================================================
        # CARD – CONTROLE DE ATUALIZAÇÃO
        # ==================================================
        card = ttk.Frame(container, padding=20, style="Card.TFrame")
        card.pack(fill="x")

        ttk.Label(
            card,
            text="Atualização e Controle do Sistema",
            font=('Segoe UI', 14, 'bold'),
            foreground=CORES['primary'],
            background=CORES['bg_card']
        ).pack(anchor="w", pady=(0, 15))

        # -------- Versão atual no servidor --------
        versao_atual = self.dao.get_config("versao_atual", VERSAO_ATUAL)

        ttk.Label(card, text="Versão liberada no servidor", background=CORES['bg_card']).pack(anchor="w")
        self.entry_versao = ttk.Entry(card)
        self.entry_versao.insert(0, versao_atual)
        self.entry_versao.pack(fill="x", pady=(0, 10))

        # -------- Caminho do EXE --------
        exe = self.dao.get_config("exe_atualizacao", "")
        ttk.Label(card, text="Executável de atualização", background=CORES['bg_card']).pack(anchor="w")
        self.entry_exe = ttk.Entry(card)
        self.entry_exe.insert(0, exe)
        self.entry_exe.pack(fill="x", pady=(0, 10))

        # -------- Mensagem --------
        mensagem = self.dao.get_config("mensagem_update", "")
        ttk.Label(card, text="Mensagem para os usuários", background=CORES['bg_card']).pack(anchor="w")
        self.txt_mensagem = tk.Text(card, height=4)
        self.txt_mensagem.insert("1.0", mensagem)
        self.txt_mensagem.pack(fill="x", pady=(0, 10))

        # -------- Flags --------
        liberar = self.dao.get_config("atualizacao_liberada", "NAO")
        bloqueado = self.dao.get_config("sistema_bloqueado", "NAO")

        self.var_liberar = tk.IntVar(value=1 if liberar == "SIM" else 0)
        self.var_bloquear = tk.IntVar(value=1 if bloqueado == "SIM" else 0)

        ttk.Checkbutton(
            card,
            text="Liberar atualização para usuários",
            style="Custom.TCheckbutton",
            variable=self.var_liberar
        ).pack(anchor="w")

        ttk.Checkbutton(
            card,
            text="Bloquear acesso ao sistema (exceto admin)",
            style="Custom.TCheckbutton",
            variable=self.var_bloquear
        ).pack(anchor="w", pady=(5, 15))

        ttk.Button(
            card,
            text="💾 Salvar configurações",
            style="Primary.TButton",
            command=self.salvar
        ).pack(anchor="e")

    def salvar(self):
        self.dao.set_config("versao_atual", self.entry_versao.get().strip())
        self.dao.set_config("exe_atualizacao", self.entry_exe.get().strip())
        self.dao.set_config(
            "mensagem_update",
            self.txt_mensagem.get("1.0", "end").strip()
        )
        self.dao.set_config(
            "atualizacao_liberada",
            "SIM" if self.var_liberar.get() else "NAO"
        )
        self.dao.set_config(
            "sistema_bloqueado",
            "SIM" if self.var_bloquear.get() else "NAO"
        )

        messagebox.showinfo(
            "Sucesso",
            "Configurações salvas com sucesso."
        )