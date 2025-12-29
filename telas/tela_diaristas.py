import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from dao.diarista_dao import DiaristaDAO
from utils.constantes import CORES
from utils.auxiliares import formatar_cpf, resource_path


class DiaristasEmbed:
    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.var_cpf = tk.StringVar()
        self.dao = DiaristaDAO()
        self.diarista_id = None
        self.criar_interface()
        self.carregar()

    def criar_interface(self):
        # Frame principal
        main_frame = ttk.Frame(self.parent_frame, style='Main.TFrame')
        main_frame.pack(fill="both", expand=True, padx=50, pady=30)

        # Header
        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.pack(fill="x", pady=(0, 30))

        header_container = ttk.Frame(header_frame, style='Main.TFrame')
        header_container.pack(fill="x")

        # Ícone e título
        left_header = ttk.Frame(header_container, style='Main.TFrame')
        left_header.pack(side="left")

        # ÍCONE DO HEADER
        caminho_icone = resource_path("Icones/diarista_azul.png")
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
            text="Cadastro de Diaristas",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")
        
        ttk.Label(
            title_frame,
            text="Gerencie os diaristas utilizados nos lançamentos de diárias",
            font=('Segoe UI', 9),
            background=CORES['bg_main'],
            foreground=CORES['text_light']
        ).pack(anchor="w")
        

        content = ttk.Frame(main_frame, style="Main.TFrame")
        content.pack(fill="both", expand=True)

        # Card
        card = ttk.Frame(content, style="Card.TFrame", padding=30)
        card.pack(fill="both", expand=True)

        body = ttk.Frame(card, style="Card.TFrame")
        body.pack(fill="both", expand=True)

        # Lista
        left = ttk.Frame(body, style="Card.TFrame")
        left.pack(side="left", fill="y", padx=(0, 30))

        # Busca
        ttk.Label(left, text="Buscar", background=CORES['bg_card']).pack(anchor="w")
        self.entry_busca = ttk.Entry(left)
        self.entry_busca.pack(fill="x", pady=(0, 10))
        self.entry_busca.bind("<KeyRelease>", self.filtrar)

        # Tabela
        columns = ("nome", "cpf")
        self.tabela = ttk.Treeview(
            left,
            columns=columns,
            show="headings",
            height=14
        )

        self.tabela.heading("nome", text="Nome")
        self.tabela.heading("cpf", text="CPF")

        self.tabela.column("nome", width=200)
        self.tabela.column("cpf", width=120)

        self.tabela.pack(side="left", fill="y")

        # Scrollbar
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tabela.yview)
        scroll.pack(side="right", fill="y")
        self.tabela.configure(yscrollcommand=scroll.set)

        self.tabela.bind("<<TreeviewSelect>>", self.selecionar)

        ttk.Button(left, text="➕ Novo", style="Add.TButton", command=self.novo)\
            .pack(fill="x", padx=5, pady=(10, 5))

        ttk.Button(left, text="🗑 Excluir", style="Danger.TButton", command=self.excluir)\
            .pack(fill="x", padx=5, pady=(10, 5))


        # Form
        right = ttk.Frame(body, style="Card.TFrame")
        right.pack(side="left", fill="both", expand=True)

        self.entry_nome = self.criar_campo(right, "Nome do diarista")
        ttk.Label(right, text="CPF", background=CORES['bg_card']).pack(anchor="w")

        self.var_cpf = tk.StringVar()
        self.entry_cpf = ttk.Entry(
            right,
            textvariable=self.var_cpf
        )
        self.entry_cpf.pack(fill="x", pady=(0, 15))

        self.var_cpf.trace_add("write", self.on_cpf_change)


        ttk.Button(
            right,
            text="💾 Salvar",
            style="Primary.TButton",
            command=self.salvar
        ).pack(pady=20)


    def on_cpf_change(self, *_):
        entry = self.entry_cpf

        valor_atual = entry.get()
        pos_cursor = entry.index(tk.INSERT)

        numeros_antes = len([c for c in valor_atual[:pos_cursor] if c.isdigit()])

        formatado = formatar_cpf(valor_atual)

        if valor_atual != formatado:
            entry.delete(0, tk.END)
            entry.insert(0, formatado)

            # Reposiciona o cursor corretamente
            nova_pos = 0
            cont_digitos = 0

            for i, c in enumerate(formatado):
                if c.isdigit():
                    cont_digitos += 1
                if cont_digitos >= numeros_antes:
                    nova_pos = i + 1
                    break
            else:
                nova_pos = len(formatado)

            entry.icursor(nova_pos)



    def criar_campo(self, parent, label):
        ttk.Label(parent, text=label, background=CORES['bg_card']).pack(anchor="w")
        entry = ttk.Entry(parent)
        entry.pack(fill="x", pady=(0, 15))
        return entry

    def carregar(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        self.dados = self.dao.listar()

        for d in self.dados:
            self.tabela.insert("", "end", iid=d[0], values=(d[1], d[2]))


    def selecionar(self, _):
        selecionado = self.tabela.selection()
        if not selecionado:
            return

        self.diarista_id = int(selecionado[0])
        dados = self.dao.buscar(self.diarista_id)

        self.entry_nome.delete(0, tk.END)
        self.entry_nome.insert(0, dados[1])

        self.entry_cpf.delete(0, tk.END)
        self.entry_cpf.insert(0, dados[2])


    def filtrar(self, _=None):
        termo = self.entry_busca.get().lower()

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for d in self.dados:
            if termo in d[1].lower() or termo in d[2]:
                self.tabela.insert("", "end", iid=d[0], values=(d[1], d[2]))
    

    def novo(self):
        self.diarista_id = None
        self.entry_nome.delete(0, tk.END)
        self.entry_cpf.delete(0, tk.END)
        self.tabela.selection_remove(self.tabela.selection())

    def salvar(self):
        nome = self.entry_nome.get().strip()
        cpf = self.entry_cpf.get().strip()

        if not nome or not cpf:
            messagebox.showwarning("Atenção", "Preencha todos os campos.")
            return

        existente = self.dao.buscar_por_cpf(cpf)

        # 🔒 CPF já existe
        if existente:
            id_existente, nome_existente = existente

            # Se for edição, permite apenas se for o mesmo registro
            if not self.diarista_id or self.diarista_id != id_existente:
                messagebox.showwarning(
                    "CPF já cadastrado",
                    f"O CPF informado já pertence a:\n\n"
                    f"👤 {nome_existente}\n\n"
                    f"Não é possível cadastrar dois diaristas com o mesmo CPF."
                )
                return

        # 💾 Salvar
        if self.diarista_id:
            self.dao.atualizar(self.diarista_id, nome, cpf)
        else:
            self.dao.salvar(nome, cpf)

        self.carregar()
        self.novo()

        messagebox.showinfo("Sucesso", "Diarista salvo com sucesso.")



    def excluir(self):
        if not self.diarista_id:
            messagebox.showinfo("Atenção", "É necessário selecionar um diarista para excluir.")
            return
        if self.diarista_id and messagebox.askyesno("Confirmar", "Excluir diarista?"):
            self.dao.excluir(self.diarista_id)
            self.novo()
            self.carregar()
