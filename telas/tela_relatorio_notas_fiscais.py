import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from dateutil.relativedelta import relativedelta
from tkcalendar import DateEntry

from dao.notas_fiscais_dao import NotasFiscaisDAO
from services.relatorio_notas_fiscais_service import (
    RelatorioNotasFiscaisPDF, _fmt_brl, _fmt_data_br, _status_nota
)
from utils.auxiliares import resource_path
from utils.constantes import CORES

DATA_MINIMA = date(2000, 1, 1)

STATUS_LABEL = {"pendente": "Pendentes", "ok": "Com recibo", "pago": "Pagos"}


class TelaRelatorioNotasFiscais:
    def __init__(self, parent):
        self.parent = parent
        self.dao = NotasFiscaisDAO()
        self._notas_atuais = []

        self.janela = tk.Toplevel(parent)
        self.janela.title("Relatório de Gestão — Notas Fiscais")
        self.janela.geometry("980x650")
        self.janela.configure(bg=CORES['bg_main'])

        try:
            self.janela.iconbitmap(resource_path("Icones/logo.ico"))
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

        tk.Label(
            main, text="Relatório de Gestão de Notas Fiscais",
            font=('Segoe UI', 16, 'bold'), bg=CORES['bg_main'], fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 15))

        filtro_card = tk.Frame(main, bg=CORES['bg_card'], relief='solid', bd=1)
        filtro_card.pack(fill="x", pady=(0, 15))
        filtro_inner = tk.Frame(filtro_card, bg=CORES['bg_card'])
        filtro_inner.pack(fill="x", padx=20, pady=15)

        # Linha 1: status + emitente
        linha1 = tk.Frame(filtro_inner, bg=CORES['bg_card'])
        linha1.pack(fill="x", pady=(0, 12))

        tk.Label(linha1, text="Status:", font=('Segoe UI', 10),
                bg=CORES['bg_card'], fg=CORES['text_dark']).pack(side="left", padx=(0, 10))
        self.var_status = tk.StringVar(value="todos")
        for texto, valor in [("Todos", "todos"), ("Pendentes", "pendente"),
                             ("Com recibo", "ok"), ("Pagos", "pago")]:
            ttk.Radiobutton(linha1, text=texto, variable=self.var_status, value=valor
                           ).pack(side="left", padx=5)

        tk.Frame(linha1, bg=CORES['border'], width=1).pack(side="left", fill="y", padx=20)

        tk.Label(linha1, text="Emitente:", font=('Segoe UI', 10),
                bg=CORES['bg_card'], fg=CORES['text_dark']).pack(side="left", padx=(0, 8))
        fornecedores = self.dao.listar_fornecedores_select()
        self._forn_map = {f["nome"]: f["id"] for f in fornecedores}
        opcoes = ["Todos os emitentes"] + [f["nome"] for f in fornecedores]
        self.var_emitente = tk.StringVar(value="Todos os emitentes")
        ttk.Combobox(linha1, textvariable=self.var_emitente, values=opcoes,
                    state="readonly", width=28).pack(side="left")

        # Linha 2: atalhos de período
        linha2 = tk.Frame(filtro_inner, bg=CORES['bg_card'])
        linha2.pack(fill="x", pady=(0, 12))

        tk.Label(linha2, text="Atalho:", font=('Segoe UI', 10),
                bg=CORES['bg_card'], fg=CORES['text_dark']).pack(side="left", padx=(0, 10))

        atalhos = [
            ("Este mês", self._atalho_mes),
            ("Este ano", self._atalho_ano),
            ("Últimos 3m", self._atalho_3m),
            ("Últimos 12m", self._atalho_12m),
            ("Todas as datas", self._atalho_tudo),
        ]
        for label, cmd in atalhos:
            tk.Button(
                linha2, text=label, font=('Segoe UI', 8),
                bg=CORES['secondary'], fg='white', relief='flat', cursor='hand2',
                padx=10, pady=4, command=cmd
            ).pack(side="left", padx=3)

        # Linha 3: datas + ações
        linha3 = tk.Frame(filtro_inner, bg=CORES['bg_card'])
        linha3.pack(fill="x")

        tk.Label(linha3, text="De:", font=('Segoe UI', 10),
                bg=CORES['bg_card'], fg=CORES['text_dark']).pack(side="left", padx=(0, 5))
        self.date_ini = DateEntry(
            linha3, font=('Segoe UI', 10), width=12,
            background=CORES['primary'], foreground='white',
            borderwidth=1, date_pattern='dd/mm/yyyy', locale='pt_BR'
        )
        self.date_ini.pack(side="left", padx=(0, 15))

        tk.Label(linha3, text="Até:", font=('Segoe UI', 10),
                bg=CORES['bg_card'], fg=CORES['text_dark']).pack(side="left", padx=(0, 5))
        self.date_fim = DateEntry(
            linha3, font=('Segoe UI', 10), width=12,
            background=CORES['primary'], foreground='white',
            borderwidth=1, date_pattern='dd/mm/yyyy', locale='pt_BR'
        )
        self.date_fim.pack(side="left", padx=(0, 20))

        self._atalho_mes()  # padrão: mês atual

        ttk.Button(linha3, text="🔍 Aplicar Filtros", style="Primary.TButton",
                  command=self._aplicar_filtros).pack(side="left", padx=(0, 10))
        ttk.Button(linha3, text="🖨️ Exportar PDF", style="Secondary.TButton",
                  command=self._exportar_pdf).pack(side="left", padx=(0, 10))
        ttk.Button(linha3, text="📎 PDF de Recibos Anexados", style="Add.TButton",
                  command=self._exportar_recibos_anexados).pack(side="left")

        # Cards de totais
        self.totais_frame = tk.Frame(main, bg=CORES['bg_main'])
        self.totais_frame.pack(fill="x", pady=(0, 15))

        # Treeview de prévia
        tree_card = tk.Frame(main, bg=CORES['bg_card'], relief='solid', bd=1)
        tree_card.pack(fill="both", expand=True)
        self._criar_treeview(tree_card)

    # ------------------------------------------------------------------
    def _criar_treeview(self, parent):
        style = ttk.Style()
        style.configure(
            "RelNF.Treeview",
            background="white", foreground=CORES['text_dark'],
            rowheight=28, fieldbackground="white",
            font=('Segoe UI', 9), borderwidth=0
        )
        style.configure(
            "RelNF.Treeview.Heading",
            background=CORES['primary'], foreground="white",
            font=('Segoe UI', 9, 'bold'), relief="flat", padding=(10, 8)
        )
        style.map("RelNF.Treeview",
                  background=[("selected", CORES['secondary'])],
                  foreground=[("selected", "white")])

        scroll_y = ttk.Scrollbar(parent, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            parent, style="RelNF.Treeview", show="headings",
            columns=("numero", "emitente", "competencia", "emissao", "valor", "status"),
            yscrollcommand=scroll_y.set
        )
        self.tree.pack(fill="both", expand=True)
        scroll_y.config(command=self.tree.yview)

        cols = [
            ("numero", "Nº NF", 80, "w"),
            ("emitente", "Emitente", 280, "w"),
            ("competencia", "Competência", 110, "center"),
            ("emissao", "Emissão", 100, "center"),
            ("valor", "Valor", 120, "e"),
            ("status", "Status", 120, "center"),
        ]
        for key, label, width, anchor in cols:
            self.tree.heading(key, text=label, anchor=anchor)
            self.tree.column(key, width=width, anchor=anchor, stretch=(key == "emitente"))

        self.tree.tag_configure("par", background="#f8f9fa")
        self.tree.tag_configure("impar", background="white")
        self.tree.tag_configure("pago", foreground=CORES['success'])
        self.tree.tag_configure("ok", foreground=CORES['primary'])
        self.tree.tag_configure("pendente", foreground=CORES['warning'])

    # ------------------------------------------------------------------
    def _aplicar_filtros(self):
        ini = self.date_ini.get_date().strftime('%Y-%m-%d')
        fim = self.date_fim.get_date().strftime('%Y-%m-%d')

        if ini > fim:
            messagebox.showwarning("Atenção", "A data inicial não pode ser maior que a final!")
            return

        status = self.var_status.get()
        filtro_status = None if status == "todos" else status

        emitente_sel = self.var_emitente.get()
        emitente_id = self._forn_map.get(emitente_sel) if emitente_sel != "Todos os emitentes" else None

        notas = self.dao.listar_notas(
            filtro_status=filtro_status, emitente_id=emitente_id,
            data_ini=ini, data_fim=fim
        )
        self._notas_atuais = notas
        self._preencher_tree(notas)
        self._atualizar_totais(notas)

    def _preencher_tree(self, notas):
        self.tree.delete(*self.tree.get_children())
        if not notas:
            self.tree.insert("", "end", values=("Nenhuma nota encontrada", "—", "—", "—", "—", "—"))
            return

        for i, n in enumerate(notas):
            status_key, status_txt = _status_nota(n)
            tag_par = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", tags=(tag_par, status_key), values=(
                n["numero"], n["emitente"], n["competencia"],
                _fmt_data_br(n["data_emissao"]), _fmt_brl(n["valor"]), status_txt
            ))

    def _atualizar_totais(self, notas):
        for w in self.totais_frame.winfo_children():
            w.destroy()

        total_qtd = len(notas)
        pendentes = sum(1 for n in notas if _status_nota(n)[0] == "pendente")
        pagos = sum(1 for n in notas if _status_nota(n)[0] == "pago")
        valor_total = sum(n["valor"] for n in notas)

        cards = [
            ("📋 Total de NFs", str(total_qtd), CORES['primary']),
            ("⏳ Pendentes", str(pendentes), CORES['warning']),
            ("✅ Pagas", str(pagos), CORES['success']),
            ("💰 Valor Total", _fmt_brl(valor_total), CORES['secondary']),
        ]
        for titulo, valor, cor in cards:
            c = tk.Frame(self.totais_frame, bg=cor, padx=20, pady=12)
            c.pack(side="left", fill="x", expand=True, padx=(0, 8))
            tk.Label(c, text=titulo, font=('Segoe UI', 8), bg=cor, fg='white').pack(anchor="w")
            tk.Label(c, text=valor, font=('Segoe UI', 14, 'bold'), bg=cor, fg='white').pack(anchor="w")

    # ------------------------------------------------------------------
    def _descricao_filtros(self):
        partes = []
        if self.date_ini.get_date() <= DATA_MINIMA:
            partes.append("Período: todas as datas")
        else:
            ini = self.date_ini.get_date().strftime('%d/%m/%Y')
            fim = self.date_fim.get_date().strftime('%d/%m/%Y')
            partes.append(f"Período: {ini} a {fim}")

        status = self.var_status.get()
        if status != "todos":
            partes.append(f"Status: {STATUS_LABEL[status]}")

        emitente_sel = self.var_emitente.get()
        if emitente_sel != "Todos os emitentes":
            partes.append(f"Emitente: {emitente_sel}")

        return "   |   ".join(partes)

    def _exportar_pdf(self):
        if not self._notas_atuais:
            if not messagebox.askyesno(
                "Atenção",
                "Nenhuma nota encontrada com os filtros atuais.\nGerar relatório vazio mesmo assim?"
            ):
                return
        try:
            RelatorioNotasFiscaisPDF.gerar(self._notas_atuais, self._descricao_filtros())
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF:\n{e}")

    def _exportar_recibos_anexados(self):
        if not self._notas_atuais:
            messagebox.showwarning("Atenção", "Nenhuma nota encontrada com os filtros atuais.")
            return

        from services.relatorio_recibos_anexados_service import RelatorioRecibosAnexadosPDF
        try:
            caminho, problemas = RelatorioRecibosAnexadosPDF.gerar(self.dao, self._notas_atuais)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar o PDF de recibos anexados:\n{e}")
            return

        if not caminho:
            messagebox.showinfo(
                "Nenhum recibo incluído",
                "\n".join(problemas) if problemas else
                "Nenhuma das notas filtradas possui recibo anexado."
            )
            return

        if problemas:
            messagebox.showwarning(
                "PDF gerado com avisos",
                "O PDF foi gerado, mas alguns recibos não puderam ser incluídos:\n\n"
                + "\n".join(problemas)
            )

    # ------------------------------------------------------------------
    # Atalhos de período
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

    def _atalho_tudo(self):
        self.date_ini.set_date(DATA_MINIMA)
        self.date_fim.set_date(date.today())
