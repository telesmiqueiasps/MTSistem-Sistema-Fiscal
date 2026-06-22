import tkinter as tk
from tkinter import ttk, messagebox
from dao.notas_fiscais_dao import NotasFiscaisDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path
from PIL import Image, ImageTk


def _fmt_brl(v):
    if not v:
        return "R$ 0,00"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class FornecedoresNFEmbed:
    """Sub-aba de Fornecedores/Emitentes dentro do módulo de Notas Fiscais."""

    def __init__(self, parent_frame, on_filtrar_notas=None):
        self.parent_frame = parent_frame
        self.dao = NotasFiscaisDAO()
        self.on_filtrar_notas = on_filtrar_notas
        self._dados = []
        self.criar_interface()
        self.carregar()

    def criar_interface(self):
        main_frame = ttk.Frame(self.parent_frame, style='Main.TFrame')
        main_frame.pack(fill="both", expand=True)

        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.pack(fill="x", pady=(0, 12))

        ttk.Label(header_frame, text="Fornecedores / Emitentes",
                  font=('Segoe UI', 13, 'bold'),
                  background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(side="left")

        ttk.Button(header_frame, text="➕ Novo Fornecedor",
                   style="Primary.TButton",
                   command=self.abrir_form_novo).pack(side="right")

        busca_frame = ttk.Frame(main_frame, style='Main.TFrame')
        busca_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(busca_frame, text="🔍 Buscar:",
                  background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(side="left", padx=(0, 6))

        self.busca_var = tk.StringVar()
        self.busca_var.trace_add("write", lambda *_: self.carregar())
        ttk.Entry(busca_frame, textvariable=self.busca_var, width=34).pack(side="left")

        card = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
        card.pack(fill="both", expand=True)

        self._criar_treeview(card)

        acoes_frame = ttk.Frame(card, style="Card.TFrame")
        acoes_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(acoes_frame, text="✏️ Editar",
                   style="Secondary.TButton",
                   command=self.abrir_form_editar).pack(side="left", padx=(0, 6))

        ttk.Button(acoes_frame, text="🗂️ Ver Notas Fiscais",
                   style="Add.TButton",
                   command=self.filtrar_notas_do_selecionado).pack(side="left", padx=(0, 6))

        ttk.Button(acoes_frame, text="🗑️ Excluir",
                   style="Danger.TButton",
                   command=self.excluir).pack(side="left")

        self.tree.bind("<Double-1>", lambda _e: self.abrir_form_editar())

    def _criar_treeview(self, parent):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "FornecedoresNF.Treeview",
            background="white", foreground=CORES['text_dark'],
            rowheight=32, fieldbackground="white",
            font=('Segoe UI', 9), borderwidth=0
        )
        style.configure(
            "FornecedoresNF.Treeview.Heading",
            background=CORES['primary'], foreground="white",
            font=('Segoe UI', 9, 'bold'), relief="flat", padding=(10, 8)
        )
        style.map("FornecedoresNF.Treeview",
                  background=[("selected", CORES['secondary'])],
                  foreground=[("selected", "white")])

        tree_frame = ttk.Frame(parent, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True)

        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("nome", "cnpj", "qtd", "total", "pendente"),
            show="headings",
            style="FornecedoresNF.Treeview",
            selectmode="browse",
            yscrollcommand=scroll_y.set
        )
        scroll_y.config(command=self.tree.yview)

        self.tree.heading("nome", text="Nome / Razão Social", anchor="w")
        self.tree.heading("cnpj", text="CNPJ / CPF", anchor="w")
        self.tree.heading("qtd", text="NFs", anchor="center")
        self.tree.heading("total", text="Total", anchor="e")
        self.tree.heading("pendente", text="Pendente", anchor="e")

        self.tree.column("nome", width=300, minwidth=180, stretch=True, anchor="w")
        self.tree.column("cnpj", width=150, minwidth=110, stretch=False, anchor="w")
        self.tree.column("qtd", width=60, minwidth=50, stretch=False, anchor="center")
        self.tree.column("total", width=130, minwidth=100, stretch=False, anchor="e")
        self.tree.column("pendente", width=130, minwidth=100, stretch=False, anchor="e")

        self.tree.pack(fill="both", expand=True)

    def carregar(self):
        busca = self.busca_var.get().strip()
        self._dados = self.dao.listar_fornecedores(busca=busca or None)
        self.tree.delete(*self.tree.get_children())
        for f in self._dados:
            self.tree.insert("", "end", iid=str(f["id"]), values=(
                f["nome"], f.get("cnpj_cpf") or "—",
                f.get("qtd_notas") or 0,
                _fmt_brl(f.get("valor_total")),
                _fmt_brl(f.get("valor_pendente")),
            ))

    def _selecionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um fornecedor na lista.")
            return None
        return int(sel[0])

    def abrir_form_novo(self):
        FornecedorFormDialog(self.parent_frame, self.dao, on_save=self.carregar)

    def abrir_form_editar(self):
        fid = self._selecionado()
        if fid is None:
            return
        FornecedorFormDialog(self.parent_frame, self.dao, forn_id=fid, on_save=self.carregar)

    def filtrar_notas_do_selecionado(self):
        fid = self._selecionado()
        if fid is None:
            return
        forn = self.dao.get_fornecedor(fid)
        if forn and self.on_filtrar_notas:
            self.on_filtrar_notas(fid, forn["nome"])

    def excluir(self):
        fid = self._selecionado()
        if fid is None:
            return
        forn = self.dao.get_fornecedor(fid)
        nome = forn["nome"] if forn else "este fornecedor"
        if messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja excluir o fornecedor:\n\n{nome}\n\n"
            "Esta ação não remove as notas fiscais já cadastradas.",
            icon="warning"
        ):
            self.dao.excluir_fornecedor(fid)
            self.carregar()


class FornecedorFormDialog:
    """Janela modal para criar/editar fornecedor."""

    def __init__(self, parent, dao, forn_id=None, on_save=None):
        self.dao = dao
        self.forn_id = forn_id
        self.on_save = on_save
        self.forn = dao.get_fornecedor(forn_id) if forn_id else None
        self.fields = {}

        self.janela = tk.Toplevel(parent)
        titulo = "Editar Fornecedor" if forn_id else "Novo Fornecedor"
        self.janela.title(titulo)
        self.janela.geometry("480x460")
        self.janela.configure(bg=CORES['bg_main'])
        self.janela.resizable(False, False)
        self.janela.grab_set()

        try:
            self.janela.iconbitmap(resource_path("Icones/logo.ico"))
        except Exception:
            pass

        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() - 480) // 2
        y = (self.janela.winfo_screenheight() - 460) // 2
        self.janela.geometry(f"480x460+{x}+{y}")

        self._build()
        if self.forn:
            self._populate()

    def _build(self):
        container = ttk.Frame(self.janela, padding=22, style="Main.TFrame")
        container.pack(fill="both", expand=True)

        ttk.Label(container,
                  text="Editar Fornecedor" if self.forn_id else "Novo Fornecedor",
                  font=('Segoe UI', 14, 'bold'),
                  background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(anchor="w", pady=(0, 14))

        self._campo(container, "nome", "Nome / Razão Social *")
        self._campo(container, "cnpj_cpf", "CNPJ / CPF")
        self._campo(container, "email", "E-mail")
        self._campo(container, "telefone", "Telefone")
        self._campo(container, "observacoes", "Observações", multiline=True, height=4)

        btns = ttk.Frame(container, style="Main.TFrame")
        btns.pack(fill="x", pady=(16, 0))

        ttk.Button(btns, text="💾 Salvar", style="Primary.TButton",
                   command=self._save).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton",
                   command=self.janela.destroy).pack(side="left")

        self.janela.bind("<Escape>", lambda _e: self.janela.destroy())

    def _campo(self, parent, key, label, multiline=False, height=3):
        frame = ttk.Frame(parent, style="Main.TFrame")
        frame.pack(fill="x", pady=(0, 10))
        ttk.Label(frame, text=label, background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(anchor="w")
        if multiline:
            widget = tk.Text(frame, height=height, font=('Segoe UI', 10))
            widget.pack(fill="x", pady=(4, 0))
        else:
            widget = ttk.Entry(frame)
            widget.pack(fill="x", pady=(4, 0))
        self.fields[key] = widget

    def _get(self, key):
        w = self.fields.get(key)
        if not w:
            return ""
        if isinstance(w, tk.Text):
            return w.get("1.0", "end").strip()
        return w.get().strip()

    def _populate(self):
        for key in ["nome", "cnpj_cpf", "email", "telefone", "observacoes"]:
            val = self.forn.get(key) or ""
            w = self.fields.get(key)
            if not w or not val:
                continue
            if isinstance(w, tk.Text):
                w.insert("1.0", val)
            else:
                w.insert(0, val)

    def _save(self):
        nome = self._get("nome")
        if not nome:
            messagebox.showerror("Campo obrigatório", "Informe o nome / razão social.",
                                 parent=self.janela)
            return

        dados = {
            "nome": nome,
            "cnpj_cpf": self._get("cnpj_cpf"),
            "email": self._get("email"),
            "telefone": self._get("telefone"),
            "observacoes": self._get("observacoes"),
        }

        if self.forn_id:
            resultado = self.dao.atualizar_fornecedor(self.forn_id, dados)
            if resultado == "já_existe":
                messagebox.showerror("Duplicata",
                                     "Já existe um fornecedor com este nome e CNPJ/CPF.",
                                     parent=self.janela)
                return
            messagebox.showinfo("Sucesso", "Fornecedor atualizado!", parent=self.janela)
        else:
            _novo_id, resultado = self.dao.inserir_fornecedor(dados)
            if resultado == "já_existe":
                messagebox.showerror(
                    "Duplicata",
                    f"Fornecedor com este nome e CNPJ/CPF já está cadastrado.\n\n"
                    f"Nome: {nome}\nCNPJ/CPF: {dados['cnpj_cpf'] or '—'}",
                    parent=self.janela
                )
                return
            messagebox.showinfo("Sucesso", "Fornecedor cadastrado!", parent=self.janela)

        if self.on_save:
            self.on_save()
        self.janela.destroy()
