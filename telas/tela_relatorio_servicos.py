import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from tkcalendar import DateEntry
from dao.servico_dao import ServicoDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path


class TelaRelatorioServicos:
    def __init__(self, parent):
        self.parent = parent
        self.dao = ServicoDAO()

        self.janela = tk.Toplevel(parent)
        self.janela.title("Relatório de Gestão — Serviços")
        self.janela.geometry("900x650")
        self.janela.configure(bg=CORES['bg_main'])
        

        caminho_icone = resource_path("Icones/logo.ico")
        self.janela.iconbitmap(caminho_icone)

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
            text="Relatório de Gestão de Serviços",
            font=('Segoe UI', 16, 'bold'),
            bg=CORES['bg_main'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 15))

        # ── Painel de Filtros ────────────────────────────────────────────
        filtro_card = tk.Frame(main, bg=CORES['bg_card'], relief='solid', bd=1)
        filtro_card.pack(fill="x", pady=(0, 15))

        filtro_inner = tk.Frame(filtro_card, bg=CORES['bg_card'])
        filtro_inner.pack(fill="x", padx=20, pady=15)

        # Linha 1: agrupamento + atalhos de período
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
            side="left", fill="y", padx=20)

        tk.Label(linha1, text="Atalho:",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(side="left", padx=(0, 10))

        atalhos = [
            ("Hoje",         self._atalho_hoje),
            ("Este mês",     self._atalho_mes),
            ("Este ano",     self._atalho_ano),
            ("Últimos 3m",   self._atalho_3m),
            ("Últimos 12m",  self._atalho_12m),
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

        # Linha 2: datas personalizadas + botão filtrar
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

        self._atalho_mes()   # padrão: mês atual — ambos os campos já existem

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
            "Rel.Treeview",
            background="white", foreground=CORES['text_dark'],
            rowheight=30, fieldbackground="white",
            font=('Segoe UI', 9), borderwidth=0
        )
        style.configure(
            "Rel.Treeview.Heading",
            background=CORES['primary'], foreground="white",
            font=('Segoe UI', 9, 'bold'), relief="flat", padding=(10, 8)
        )
        style.map("Rel.Treeview",
                  background=[("selected", CORES['secondary'])],
                  foreground=[("selected", "white")])
        style.map("Rel.Treeview.Heading",
                  background=[("active", CORES['primary'])])

        scroll_y = ttk.Scrollbar(parent, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        scroll_x = ttk.Scrollbar(parent, orient="horizontal")
        scroll_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            parent, style="Rel.Treeview",
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
        self.tree.config(columns=("centro", "qtd", "total"))
        self.tree.heading("centro", text="Centro de Custo", anchor="w")
        self.tree.heading("qtd",    text="Qtd. Serviços",  anchor="center")
        self.tree.heading("total",  text="Total (R$)",     anchor="e")
        self.tree.column("centro", width=350, minwidth=200, stretch=True,  anchor="w")
        self.tree.column("qtd",    width=120, minwidth=80,  stretch=False, anchor="center")
        self.tree.column("total",  width=150, minwidth=100, stretch=False, anchor="e")

    def _configurar_colunas_diarista(self):
        self.tree.config(columns=("nome", "cpf", "qtd", "total"))
        self.tree.heading("nome",  text="Diarista",       anchor="w")
        self.tree.heading("cpf",   text="CPF",            anchor="w")
        self.tree.heading("qtd",   text="Qtd. Serviços",  anchor="center")
        self.tree.heading("total", text="Total (R$)",     anchor="e")
        self.tree.column("nome",  width=250, minwidth=150, stretch=True,  anchor="w")
        self.tree.column("cpf",   width=140, minwidth=110, stretch=False, anchor="w")
        self.tree.column("qtd",   width=110, minwidth=80,  stretch=False, anchor="center")
        self.tree.column("total", width=140, minwidth=100, stretch=False, anchor="e")

    # ------------------------------------------------------------------
    def _aplicar_filtros(self):
        ini = self.date_ini.get_date().strftime('%Y-%m-%d')
        fim = self.date_fim.get_date().strftime('%Y-%m-%d')

        if ini > fim:
            messagebox.showwarning("Atenção", "A data inicial não pode ser maior que a final!")
            return

        self.tree.delete(*self.tree.get_children())

        agrup = self.var_agrup.get()

        if agrup == "centro_custo":
            self._configurar_colunas_centro()
            dados = self.dao.relatorio_por_centro_custo(ini, fim)
            self._preencher_centro(dados)
        else:
            self._configurar_colunas_diarista()
            dados = self.dao.relatorio_por_diarista(ini, fim)
            self._preencher_diarista(dados)

        self._atualizar_totais(dados, agrup, ini, fim)

    # ------------------------------------------------------------------
    def _preencher_centro(self, dados):
        if not dados:
            self.tree.insert("", "end",
                             values=("Nenhum resultado encontrado", "—", "—"),
                             tags=("impar",))
            return

        total_qtd = total_val = 0
        for i, (centro, qtd, valor) in enumerate(dados):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=(
                centro, qtd,
                self._fmt(valor)
            ), tags=(tag,))
            total_qtd += qtd
            total_val += valor

        # Linha de total
        self.tree.insert("", "end",
                         values=("TOTAL GERAL", total_qtd, self._fmt(total_val)),
                         tags=("total",))

    def _preencher_diarista(self, dados):
        if not dados:
            self.tree.insert("", "end",
                             values=("Nenhum resultado encontrado", "—", "—", "—"),
                             tags=("impar",))
            return

        total_qtd = total_val = 0
        for i, (nome, cpf, qtd, valor) in enumerate(dados):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=(
                nome, cpf, qtd, self._fmt(valor)
            ), tags=(tag,))
            total_qtd += qtd
            total_val += valor

        self.tree.insert("", "end",
                         values=("TOTAL GERAL", "—", total_qtd, self._fmt(total_val)),
                         tags=("total",))

    # ------------------------------------------------------------------
    def _atualizar_totais(self, dados, agrup, ini, fim):
        for w in self.totais_frame.winfo_children():
            w.destroy()

        total_val = sum(row[-1] for row in dados) if dados else 0
        total_qtd = sum(row[-2] for row in dados) if dados else 0
        qtd_grupos = len(dados)

        label_grupo = "centros" if agrup == "centro_custo" else "diaristas"

        periodo_ini = datetime.strptime(ini, '%Y-%m-%d').strftime('%d/%m/%Y')
        periodo_fim = datetime.strptime(fim, '%Y-%m-%d').strftime('%d/%m/%Y')

        cards = [
            ("📅 Período",         f"{periodo_ini} a {periodo_fim}", CORES['primary']),
            (f"🏷️ {label_grupo.capitalize()}", str(qtd_grupos),      CORES['secondary']),
            ("📋 Total Serviços",  str(total_qtd),                   CORES['warning']),
            ("💰 Total Pago",       self._fmt(total_val),            CORES['success']),
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
            from services.relatorio_servico_service import RelatorioServicoPDF
            agrup = self.var_agrup.get()
            RelatorioServicoPDF.gerar(self.janela, self.dao, agrup, ini, fim)
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