import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
from dao.servico_dao import ServicoDAO
from dao.diarista_dao import DiaristaDAO
from dao.centro_custo_dao import CentroCustoDAO
from telas.tela_novo_servico import TelaNovoServico
from services.recibo_servico_service import ReciboServicoService
from utils.constantes import CORES
from utils.auxiliares import resource_path
from PIL import Image, ImageTk


def formatar_data_br(data):
    if not data:
        return None
    if isinstance(data, (datetime, date)):
        return data.strftime("%d/%m/%Y")
    return datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")


def _fmt_valor(valor: float) -> str:
    return (
        f"R$ {valor:,.2f}"
        .replace(',', 'X').replace('.', ',').replace('X', '.')
    )


class ServicosEmbed:
    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.dao = ServicoDAO()
        self.diarista_dao = DiaristaDAO()
        self.centro_custo_dao = CentroCustoDAO()

        # cache completo para filtragem local
        self._servicos_cache = []

        self.criar_interface()
        self.carregar_servicos()

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
            img = Image.open(resource_path("Icones/servicos_azul.png")).resize(
                (32, 32), Image.LANCZOS)
            self.icon_header = ImageTk.PhotoImage(img)
            ttk.Label(left_header, image=self.icon_header,
                      background=CORES['bg_main']).pack(side="left", padx=(0, 15))
        except Exception:
            pass

        title_frame = ttk.Frame(left_header, style='Main.TFrame')
        title_frame.pack(side="left")

        ttk.Label(title_frame, text="Emissão de Serviços",
                  font=('Segoe UI', 18, 'bold'),
                  background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(anchor="w")

        ttk.Label(title_frame,
                  text="Registro e emissão de recibos de serviços prestados",
                  font=('Segoe UI', 9),
                  background=CORES['bg_main'],
                  foreground=CORES['text_light']).pack(anchor="w")

        right_header = ttk.Frame(header_frame, style='Main.TFrame')
        right_header.pack(side="right")

        ttk.Button(right_header, text="➕ Novo Serviço",
                   style="Primary.TButton",
                   command=self.novo_servico).pack(side="left", padx=5)

        ttk.Button(right_header, text="🔄 Atualizar",
                   style="Secondary.TButton",
                   command=self.carregar_servicos).pack(side="left", padx=5)

        ttk.Button(right_header, text="📊 Relatório",
                   style="Add.TButton",
                   command=self.abrir_relatorio).pack(side="left", padx=5)

        # ── Card principal ────────────────────────────────────────────────────
        card = ttk.Frame(main_frame, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)

        # ── Filtros ───────────────────────────────────────────────────────────
        filtro_frame = ttk.Frame(card, style="Card.TFrame")
        filtro_frame.pack(fill="x", pady=(0, 12))

        # Busca
        ttk.Label(filtro_frame, text="🔍 Buscar:",
                  font=('Segoe UI', 10),
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(side="left", padx=(0, 5))

        self.var_busca = tk.StringVar()
        self.var_busca.trace_add("write", lambda *_: self.aplicar_filtros())
        ttk.Entry(filtro_frame, textvariable=self.var_busca,
                  width=30).pack(side="left", padx=(0, 5))

        ttk.Label(filtro_frame, text="(nome ou CPF)",
                  font=('Segoe UI', 8),
                  background=CORES['bg_card'],
                  foreground=CORES['text_light']).pack(side="left", padx=(0, 15))

        # Período
        ttk.Separator(filtro_frame, orient="vertical").pack(
            side="left", fill="y", padx=10, pady=2)

        ttk.Label(filtro_frame, text="📅 Período:",
                  font=('Segoe UI', 10),
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(side="left", padx=(0, 5))

        self.combo_periodo = ttk.Combobox(
            filtro_frame,
            values=["Todos", "Hoje", "Última Semana", "Último Mês"],
            state="readonly", width=15
        )
        self.combo_periodo.set("Todos")
        self.combo_periodo.pack(side="left", padx=(0, 5))
        self.combo_periodo.bind("<<ComboboxSelected>>",
                                lambda _: self.carregar_servicos())

        ttk.Button(filtro_frame, text="✖ Limpar",
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

        # ── Ações ─────────────────────────────────────────────────────────────
        acoes_frame = ttk.Frame(card, style="Card.TFrame")
        acoes_frame.pack(fill="x", pady=(10, 0))


        ttk.Button(acoes_frame, text="✏️ Editar",
                   style="Primary.TButton",
                   command=lambda: self._acao("editar")).pack(side="left", padx=5)

        ttk.Button(acoes_frame, text="🗑️ Excluir",
                   style="Danger.TButton",
                   command=lambda: self._acao("excluir")).pack(side="left", padx=5)

        ttk.Label(acoes_frame,
                  text="Duplo clique para abrir o recibo",
                  font=('Segoe UI', 8, 'italic'),
                  background=CORES['bg_card'],
                  foreground=CORES['text_light']).pack(side="right")

        self.tree.bind("<Double-1>", lambda _e: self._acao("recibo"))

    # ─────────────────────────────────────────────────────────────────────────

    def _criar_treeview(self, parent):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure(
            "Servicos.Treeview",
            background="white", foreground=CORES['text_dark'],
            rowheight=32, fieldbackground="white",
            font=('Segoe UI', 9), borderwidth=0
        )
        style.configure(
            "Servicos.Treeview.Heading",
            background=CORES['primary'], foreground="white",
            font=('Segoe UI', 9, 'bold'), relief="flat", padding=(10, 8)
        )
        style.map("Servicos.Treeview",
                  background=[("selected", CORES['secondary'])],
                  foreground=[("selected", "white")])
        style.map("Servicos.Treeview.Heading",
                  background=[("active", CORES['primary'])])

        tree_frame = ttk.Frame(parent, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True)

        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        scroll_x.pack(side="bottom", fill="x")

        colunas = ("data", "diaristas", "centro_custo", "descricao", "valor")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=colunas,
            show="headings",
            style="Servicos.Treeview",
            selectmode="browse",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        self.tree.heading("data",         text="Data",            anchor="w")
        self.tree.heading("diaristas",    text="Diarista(s)",     anchor="w")
        self.tree.heading("centro_custo", text="Centro de Custo", anchor="w")
        self.tree.heading("descricao",    text="Descrição",       anchor="w")
        self.tree.heading("valor",        text="Valor Total",     anchor="e")

        self.tree.column("data",         width=100, minwidth=90,  stretch=False, anchor="w")
        self.tree.column("diaristas",    width=220, minwidth=140, stretch=False, anchor="w")
        self.tree.column("centro_custo", width=160, minwidth=110, stretch=False, anchor="w")
        self.tree.column("descricao",    width=240, minwidth=140, stretch=True,  anchor="w")
        self.tree.column("valor",        width=120, minwidth=90,  stretch=False, anchor="e")

        self.tree.tag_configure("par",   background="#f8f9fa")
        self.tree.tag_configure("impar", background="white")

        self.tree.pack(fill="both", expand=True)

    # ─────────────────────────────────────────────────────────────────────────
    # CARREGAMENTO / FILTRAGEM
    # ─────────────────────────────────────────────────────────────────────────

    def _get_filtro_periodo(self):
        periodo = self.combo_periodo.get()
        hoje    = datetime.now()
        if periodo == "Hoje":
            d = hoje.strftime('%Y-%m-%d')
            return d, d
        elif periodo == "Última Semana":
            return (hoje - timedelta(days=7)).strftime('%Y-%m-%d'), hoje.strftime('%Y-%m-%d')
        elif periodo == "Último Mês":
            return (hoje - timedelta(days=30)).strftime('%Y-%m-%d'), hoje.strftime('%Y-%m-%d')
        return None, None

    def carregar_servicos(self):
        ini, fim = self._get_filtro_periodo()
        self._servicos_cache = self.dao.listar(
            filtro_data_inicio=ini,
            filtro_data_fim=fim
        )
        self.aplicar_filtros()

    def aplicar_filtros(self):
        termo = self.var_busca.get().strip().lower()

        resultado = []
        for s in self._servicos_cache:
            if termo:
                # Busca em nome e CPF de qualquer participante
                match = any(
                    termo in p['nome'].lower() or termo in p['cpf']
                    for p in s['diaristas']
                )
                if not match:
                    continue
            resultado.append(s)

        self._popular_tree(resultado)

    def _popular_tree(self, servicos):
        selecionado = self._iid_selecionado()
        self.tree.delete(*self.tree.get_children())

        for i, s in enumerate(servicos):
            tag = "par" if i % 2 == 0 else "impar"

            # Exibe nomes resumidos: "João, Maria +1"
            nomes = [p['nome'].split()[0] for p in s['diaristas']]
            if len(nomes) <= 2:
                diaristas_txt = ", ".join(nomes)
            else:
                diaristas_txt = f"{', '.join(nomes[:2])} +{len(nomes)-2}"

            iid = str(s['id'])
            self.tree.insert(
                "", "end", iid=iid,
                values=(
                    formatar_data_br(s['data_servico']) or "—",
                    diaristas_txt,
                    s['centro_custo'],
                    s['descricao'],
                    _fmt_valor(s['valor'])
                ),
                tags=(tag,)
            )

        if selecionado and self.tree.exists(selecionado):
            self.tree.selection_set(selecionado)
            self.tree.see(selecionado)

        total = len(servicos)
        self.label_total.config(
            text=f"{total} serviço{'s' if total != 1 else ''} encontrado{'s' if total != 1 else ''}"
        )

    def limpar_filtros(self):
        self.var_busca.set("")
        self.combo_periodo.set("Todos")
        self.carregar_servicos()

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _iid_selecionado(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _servico_selecionado(self):
        iid = self._iid_selecionado()
        if not iid:
            return None
        pid = int(iid)
        return next((s for s in self._servicos_cache if s['id'] == pid), None)

    # ─────────────────────────────────────────────────────────────────────────
    # AÇÕES
    # ─────────────────────────────────────────────────────────────────────────

    def _acao(self, tipo):
        servico = self._servico_selecionado()
        if not servico:
            messagebox.showwarning("Atenção", "Selecione um serviço na tabela!")
            return
        if tipo == "recibo":
            self.exibir_recibo(servico)
        elif tipo == "editar":
            self.editar_servico(servico['id'])
        elif tipo == "excluir":
            nomes = ", ".join(p['nome'] for p in servico['diaristas'])
            self.excluir_servico(servico['id'], nomes)

    def abrir_relatorio(self):
        from telas.tela_relatorio_servicos import TelaRelatorioServicos
        TelaRelatorioServicos(self.parent_frame)

    def novo_servico(self):
        TelaNovoServico(self.parent_frame, self.carregar_servicos)

    def editar_servico(self, servico_id):
        TelaNovoServico(self.parent_frame, self.carregar_servicos, servico_id)

    def exibir_recibo(self, servico_dados):
        try:
            ReciboServicoService.gerar_recibo_temporario(servico_dados)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar recibo: {str(e)}")

    def excluir_servico(self, servico_id, diarista_nomes):
        if messagebox.askyesno(
            "Confirmar Exclusão",
            f"Excluir o serviço de '{diarista_nomes}'?\n\nEsta ação não pode ser desfeita!"
        ):
            if self.dao.excluir(servico_id):
                messagebox.showinfo("Sucesso", "Serviço excluído com sucesso!")
                self.carregar_servicos()
            else:
                messagebox.showerror("Erro", "Erro ao excluir serviço!")