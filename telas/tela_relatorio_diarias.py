import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from tkcalendar import DateEntry
from dao.diaria_dao import DiariaDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path


class TelaRelatorioDiarias:
    def __init__(self, parent):
        self.parent = parent
        self.dao = DiariaDAO()

        self.janela = tk.Toplevel(parent)
        self.janela.title("Relatório de Gestão — Diárias")
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

        tk.Label(
            main,
            text="Relatório de Gestão de Diárias",
            font=('Segoe UI', 16, 'bold'),
            bg=CORES['bg_main'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 15))

        # ================= FILTROS =================
        filtro_card = tk.Frame(main, bg=CORES['bg_card'], relief='solid', bd=1)
        filtro_card.pack(fill="x", pady=(0, 15))

        filtro_inner = tk.Frame(filtro_card, bg=CORES['bg_card'])
        filtro_inner.pack(fill="x", padx=20, pady=15)

        linha1 = tk.Frame(filtro_inner, bg=CORES['bg_card'])
        linha1.pack(fill="x", pady=(0, 12))

        tk.Label(linha1, text="Agrupar por:",
                 bg=CORES['bg_card']).pack(side="left", padx=(0, 10))

        self.var_agrup = tk.StringVar(value="centro_custo")

        ttk.Radiobutton(linha1, text="Centro de Custo",
                variable=self.var_agrup,
                value="centro_custo").pack(side="left", padx=5)


        ttk.Radiobutton(linha1, text="Diarista",
                        variable=self.var_agrup,
                        value="diarista").pack(side="left", padx=5)

        ttk.Radiobutton(linha1, text="Mês",
                        variable=self.var_agrup,
                        value="mes").pack(side="left", padx=5)

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


        # Datas
        linha2 = tk.Frame(filtro_inner, bg=CORES['bg_card'])
        linha2.pack(fill="x")

        tk.Label(linha2, text="De:",
                 bg=CORES['bg_card']).pack(side="left", padx=(0, 5))

        self.date_ini = DateEntry(
            linha2, width=12,
            background=CORES['primary'],
            foreground='white',
            date_pattern='dd/mm/yyyy',
            locale='pt_BR'
        )
        self.date_ini.pack(side="left", padx=(0, 15))

        tk.Label(linha2, text="Até:",
                 bg=CORES['bg_card']).pack(side="left", padx=(0, 5))

        self.date_fim = DateEntry(
            linha2, width=12,
            background=CORES['primary'],
            foreground='white',
            date_pattern='dd/mm/yyyy',
            locale='pt_BR'
        )
        self.date_fim.pack(side="left", padx=(0, 20))

        self._atalho_mes()

        ttk.Button(
            linha2,
            text="🔍 Gerar Relatório",
            style="Primary.TButton",
            command=self._aplicar_filtros
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            linha2,
            text="🖨️ Imprimir PDF",
            style="Secondary.TButton",
            command=self._exportar_pdf
        ).pack(side="left")


        # ================= TOTAIS =================
        self.totais_frame = tk.Frame(main, bg=CORES['bg_main'])
        self.totais_frame.pack(fill="x", pady=(0, 15))

        # ================= TREE =================
        tree_card = tk.Frame(main, bg=CORES['bg_card'], relief='solid', bd=1)
        tree_card.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_card, show="headings")
        self.tree.pack(fill="both", expand=True)

        self.tree.tag_configure("par", background="#f8f9fa")
        self.tree.tag_configure("impar", background="white")
        self.tree.tag_configure("total", background=CORES['primary'],
                                foreground="white",
                                font=('Segoe UI', 9, 'bold'))

    # ------------------------------------------------------------------
    def _configurar_colunas_centro(self):
        self.tree.config(columns=("centro", "qtd", "total"))

        self.tree.heading("centro", text="Centro de Custo")
        self.tree.heading("qtd", text="Qtd. Diárias")
        self.tree.heading("total", text="Total (R$)")

        self.tree.column("centro", width=300, anchor="w")
        self.tree.column("qtd", width=120, anchor="center")
        self.tree.column("total", width=150, anchor="e")

    def _configurar_colunas_diarista(self):
        self.tree.config(columns=("nome", "cpf", "qtd", "total"))
        self.tree.heading("nome", text="Diarista")
        self.tree.heading("cpf", text="CPF")
        self.tree.heading("qtd", text="Qtd. Diárias")
        self.tree.heading("total", text="Total (R$)")

    def _configurar_colunas_mes(self):
        self.tree.config(columns=("mes", "qtd", "total"))
        self.tree.heading("mes", text="Mês")
        self.tree.heading("qtd", text="Qtd. Diárias")
        self.tree.heading("total", text="Total (R$)")

    # ------------------------------------------------------------------
    def _aplicar_filtros(self):
        ini = self.date_ini.get_date().strftime('%Y-%m-%d')
        fim = self.date_fim.get_date().strftime('%Y-%m-%d')

        if ini > fim:
            messagebox.showwarning("Atenção", "Período inválido!")
            return

        self.tree.delete(*self.tree.get_children())

        agrup = self.var_agrup.get()

        if agrup == "centro_custo":
            self._configurar_colunas_centro()
            dados = self.dao.relatorio_por_centro_custo(ini, fim)
            self._preencher_centro(dados)
        
        elif agrup == "diarista":
            self._configurar_colunas_diarista()
            dados = self.dao.relatorio_por_diarista(ini, fim)
            self._preencher_diarista(dados) 

        else:  # mês
            self._configurar_colunas_mes()
            dados = self.dao.relatorio_por_mes(ini, fim)
            self._preencher_mes(dados)


        self._atualizar_totais(dados, ini, fim)

    # ------------------------------------------------------------------
    def _preencher_centro(self, dados):
        total_qtd = total_val = 0

        for i, (centro, qtd_lanc, qtd_diarias, valor) in enumerate(dados):
            tag = "par" if i % 2 == 0 else "impar"

            self.tree.insert("", "end", values=(
                centro,
                qtd_diarias,
                self._fmt(valor)
            ), tags=(tag,))

            total_qtd += qtd_diarias
            total_val += valor

        self.tree.insert("", "end",
                        values=("TOTAL GERAL",
                                total_qtd,
                                self._fmt(total_val)),
                        tags=("total",))

    # ------------------------------------------------------------------
    def _preencher_diarista(self, dados):
        total_qtd = total_val = 0

        for i, (nome, cpf, qtd_lanc, qtd_diarias, valor) in enumerate(dados):
            tag = "par" if i % 2 == 0 else "impar"

            self.tree.insert("", "end", values=(
                nome, cpf, qtd_diarias,
                self._fmt(valor)
            ), tags=(tag,))

            total_qtd += qtd_diarias
            total_val += valor

        self.tree.insert("", "end",
                         values=("TOTAL GERAL", "—",
                                 total_qtd,
                                 self._fmt(total_val)),
                         tags=("total",))

    # ------------------------------------------------------------------
    def _preencher_mes(self, dados):
        total_qtd = total_val = 0

        for i, (mes, qtd_diarias, valor) in enumerate(dados):
            tag = "par" if i % 2 == 0 else "impar"

            self.tree.insert("", "end", values=(
                mes, qtd_diarias,
                self._fmt(valor)
            ), tags=(tag,))

            total_qtd += qtd_diarias
            total_val += valor

        self.tree.insert("", "end",
                         values=("TOTAL GERAL",
                                 total_qtd,
                                 self._fmt(total_val)),
                         tags=("total",))

    # ------------------------------------------------------------------
    def _atualizar_totais(self, dados, ini, fim):
        for w in self.totais_frame.winfo_children():
            w.destroy()

        total_val = sum(row[-1] for row in dados) if dados else 0
        total_qtd = sum(row[-2] for row in dados) if dados else 0

        periodo_ini = datetime.strptime(ini, '%Y-%m-%d').strftime('%d/%m/%Y')
        periodo_fim = datetime.strptime(fim, '%Y-%m-%d').strftime('%d/%m/%Y')

        cards = [
            ("📅 Período", f"{periodo_ini} a {periodo_fim}", CORES['primary']),
            ("📋 Total Diárias", str(total_qtd), CORES['warning']),
            ("💰 Total Pago", self._fmt(total_val), CORES['success']),
        ]

        for titulo, valor, cor in cards:
            c = tk.Frame(self.totais_frame, bg=cor, padx=20, pady=12)
            c.pack(side="left", fill="x", expand=True, padx=(0, 8))

            tk.Label(c, text=titulo,
                     bg=cor, fg='white').pack(anchor="w")
            tk.Label(c, text=valor,
                     font=('Segoe UI', 14, 'bold'),
                     bg=cor, fg='white').pack(anchor="w")

    # ------------------------------------------------------------------        
    def _exportar_pdf(self):
        ini = self.date_ini.get_date().strftime('%Y-%m-%d')
        fim = self.date_fim.get_date().strftime('%Y-%m-%d')

        if ini > fim:
            messagebox.showwarning("Atenção", "Período inválido!")
            return

        try:
            from services.relatorio_diaria_service import RelatorioDiariaPDF

            agrup = self.var_agrup.get()

            RelatorioDiariaPDF.gerar(
                self.janela,
                self.dao,
                agrup,
                ini,
                fim
            )

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
    def _fmt(valor):
        return (
            f"R$ {valor:,.2f}"
            .replace(',', 'X').replace('.', ',').replace('X', '.')
        )
