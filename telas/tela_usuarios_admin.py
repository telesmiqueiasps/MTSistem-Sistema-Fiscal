import tkinter as tk
from tkinter import ttk, messagebox
from dao.usuario_dao import UsuarioDAO
from database.sessao import sessao
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

        filtro_frame = ttk.Frame(left, style="Card.TFrame")
        filtro_frame.pack(fill="x", pady=(6, 0))

        self.filtro_var = tk.StringVar(value="todos")
        for texto, valor in [("Todos", "todos"), ("Ativos", "ativos"), ("Inativos", "inativos")]:
            ttk.Radiobutton(
                filtro_frame, text=texto, variable=self.filtro_var, value=valor,
                command=self.carregar_usuarios
            ).pack(side="left", padx=(0, 6))

        self.lista = tk.Listbox(left, width=30, height=23)
        self.lista.pack(pady=10)
        self.lista.bind("<<ListboxSelect>>", self.selecionar_usuario)

        ttk.Button(
            left,
            text="➕ Novo Usuário",
            style='Add.TButton',
            command=self.novo_usuario
        ).pack(fill="x", pady=(5, 0))

        self.btn_status = ttk.Button(
            left,
            text="🔒 Desativar Usuário",
            style='Warning.TButton',
            command=self.alternar_status
        )
        self.btn_status.pack(fill="x", pady=5)

        ttk.Button(
            left,
            text="🗑 Excluir Usuário",
            style='Danger.TButton',
            command=self.excluir_usuario
        ).pack(fill="x")

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
        ).pack(anchor="w", pady=(20, 10))

        perms_container = ttk.Frame(right, style="Card.TFrame")
        perms_container.pack(fill="x", pady=(0, 10))

        # Criar 3 colunas
        col1 = ttk.Frame(perms_container, style="Card.TFrame")
        col2 = ttk.Frame(perms_container, style="Card.TFrame")
        col3 = ttk.Frame(perms_container, style="Card.TFrame")

        col1.pack(side="left", fill="both", expand=True, padx=(0, 20))
        col2.pack(side="left", fill="both", expand=True, padx=(0, 20))
        col3.pack(side="left", fill="both", expand=True)

        # Lista de módulos (assumindo que MODULOS é um dict como: {"abrir_extrator": "Extrator TXT → Excel", ...})
        modulos_list = list(MODULOS.items())
        total = len(modulos_list)
        por_coluna = (total + 2) // 3  # Distribui igualmente (arredonda pra cima)

        # Coluna 1
        for i in range(0, min(por_coluna, total)):
            modulo, label = modulos_list[i]
            var = tk.IntVar()
            self.vars_permissoes[modulo] = var
            ttk.Checkbutton(
                col1,
                text=label,
                style="Custom.TCheckbutton",
                variable=var
            ).pack(anchor="w", pady=4)

        # Coluna 2
        for i in range(por_coluna, min(por_coluna * 2, total)):
            modulo, label = modulos_list[i]
            var = tk.IntVar()
            self.vars_permissoes[modulo] = var
            ttk.Checkbutton(
                col2,
                text=label,
                style="Custom.TCheckbutton",
                variable=var
            ).pack(anchor="w", pady=4)

        # Coluna 3
        for i in range(por_coluna * 2, total):
            modulo, label = modulos_list[i]
            var = tk.IntVar()
            self.vars_permissoes[modulo] = var
            ttk.Checkbutton(
                col3,
                text=label,
                style="Custom.TCheckbutton",
                variable=var
            ).pack(anchor="w", pady=4)

        # Botão salvar
        ttk.Button(
            right,
            text="💾 Salvar alterações",
            style='Primary.TButton',
            command=self.salvar
        ).pack(pady=20)

    # ======================
    # MÉTODOS
    # ======================
    def carregar_usuarios(self):
        self.lista.delete(0, tk.END)
        todos = self.dao.listar_usuarios()
        filtro = self.filtro_var.get()
        if filtro == "ativos":
            self.usuarios = [u for u in todos if u[3]]
        elif filtro == "inativos":
            self.usuarios = [u for u in todos if not u[3]]
        else:
            self.usuarios = todos

        for uid, nome, admin, is_active in self.usuarios:
            sufixo_admin = " (Admin)" if admin else ""
            sufixo_status = "" if is_active else "  [Inativo]"
            self.lista.insert(tk.END, f"{nome}{sufixo_admin}{sufixo_status}")

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

        self._atualizar_botao_status(dados[3])

    def _atualizar_botao_status(self, is_active):
        if is_active:
            self.btn_status.configure(text="🔒 Desativar Usuário", style="Warning.TButton")
        else:
            self.btn_status.configure(text="✅ Ativar Usuário", style="Add.TButton")

    def novo_usuario(self):
        self.usuario_atual_id = None
        self.entry_nome.delete(0, tk.END)
        self.entry_senha.delete(0, tk.END)
        self.var_admin.set(0)
        for var in self.vars_permissoes.values():
            var.set(0)
        self._atualizar_botao_status(True)
    
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

    def alternar_status(self):
        if not self.usuario_atual_id:
            messagebox.showwarning("Atenção", "Selecione um usuário na lista.")
            return

        dados = self.dao.buscar_usuario(self.usuario_atual_id)
        nome, is_active = dados[1], dados[3]

        if is_active:
            if self.usuario_atual_id == sessao.usuario_id and not messagebox.askyesno(
                "Atenção",
                "Você está desativando o seu próprio usuário e perderá "
                "acesso ao sistema no próximo login. Deseja continuar?"
            ):
                return
            if not messagebox.askyesno(
                "Confirmar desativação",
                f"Desativar o usuário '{nome}'?\n\n"
                "Ele não conseguirá mais fazer login até ser reativado."
            ):
                return
            self.dao.desativar_usuario(self.usuario_atual_id)
            messagebox.showinfo("Sucesso", "Usuário desativado.")
        else:
            if not messagebox.askyesno("Confirmar reativação", f"Reativar o usuário '{nome}'?"):
                return
            self.dao.ativar_usuario(self.usuario_atual_id)
            messagebox.showinfo("Sucesso", "Usuário reativado.")

        self.carregar_usuarios()
        self._atualizar_botao_status(not is_active)