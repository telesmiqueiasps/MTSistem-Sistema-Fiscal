import tkinter as tk
from tkinter import ttk, messagebox
from dao.usuario_dao import UsuarioDAO
from utils.constantes import CORES, MODULOS
from utils.auxiliares import resource_path


class TelaUsuariosAdmin:
    def __init__(self, parent):
        self.dao = UsuarioDAO()
        self.usuario_atual_id = None
        self.vars_permissoes = {}

        self.janela = tk.Toplevel(parent)
        self.janela.title("Usuários e Permissões")
        self.janela.geometry("900x600")
        self.janela.configure(bg=CORES['bg_main'])

        # ÍCONE
        caminho_icone = resource_path("Icones/logo.ico")
        self.janela.iconbitmap(caminho_icone)

        self.centralizar_janela()
        self.criar_interface()
        self.carregar_usuarios()

    def centralizar_janela(self):
        self.janela.update_idletasks()
        width = self.janela.winfo_width()
        height = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() // 2) - (width // 2)
        y = (self.janela.winfo_screenheight() // 2) - (height // 2)
        self.janela.geometry(f"{width}x{height}+{x}+{y}")    

    def criar_interface(self):
        container = ttk.Frame(self.janela, padding=20, style="Main.TFrame")
        container.pack(fill="both", expand=True)

        # ======================
        # LADO ESQUERDO – LISTA
        # ======================
        left = ttk.Frame(container, style="Card.TFrame")
        left.pack(side="left", fill="y", padx=(0, 20))

        ttk.Label(
            left,
            text="Usuários",
            font=('Segoe UI', 14, 'bold'),
            foreground=CORES['primary'],
            background=CORES['bg_card']
        ).pack(anchor="w")

        self.lista = tk.Listbox(left, width=30, height=25)
        self.lista.pack(pady=10)
        self.lista.bind("<<ListboxSelect>>", self.selecionar_usuario)

        ttk.Button(
            left,
            text="Novo Usuário",
            style='Add.TButton',
            command=self.novo_usuario
        ).pack(fill="x", pady=(5, 0))

        ttk.Button(
            left,
            text="Excluir Usuário",
            style='Danger.TButton',
            command=self.excluir_usuario
        ).pack(fill="x", pady=5)

        # ======================
        # LADO DIREITO – FORM
        # ======================
        right = ttk.Frame(container, style="Card.TFrame")
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(
            right,
            text="Dados do Usuário",
            font=('Segoe UI', 14, 'bold'),
            foreground=CORES['primary'],
            background=CORES['bg_card']
        ).pack(anchor="w")

        form = ttk.Frame(right, style="Card.TFrame")
        form.pack(fill="x", pady=10)

        ttk.Label(form, text="Nome", background=CORES['bg_card']).grid(row=0, column=0, sticky="w")
        self.entry_nome = ttk.Entry(form)
        self.entry_nome.grid(row=0, column=1, sticky="ew", padx=10)

        ttk.Label(form, text="Nova senha", background=CORES['bg_card']).grid(row=1, column=0, sticky="w")
        self.entry_senha = ttk.Entry(form, show="*")
        self.entry_senha.grid(row=1, column=1, sticky="ew", padx=10)

        self.var_admin = tk.IntVar()
        ttk.Checkbutton(
            form,
            text="Administrador",
            style="Custom.TCheckbutton",
            variable=self.var_admin
        ).grid(row=2, column=1, sticky="w", pady=5)

        form.columnconfigure(1, weight=1)

        # ======================
        # PERMISSÕES
        # ======================
        ttk.Label(
            right,
            text="Permissões",
            font=('Segoe UI', 12, 'bold'),
            foreground=CORES['primary'],
            background=CORES['bg_card']
        ).pack(anchor="w", pady=(15, 5))

        perms = ttk.Frame(right, style="Card.TFrame")
        perms.pack(anchor="w")

        for modulo, label in MODULOS.items():
            var = tk.IntVar()
            self.vars_permissoes[modulo] = var
            ttk.Checkbutton(
                perms,
                text=label,
                style="Custom.TCheckbutton",
                variable=var
            ).pack(anchor="w", pady=(15, 2))

        ttk.Button(
            right,
            text="Salvar alterações",
            style='Primary.TButton',
            command=self.salvar
        ).pack(pady=20)

    # ======================
    # MÉTODOS
    # ======================
    def carregar_usuarios(self):
        self.lista.delete(0, tk.END)
        self.usuarios = self.dao.listar_usuarios()
        for uid, nome, admin in self.usuarios:
            sufixo = " (Admin)" if admin else ""
            self.lista.insert(tk.END, f"{nome}{sufixo}")

    def selecionar_usuario(self, event):
        idx = self.lista.curselection()
        if not idx:
            return

        self.usuario_atual_id = self.usuarios[idx[0]][0]
        dados = self.dao.buscar_usuario(self.usuario_atual_id)

        self.entry_nome.delete(0, tk.END)
        self.entry_nome.insert(0, dados[1])
        self.var_admin.set(dados[2])

        self.entry_senha.delete(0, tk.END)

        permissoes = self.dao.permissoes_usuario(self.usuario_atual_id)
        for modulo, var in self.vars_permissoes.items():
            var.set(1 if modulo in permissoes else 0)

    def novo_usuario(self):
        self.usuario_atual_id = None
        self.entry_nome.delete(0, tk.END)
        self.entry_senha.delete(0, tk.END)
        self.var_admin.set(0)
        for var in self.vars_permissoes.values():
            var.set(0)
    
    def salvar(self):
        nome = self.entry_nome.get().strip()
        senha = self.entry_senha.get().strip()
        admin = self.var_admin.get()

        if not nome:
            messagebox.showerror("Erro", "Nome é obrigatório")
            return

        if self.usuario_atual_id:
            self.dao.atualizar_usuario(self.usuario_atual_id, nome, admin)

            if senha:
                self.dao.atualizar_senha(self.usuario_atual_id, senha)

            usuario_id = self.usuario_atual_id
        else:
            if not senha:
                messagebox.showerror("Erro", "Senha obrigatória para novo usuário")
                return

            usuario_id = self.dao.criar_usuario(nome, senha, admin)

        permissoes = {
            modulo: var.get()
            for modulo, var in self.vars_permissoes.items()
        }
        self.dao.salvar_permissoes(usuario_id, permissoes)

        self.carregar_usuarios()
        messagebox.showinfo("Sucesso", "Usuário salvo com sucesso")

    def excluir_usuario(self):
        if not self.usuario_atual_id:
            return

        if messagebox.askyesno(
            "Confirmar",
            "Deseja realmente excluir este usuário?"
        ):
            self.dao.excluir_usuario(self.usuario_atual_id)
            self.novo_usuario()
            self.carregar_usuarios()