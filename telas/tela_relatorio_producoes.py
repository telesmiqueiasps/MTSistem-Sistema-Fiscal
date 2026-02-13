import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from tkcalendar import DateEntry
from dao.producao_dao import ProducaoDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path


class TelaRelatorioProducoes:
    def __init__(self, parent):
        self.parent = parent
        self.dao = ProducaoDAO()

        self.janela = tk.Toplevel(parent)
        self.janela.title("Relatório de Gestão — Produções")
        self.janela.geometry("960x680")
        self.janela.configure(bg=CORES['bg_main'])

        try:
            caminho_icone = resource_path("Icones/logo.ico")
            self.janela.iconbitmap(caminho_icone)
        except Exception:
            pass

        self.centralizar()
        self._criar_interface()
        self._aplicar_filtros()

    # ------------------------------------------------------------------
    def centralizar(self):
        self.janela.update_idletasks()
        w = self.janela.winfo_width()
        h = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

    # ------------------------------------------------------------------
    def _criar_interface(self):
        main = tk.Frame(self.janela, bg=CORES['bg_main'])
        main.pack(fill="both", expand=True, padx=25, pady=20)

        # ── Título ──────────────────────────────────────────────────────
        tk.Label(
            main,
            text="Relatório de Gestão de Produções",
            font=('Segoe UI', 16, 'bold'),
            bg=CORES['bg_main'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 15))

        # ── Painel de Filtros ────────────────────────────────────────────
        filtro_card = tk.Frame(main, bg=CORES['bg_card'], relief='solid', bd=1)
        filtro_card.pack(fill="x", pady=(0, 15))

        filtro_inner = tk.Frame(filtro_card, bg=CORES['bg_card'])
        filtro_inner.pack(fill="x", padx=20, pady=15)

        # Linha 1: agrupamento + status + atalhos
        linha1 = tk.Frame(filtro_inner, bg=CORES['bg_card'])
        linha1.pack(fill="x", pady=(0, 12))

        tk.Label(linha1, text="Agrupar por:",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(side="left", padx=(0, 10))

        self.var_agrup = tk.StringVar(value="centro_custo")
        ttk.Radiobutton(linha1, text="Centro de Custo",
                        variable=self.var_agrup, value="centro_custo"
                        ).pack(side="left", padx=5)
        ttk.Radiobutton(linha1, text="Diarista",
                        variable=self.var_agrup, value="diarista"
                        ).pack(side="left", padx=5)

        # Separador vertical
        tk.Frame(linha1, bg=CORES['border'], width=1).pack(
            side="left", fill="y", padx=15)

        tk.Label(linha1, text="Status:",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(side="left", padx=(0, 8))

        self.var_status = tk.StringVar(value="todas")
        for texto, valor in [("Todas", "todas"), ("Fechadas", "fechadas")]:
            ttk.Radiobutton(linha1, text=texto,
                            variable=self.var_status, value=valor
                            ).pack(side="left", padx=4)

        # Separador vertical
        tk.Frame(linha1, bg=CORES['border'], width=1).pack(
            side="left", fill="y", padx=15)

        tk.Label(linha1, text="Atalho:",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(side="left", padx=(0, 10))

        atalhos = [
            ("Hoje",        self._atalho_hoje),
            ("Este mês",    self._atalho_mes),
            ("Este ano",    self._atalho_ano),
            ("Últimos 3m",  self._atalho_3m),
            ("Últimos 12m", self._atalho_12m),
        ]
        for label, cmd in atalhos:
            tk.Button(
                linha1, text=label,
                font=('Segoe UI', 8),
                bg=CORES['secondary'], fg='white',
                relief='flat', cursor='hand2',
                padx=10, pady=4,
                command=cmd
            ).pack(side="left", padx=3)

        # Linha 2: datas + centro de custo + botões
        linha2 = tk.Frame(filtro_inner, bg=CORES['bg_card'])
        linha2.pack(fill="x")

        tk.Label(linha2, text="De:",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(side="left", padx=(0, 5))

        self.date_ini = DateEntry(
            linha2, font=('Segoe UI', 10), width=12,
            background=CORES['primary'], foreground='white',
            borderwidth=1, date_pattern='dd/mm/yyyy', locale='pt_BR'
        )
        self.date_ini.pack(side="left", padx=(0, 15))

        tk.Label(linha2, text="Até:",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(side="left", padx=(0, 5))

        self.date_fim = DateEntry(
            linha2, font=('Segoe UI', 10), width=12,
            background=CORES['primary'], foreground='white',
            borderwidth=1, date_pattern='dd/mm/yyyy', locale='pt_BR'
        )
        self.date_fim.pack(side="left", padx=(0, 20))

        # Filtro de centro de custo
        tk.Label(linha2, text="Centro:",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(side="left", padx=(0, 5))

        self._centros = self.dao.listar_centros_custo()
        nomes = ["Todos"] + [c['centro'] for c in self._centros]
        self._combo_centro = ttk.Combobox(
            linha2, values=nomes, font=('Segoe UI', 10),
            state="readonly", width=22
        )
        self._combo_centro.pack(side="left", padx=(0, 20))
        self._combo_centro.current(0)

        self._atalho_mes()   # padrão: mês atual

        ttk.Button(
            linha2, text="🔍 Gerar Relatório",
            style="Primary.TButton",
            command=self._aplicar_filtros
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            linha2, text="🖨️ Imprimir PDF",
            style="Secondary.TButton",
            command=self._exportar_pdf
        ).pack(side="left")

        # ── Cards de totais ──────────────────────────────────────────────
        self.totais_frame = tk.Frame(main, bg=CORES['bg_main'])
        self.totais_frame.pack(fill="x", pady=(0, 15))

        # ── Treeview ────────────────────────────────────────────────────
        tree_card = tk.Frame(main, bg=CORES['bg_card'], relief='solid', bd=1)
        tree_card.pack(fill="both", expand=True)

        self._criar_treeview(tree_card)

    # ------------------------------------------------------------------
    def _criar_treeview(self, parent):
        style = ttk.Style()
        style.configure(
            "RelProd.Treeview",
            background="white", foreground=CORES['text_dark'],
            rowheight=30, fieldbackground="white",
            font=('Segoe UI', 9), borderwidth=0
        )
        style.configure(
            "RelProd.Treeview.Heading",
            background=CORES['primary'], foreground="white",
            font=('Segoe UI', 9, 'bold'), relief="flat", padding=(10, 8)
        )
        style.map("RelProd.Treeview",
                  background=[("selected", CORES['secondary'])],
                  foreground=[("selected", "white")])
        style.map("RelProd.Treeview.Heading",
                  background=[("active", CORES['primary'])])

        scroll_y = ttk.Scrollbar(parent, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        scroll_x = ttk.Scrollbar(parent, orient="horizontal")
        scroll_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            parent, style="RelProd.Treeview",
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        self.tree.pack(fill="both", expand=True)

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        self.tree.tag_configure("par",   background="#f8f9fa")
        self.tree.tag_configure("impar", background="white")
        self.tree.tag_configure("total", background=CORES['primary'],
                                         foreground="white",
                                         font=('Segoe UI', 9, 'bold'))

    # ------------------------------------------------------------------
    def _configurar_colunas_centro(self):
        self.tree.config(columns=("centro", "qtd", "sacos", "valor"))
        self.tree.heading("centro", text="Centro de Custo", anchor="w")
        self.tree.heading("qtd",    text="Qtd. Produções",  anchor="center")
        self.tree.heading("sacos",  text="Total Sacos",     anchor="center")
        self.tree.heading("valor",  text="Valor Total (R$)", anchor="e")
        self.tree.column("centro", width=300, minwidth=180, stretch=True,  anchor="w")
        self.tree.column("qtd",    width=120, minwidth=80,  stretch=False, anchor="center")
        self.tree.column("sacos",  width=120, minwidth=80,  stretch=False, anchor="center")
        self.tree.column("valor",  width=160, minwidth=110, stretch=False, anchor="e")

    def _configurar_colunas_diarista(self):
        self.tree.config(columns=("nome", "cpf", "sacos", "valor"))
        self.tree.heading("nome",  text="Diarista",          anchor="w")
        self.tree.heading("cpf",   text="CPF",               anchor="w")
        self.tree.heading("sacos", text="Total Sacos",       anchor="center")
        self.tree.heading("valor", text="Valor Total (R$)",  anchor="e")
        self.tree.column("nome",  width=280, minwidth=160, stretch=True,  anchor="w")
        self.tree.column("cpf",   width=140, minwidth=110, stretch=False, anchor="w")
        self.tree.column("sacos", width=130, minwidth=80,  stretch=False, anchor="center")
        self.tree.column("valor", width=160, minwidth=110, stretch=False, anchor="e")

    # ------------------------------------------------------------------
    def _centro_custo_id_filtro(self):
        """Retorna o centro_custo_id selecionado, ou None se 'Todos'."""
        idx = self._combo_centro.current()
        if idx <= 0:
            return None
        return self._centros[idx - 1]['id']   # -1 porque índice 0 = "Todos"

    def _aplicar_filtros(self):
        ini = self.date_ini.get_date().strftime('%Y-%m-%d')
        fim = self.date_fim.get_date().strftime('%Y-%m-%d')

        if ini > fim:
            messagebox.showwarning("Atenção", "A data inicial não pode ser maior que a final!")
            return

        self.tree.delete(*self.tree.get_children())

        agrup          = self.var_agrup.get()
        apenas_fechadas = self.var_status.get() == "fechadas"
        centro_id      = self._centro_custo_id_filtro()

        if agrup == "centro_custo":
            self._configurar_colunas_centro()
            dados = self.dao.relatorio_por_centro_custo(ini, fim, apenas_fechadas)
            self._preencher_centro(dados)
        else:
            self._configurar_colunas_diarista()
            dados = self.dao.relatorio_por_diarista(ini, fim, centro_id)
            self._preencher_diarista(dados)

        self._atualizar_totais(dados, agrup, ini, fim)

    # ------------------------------------------------------------------
    def _preencher_centro(self, dados):
        if not dados:
            self.tree.insert("", "end",
                             values=("Nenhum resultado encontrado", "—", "—", "—"),
                             tags=("impar",))
            return

        total_qtd = total_sacos = total_val = 0
        for i, d in enumerate(dados):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=(
                d['centro'],
                d['qtd_producoes'],
                d['total_sacos'],
                self._fmt(d['valor_total'])
            ), tags=(tag,))
            total_qtd   += d['qtd_producoes']
            total_sacos += d['total_sacos']
            total_val   += d['valor_total']

        self.tree.insert("", "end",
                         values=("TOTAL GERAL", total_qtd, total_sacos, self._fmt(total_val)),
                         tags=("total",))

    def _preencher_diarista(self, dados):
        if not dados:
            self.tree.insert("", "end",
                             values=("Nenhum resultado encontrado", "—", "—", "—"),
                             tags=("impar",))
            return

        total_sacos = total_val = 0
        for i, d in enumerate(dados):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=(
                d['nome'],
                d['cpf'],
                d['total_sacos'],
                self._fmt(d['valor_total'])
            ), tags=(tag,))
            total_sacos += d['total_sacos']
            total_val   += d['valor_total']

        self.tree.insert("", "end",
                         values=("TOTAL GERAL", "—", total_sacos, self._fmt(total_val)),
                         tags=("total",))

    # ------------------------------------------------------------------
    def _atualizar_totais(self, dados, agrup, ini, fim):
        for w in self.totais_frame.winfo_children():
            w.destroy()

        total_val   = sum(d['valor_total']   for d in dados) if dados else 0
        total_sacos = sum(d['total_sacos']   for d in dados) if dados else 0
        qtd_grupos  = len(dados)

        label_grupo = "centros" if agrup == "centro_custo" else "diaristas"

        periodo_ini = datetime.strptime(ini, '%Y-%m-%d').strftime('%d/%m/%Y')
        periodo_fim = datetime.strptime(fim, '%Y-%m-%d').strftime('%d/%m/%Y')

        cards = [
            ("📅 Período",                 f"{periodo_ini} a {periodo_fim}", CORES['primary']),
            (f"🏷️ {label_grupo.capitalize()}", str(qtd_grupos),             CORES['secondary']),
            ("📦 Total Sacos",             str(total_sacos),                 CORES['warning']),
            ("💰 Valor Total",             self._fmt(total_val),             CORES['success']),
        ]

        for titulo, valor, cor in cards:
            c = tk.Frame(self.totais_frame, bg=cor, padx=20, pady=12)
            c.pack(side="left", fill="x", expand=True, padx=(0, 8))
            tk.Label(c, text=titulo, font=('Segoe UI', 8),
                     bg=cor, fg='white').pack(anchor="w")
            tk.Label(c, text=valor, font=('Segoe UI', 14, 'bold'),
                     bg=cor, fg='white').pack(anchor="w")

    # ------------------------------------------------------------------
    def _exportar_pdf(self):
        ini = self.date_ini.get_date().strftime('%Y-%m-%d')
        fim = self.date_fim.get_date().strftime('%Y-%m-%d')

        if ini > fim:
            messagebox.showwarning("Atenção", "Período inválido!")
            return

        try:
            from services.relatorio_producao_service import RelatorioProducaoPDF
            agrup           = self.var_agrup.get()
            apenas_fechadas = self.var_status.get() == "fechadas"
            centro_id       = self._centro_custo_id_filtro()
            RelatorioProducaoPDF.gerar(self.janela, self.dao, agrup,
                                       ini, fim, apenas_fechadas, centro_id)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF:\n{str(e)}")

    # ------------------------------------------------------------------
    # Atalhos de período
    def _atalho_hoje(self):
        hoje = date.today()
        self.date_ini.set_date(hoje)
        self.date_fim.set_date(hoje)

    def _atalho_mes(self):
        hoje = date.today()
        self.date_ini.set_date(hoje.replace(day=1))
        self.date_fim.set_date(hoje)

    def _atalho_ano(self):
        hoje = date.today()
        self.date_ini.set_date(hoje.replace(month=1, day=1))
        self.date_fim.set_date(hoje)

    def _atalho_3m(self):
        hoje = date.today()
        self.date_ini.set_date(hoje - relativedelta(months=3))
        self.date_fim.set_date(hoje)

    def _atalho_12m(self):
        hoje = date.today()
        self.date_ini.set_date(hoje - relativedelta(months=12))
        self.date_fim.set_date(hoje)

    # ------------------------------------------------------------------
    @staticmethod
    def _fmt(valor) -> str:
        return (
            f"R$ {valor:,.2f}"
            .replace(',', 'X').replace('.', ',').replace('X', '.')
        )