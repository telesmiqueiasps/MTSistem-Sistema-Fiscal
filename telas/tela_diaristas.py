import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from tkcalendar import DateEntry
from PIL import Image, ImageTk
from dao.diarista_dao import DiaristaDAO
from utils.constantes import CORES
from utils.auxiliares import formatar_cpf, resource_path


class DiaristasEmbed:
    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.dao = DiaristaDAO()
        self.diarista_id = None
        self._dados_completos = []
        self.criar_interface()
        self.carregar()

    # ─────────────────────────────────────────────────────────────────────────
    # INTERFACE
    # ─────────────────────────────────────────────────────────────────────────

    def criar_interface(self):
        main_frame = ttk.Frame(self.parent_frame, style='Main.TFrame')
        main_frame.pack(fill="both", expand=True, padx=50, pady=30)

        # ── Header ────────────────────────────────────────────────────────────
        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.pack(fill="x", pady=(0, 20))

        left_header = ttk.Frame(header_frame, style='Main.TFrame')
        left_header.pack(side="left")

        try:
            img = Image.open(resource_path("Icones/diarista_azul.png")).resize((32, 32), Image.LANCZOS)
            self.icon_header = ImageTk.PhotoImage(img)
            ttk.Label(left_header, image=self.icon_header,
                      background=CORES['bg_main']).pack(side="left", padx=(0, 15))
        except Exception:
            pass

        title_frame = ttk.Frame(left_header, style='Main.TFrame')
        title_frame.pack(side="left")

        ttk.Label(title_frame, text="Cadastro de Diaristas",
                  font=('Segoe UI', 18, 'bold'),
                  background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(anchor="w")

        ttk.Label(title_frame,
                  text="Gerencie os diaristas utilizados nos lançamentos de diárias",
                  font=('Segoe UI', 9),
                  background=CORES['bg_main'],
                  foreground=CORES['text_light']).pack(anchor="w")

        right_header = ttk.Frame(header_frame, style='Main.TFrame')
        right_header.pack(side="right")

        ttk.Button(right_header, text="➕ Novo Diarista",
                   style="Primary.TButton",
                   command=self.abrir_form_novo).pack(side="left", padx=5)

        # ── Card principal ────────────────────────────────────────────────────
        card = ttk.Frame(main_frame, style="Card.TFrame", padding=25)
        card.pack(fill="both", expand=True)

        # ── Barra de filtros ──────────────────────────────────────────────────
        filtros_frame = ttk.Frame(card, style="Card.TFrame")
        filtros_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(filtros_frame, text="Exibir:",
                  font=('Segoe UI', 10),
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(side="left", padx=(0, 8))

        self.var_filtro_status = tk.StringVar(value="ativos")
        for texto, valor in [("Ativos", "ativos"), ("Inativos", "inativos"), ("Todos", "todos")]:
            ttk.Radiobutton(filtros_frame, text=texto,
                            variable=self.var_filtro_status, value=valor,
                            command=self.carregar).pack(side="left", padx=4)

        ttk.Separator(filtros_frame, orient="vertical").pack(
            side="left", fill="y", padx=15, pady=2)

        ttk.Label(filtros_frame, text="🔍 Nome:",
                  font=('Segoe UI', 10),
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(side="left", padx=(0, 5))

        self.busca_var = tk.StringVar()
        self.busca_var.trace_add("write", lambda *_: self.filtrar())
        ttk.Entry(filtros_frame, textvariable=self.busca_var, width=24).pack(side="left", padx=(0, 15))

        ttk.Label(filtros_frame, text="CPF:",
                  font=('Segoe UI', 10),
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(side="left", padx=(0, 5))

        self.busca_cpf_var = tk.StringVar()
        self.busca_cpf_var.trace_add("write", lambda *_: self.filtrar())
        ttk.Entry(filtros_frame, textvariable=self.busca_cpf_var, width=16).pack(side="left")

        ttk.Button(filtros_frame, text="✖ Limpar",
                   style="Secondary.TButton",
                   command=self.limpar_filtros).pack(side="right")

        # ── Contador ──────────────────────────────────────────────────────────
        self.label_total = ttk.Label(card, text="",
                                     font=('Segoe UI', 9),
                                     background=CORES['bg_card'],
                                     foreground=CORES['text_light'])
        self.label_total.pack(anchor="w", pady=(0, 8))

        # ── Treeview ──────────────────────────────────────────────────────────
        self._criar_treeview(card)

        # ── Barra de ações ────────────────────────────────────────────────────
        acoes_frame = ttk.Frame(card, style="Card.TFrame")
        acoes_frame.pack(fill="x", pady=(12, 0))


        ttk.Button(acoes_frame, text="🔒 Inativar",
                   style="Warning.TButton",
                   command=self.inativar).pack(side="left", padx=(0, 6))

        ttk.Button(acoes_frame, text="✅ Reativar",
                   style="Add.TButton",
                   command=self.reativar).pack(side="left", padx=(0, 6))

        ttk.Button(acoes_frame, text="🗑️ Excluir",
                   style="Danger.TButton",
                   command=self.excluir).pack(side="left")

        self.tree.bind("<Double-1>", lambda _e: self.abrir_form_editar())

    # ─────────────────────────────────────────────────────────────────────────

    def _criar_treeview(self, parent):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure(
            "Diaristas.Treeview",
            background="white", foreground=CORES['text_dark'],
            rowheight=32, fieldbackground="white",
            font=('Segoe UI', 9), borderwidth=0
        )
        style.configure(
            "Diaristas.Treeview.Heading",
            background=CORES['primary'], foreground="white",
            font=('Segoe UI', 9, 'bold'), relief="flat", padding=(10, 8)
        )
        style.map("Diaristas.Treeview",
                  background=[("selected", CORES['secondary'])],
                  foreground=[("selected", "white")])
        style.map("Diaristas.Treeview.Heading",
                  background=[("active", CORES['primary'])])

        tree_frame = ttk.Frame(parent, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True)

        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("nome", "cpf", "admissao", "status"),
            show="headings",
            style="Diaristas.Treeview",
            selectmode="browse",
            yscrollcommand=scroll_y.set
        )
        scroll_y.config(command=self.tree.yview)

        self.tree.heading("nome",     text="Nome",       anchor="w")
        self.tree.heading("cpf",      text="CPF",        anchor="w")
        self.tree.heading("admissao", text="Admissão",   anchor="w")
        self.tree.heading("status",   text="Status",     anchor="w")

        self.tree.column("nome",     width=300, minwidth=180, stretch=True,  anchor="w")
        self.tree.column("cpf",      width=150, minwidth=110, stretch=False, anchor="w")
        self.tree.column("admissao", width=120, minwidth=90,  stretch=False, anchor="w")
        self.tree.column("status",   width=110, minwidth=80,  stretch=False, anchor="w")

        self.tree.tag_configure("ativo",   background="#f8f9fa")
        self.tree.tag_configure("inativo", background="white",
                                foreground=CORES.get('text_light', '#888888'))

        self.tree.pack(fill="both", expand=True)

    # ─────────────────────────────────────────────────────────────────────────
    # CARREGAMENTO / FILTRAGEM
    # ─────────────────────────────────────────────────────────────────────────

    def carregar(self):
        filtro = self.var_filtro_status.get()
        todos  = self.dao.listar(apenas_ativos=False)

        if filtro == "ativos":
            self._dados_completos = [d for d in todos if d[3] == 1]
        elif filtro == "inativos":
            self._dados_completos = [d for d in todos if d[3] == 0]
        else:
            self._dados_completos = todos

        self.filtrar()

    def filtrar(self):
        termo_nome = self.busca_var.get().strip().lower()
        termo_cpf  = self.busca_cpf_var.get().strip()

        resultado = [
            d for d in self._dados_completos
            if (not termo_nome or termo_nome in d[1].lower())
            and (not termo_cpf  or termo_cpf  in d[2])
        ]
        self._popular_tree(resultado)

    def _popular_tree(self, dados):
        self.tree.delete(*self.tree.get_children())

        for d in dados:
            # d = (id, nome, cpf, ativo, data_admissao)
            ativo      = d[3]
            admissao   = self._fmt_data(d[4]) if len(d) > 4 and d[4] else "—"
            status_txt = "✅ Ativo" if ativo else "🔒 Inativo"
            tag        = "ativo" if ativo else "inativo"

            self.tree.insert("", "end", iid=str(d[0]),
                             values=(d[1], d[2], admissao, status_txt),
                             tags=(tag,))

        total = len(dados)
        self.label_total.config(
            text=f"{total} diarista{'s' if total != 1 else ''} "
                 f"encontrado{'s' if total != 1 else ''}"
        )

    def limpar_filtros(self):
        self.var_filtro_status.set("ativos")
        self.busca_var.set("")
        self.busca_cpf_var.set("")
        self.carregar()

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _fmt_data(self, data_iso: str) -> str:
        try:
            return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return data_iso or "—"

    def _diarista_selecionado(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um diarista na lista.")
            return None
        return int(sel[0])

    # ─────────────────────────────────────────────────────────────────────────
    # FORMULÁRIO MODAL
    # ─────────────────────────────────────────────────────────────────────────

    def _abrir_form(self, titulo: str, dados=None):
        """Modal de criação/edição. dados = tupla do DAO ou None para novo."""
        janela = tk.Toplevel(self.parent_frame)
        janela.title(titulo)
        janela.geometry("420x300")
        janela.configure(bg=CORES['bg_main'])
        janela.resizable(False, False)
        janela.grab_set()

        try:
            janela.iconbitmap(resource_path("Icones/logo.ico"))
        except Exception:
            pass

        janela.update_idletasks()
        x = (janela.winfo_screenwidth()  - 420) // 2
        y = (janela.winfo_screenheight() - 300) // 2
        janela.geometry(f"420x300+{x}+{y}")

        frame = tk.Frame(janela, bg=CORES['bg_card'])
        frame.pack(fill="both", expand=True, padx=25, pady=25)

        # Nome
        tk.Label(frame, text="Nome do diarista", font=('Segoe UI', 10),
                 bg=CORES['bg_card'], fg=CORES['text_dark']).pack(anchor="w")
        entry_nome = ttk.Entry(frame, font=('Segoe UI', 11))
        entry_nome.pack(fill="x", pady=(2, 15))

        # CPF
        tk.Label(frame, text="CPF", font=('Segoe UI', 10),
                 bg=CORES['bg_card'], fg=CORES['text_dark']).pack(anchor="w")
        var_cpf   = tk.StringVar()
        entry_cpf = ttk.Entry(frame, textvariable=var_cpf, font=('Segoe UI', 11))
        entry_cpf.pack(fill="x", pady=(2, 15))

        def on_cpf(*_):
            cur  = entry_cpf.get()
            pos  = entry_cpf.index(tk.INSERT)
            nd_b = len([c for c in cur[:pos] if c.isdigit()])
            fmt  = formatar_cpf(cur)
            if cur != fmt:
                entry_cpf.delete(0, tk.END)
                entry_cpf.insert(0, fmt)
                nova = nd = 0
                for i, c in enumerate(fmt):
                    if c.isdigit():
                        nd += 1
                    if nd >= nd_b:
                        nova = i + 1
                        break
                else:
                    nova = len(fmt)
                entry_cpf.icursor(nova)
        var_cpf.trace_add("write", on_cpf)

        # Data de admissão
        tk.Label(frame, text="Data de Admissão", font=('Segoe UI', 10),
                 bg=CORES['bg_card'], fg=CORES['text_dark']).pack(anchor="w")
        date_admissao = DateEntry(
            frame, font=('Segoe UI', 11), width=18,
            background=CORES['primary'], foreground='white',
            borderwidth=1, date_pattern='dd/mm/yyyy', locale='pt_BR'
        )
        date_admissao.pack(anchor="w", pady=(2, 20))

        # Preenche campos na edição
        if dados:
            entry_nome.insert(0, dados[1])
            var_cpf.set(dados[2])
            if len(dados) > 4 and dados[4]:
                try:
                    dt = datetime.strptime(dados[4], "%Y-%m-%d").date()
                    date_admissao.set_date(dt)
                except Exception:
                    pass

        entry_nome.focus()

        # Botões
        btn_frame = tk.Frame(frame, bg=CORES['bg_card'])
        btn_frame.pack(anchor="center")

        def salvar():
            nome             = entry_nome.get().strip()
            cpf              = entry_cpf.get().strip()
            data_admissao_iso = date_admissao.get_date().strftime("%Y-%m-%d")

            if not nome or not cpf:
                messagebox.showwarning("Atenção", "Preencha nome e CPF.", parent=janela)
                return

            existente = self.dao.buscar_por_cpf(cpf)
            if existente:
                id_ex, nome_ex = existente
                id_atual = dados[0] if dados else None
                if not id_atual or id_atual != id_ex:
                    messagebox.showwarning(
                        "CPF já cadastrado",
                        f"O CPF informado já pertence a:\n\n👤 {nome_ex}\n\n"
                        "Não é possível cadastrar dois diaristas com o mesmo CPF.",
                        parent=janela
                    )
                    return

            if dados:
                self.dao.atualizar(dados[0], nome, cpf, data_admissao_iso)
            else:
                self.dao.salvar(nome, cpf, data_admissao_iso)

            messagebox.showinfo("Sucesso", "Diarista salvo com sucesso.", parent=janela)
            janela.destroy()
            self.carregar()

        tk.Button(btn_frame, text="Cancelar",
                  font=('Segoe UI', 10), bg=CORES['text_light'], fg='white',
                  relief='flat', cursor='hand2', padx=20, pady=8,
                  command=janela.destroy).pack(side="left", padx=5)

        tk.Button(btn_frame, text="💾 Salvar",
                  font=('Segoe UI', 10, 'bold'), bg=CORES['success'], fg='white',
                  relief='flat', cursor='hand2', padx=20, pady=8,
                  command=salvar).pack(side="left", padx=5)

        janela.bind("<Return>", lambda _: salvar())
        janela.bind("<Escape>", lambda _: janela.destroy())

    def abrir_form_novo(self):
        self._abrir_form("Novo Diarista")

    def abrir_form_editar(self):
        pid = self._diarista_selecionado()
        if pid is None:
            return
        dados = self.dao.buscar(pid)
        if not dados:
            return
        self._abrir_form("Editar Diarista", dados)

    # ─────────────────────────────────────────────────────────────────────────
    # AÇÕES
    # ─────────────────────────────────────────────────────────────────────────

    def inativar(self):
        pid = self._diarista_selecionado()
        if pid is None:
            return
        dados = self.dao.buscar(pid)
        if dados[3] == 0:
            messagebox.showinfo("Atenção", "Este diarista já está inativo.")
            return
        if messagebox.askyesno(
            "Confirmar Inativação",
            f"Deseja inativar '{dados[1]}'?\n\n"
            "Ele não aparecerá nos lançamentos, mas o histórico é preservado."
        ):
            if self.dao.inativar(pid, date.today().strftime("%Y-%m-%d")):
                messagebox.showinfo("Sucesso", "Diarista inativado com sucesso.")
                self.carregar()
            else:
                messagebox.showerror("Erro", "Erro ao inativar diarista.")

    def reativar(self):
        pid = self._diarista_selecionado()
        if pid is None:
            return
        dados = self.dao.buscar(pid)
        if dados[3] == 1:
            messagebox.showinfo("Atenção", "Este diarista já está ativo.")
            return
        if messagebox.askyesno(
            "Confirmar Reativação",
            f"Deseja reativar '{dados[1]}'?\n\n"
            "A data de admissão será atualizada para hoje."
        ):
            if self.dao.reativar(pid, date.today().strftime("%Y-%m-%d")):
                messagebox.showinfo("Sucesso", "Diarista reativado com sucesso.")
                self.carregar()
            else:
                messagebox.showerror("Erro", "Erro ao reativar diarista.")

    def excluir(self):
        pid = self._diarista_selecionado()
        if pid is None:
            return
        dados = self.dao.buscar(pid)
        nome  = dados[1] if dados else "este diarista"
        if messagebox.askyesno(
            "Confirmar Exclusão",
            f"Deseja excluir permanentemente '{nome}'?\n\n"
            "⚠️ Considere usar 'Inativar' para preservar o histórico."
        ):
            if self.dao.excluir(pid):
                self.carregar()
            else:
                messagebox.showerror("Erro", "Erro ao excluir diarista.")