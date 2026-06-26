import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from dao.notas_fiscais_dao import NotasFiscaisDAO
from database.sessao import sessao
from telas.tela_fornecedores_nf import FornecedoresNFEmbed
from telas.tela_importacao_lote_nf import ImportacaoLoteNFDialog
from telas.tela_nota_fiscal_form import NotaFiscalFormDialog
from telas.tela_recibo_nota import ReciboNotaDialog
from telas.tela_recibos_assinados import RecibosAssinadosEmbed
from utils.auxiliares import pasta_recibos_nf, resource_path
from utils.constantes import CORES
from PIL import Image, ImageTk


def _fmt_brl(valor):
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _abrir_arquivo(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o arquivo:\n{e}")


def _fmt_data_br(iso):
    if not iso:
        return "—"
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return iso


class NotasFiscaisEmbed:
    """Tela principal do módulo de Notas Fiscais de Serviço, com sub-abas
    para Notas Fiscais, Fornecedores e Recibos Assinados."""

    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.dao = NotasFiscaisDAO()
        self.recibos_dir = pasta_recibos_nf(sessao.empresa_id)

        self._aba_atual = "notas"
        self._filtro_status = None
        self._emitente_filtro_id = None
        self._emitente_filtro_nome = None

        self.criar_interface()
        self._mostrar_aba("notas")

    # ─────────────────────────────────────────────────────────────────────────
    # ESTRUTURA GERAL
    # ─────────────────────────────────────────────────────────────────────────

    def criar_interface(self):
        main_frame = ttk.Frame(self.parent_frame, style='Main.TFrame')
        main_frame.pack(fill="both", expand=True, padx=50, pady=30)

        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.pack(fill="x", pady=(0, 16))

        left_header = ttk.Frame(header_frame, style='Main.TFrame')
        left_header.pack(side="left")

        try:
            img = Image.open(resource_path("Icones/notas_fiscal.png")).resize((32, 32), Image.LANCZOS)
            self.icon_header = ImageTk.PhotoImage(img)
            ttk.Label(left_header, image=self.icon_header,
                      background=CORES['bg_main']).pack(side="left", padx=(0, 15))
        except Exception:
            pass

        title_frame = ttk.Frame(left_header, style='Main.TFrame')
        title_frame.pack(side="left")

        ttk.Label(title_frame, text="Notas Fiscais de Serviço",
                  font=('Segoe UI', 18, 'bold'),
                  background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(anchor="w")
        ttk.Label(title_frame, text="Controle de emissões, recibos e pagamentos",
                  font=('Segoe UI', 9),
                  background=CORES['bg_main'],
                  foreground=CORES['text_light']).pack(anchor="w")

        right_header = ttk.Frame(header_frame, style='Main.TFrame')
        right_header.pack(side="right")

        ttk.Button(right_header, text="➕ Nova Nota Fiscal", style="Primary.TButton",
                   command=self.nova_nota).pack(side="left", padx=5)
        ttk.Button(right_header, text="📥 Importar em Lote (XML)", style="Secondary.TButton",
                   command=self.abrir_importacao_lote).pack(side="left", padx=5)
        ttk.Button(right_header, text="📊 Relatório", style="Add.TButton",
                   command=self.abrir_relatorio).pack(side="left", padx=5)

        # ── SUB-NAVEGAÇÃO ────────────────────────────────────────────────────
        nav_frame = ttk.Frame(main_frame, style='Main.TFrame')
        nav_frame.pack(fill="x", pady=(0, 14))

        self._nav_buttons = {}
        for key, label in [
            ("notas", "📋 Notas Fiscais"),
            ("fornecedores", "🏢 Fornecedores"),
            ("recibos", "📎 Recibos Assinados"),
        ]:
            btn = ttk.Button(nav_frame, text=label, style="Secondary.TButton",
                             command=lambda k=key: self._mostrar_aba(k))
            btn.pack(side="left", padx=(0, 6))
            self._nav_buttons[key] = btn

        # ── STATS (somente na aba Notas) ─────────────────────────────────────
        self.stats_frame = ttk.Frame(main_frame, style='Main.TFrame')

        # ── CARD DE CONTEÚDO ─────────────────────────────────────────────────
        self.card = ttk.Frame(main_frame, style="Card.TFrame", padding=20)
        self.card.pack(fill="both", expand=True)

    def _mostrar_aba(self, key):
        self._aba_atual = key
        for k, btn in self._nav_buttons.items():
            btn.configure(style="Primary.TButton" if k == key else "Secondary.TButton")

        self.stats_frame.pack_forget()
        for w in self.card.winfo_children():
            w.destroy()

        if key == "notas":
            self.stats_frame.pack(fill="x", pady=(0, 14), before=self.card)
            self._build_notas()
        elif key == "fornecedores":
            FornecedoresNFEmbed(self.card, on_filtrar_notas=self._filtrar_por_fornecedor)
        elif key == "recibos":
            RecibosAssinadosEmbed(self.card, self.recibos_dir)

    def _filtrar_por_fornecedor(self, forn_id, forn_nome):
        self._emitente_filtro_id = forn_id
        self._emitente_filtro_nome = forn_nome
        self._mostrar_aba("notas")

    # ─────────────────────────────────────────────────────────────────────────
    # ABA: NOTAS FISCAIS
    # ─────────────────────────────────────────────────────────────────────────

    def _build_notas(self):
        # ── Filtros ───────────────────────────────────────────────────────────
        filtros = ttk.Frame(self.card, style="Card.TFrame")
        filtros.pack(fill="x", pady=(0, 10))

        ttk.Label(filtros, text="🔍 Buscar:",
                  background=CORES['bg_card'], foreground=CORES['text_dark']
                  ).pack(side="left", padx=(0, 5))
        self.busca_var = tk.StringVar()
        self.busca_var.trace_add("write", lambda *_: self._carregar_notas())
        ttk.Entry(filtros, textvariable=self.busca_var, width=26).pack(side="left", padx=(0, 12))

        ttk.Label(filtros, text="Status:",
                  background=CORES['bg_card'], foreground=CORES['text_dark']
                  ).pack(side="left", padx=(0, 5))
        self.status_var = tk.StringVar(value="todos")
        for texto, valor in [("Todos", "todos"), ("Pendentes", "pendente"),
                             ("Ok", "ok"), ("Pagos", "pago")]:
            ttk.Radiobutton(filtros, text=texto, variable=self.status_var, value=valor,
                            command=self._carregar_notas).pack(side="left", padx=3)

        ttk.Button(filtros, text="✖ Limpar", style="Secondary.TButton",
                   command=self._limpar_filtros).pack(side="right")

        filtros2 = ttk.Frame(self.card, style="Card.TFrame")
        filtros2.pack(fill="x", pady=(0, 10))

        ttk.Label(filtros2, text="Emitente:",
                  background=CORES['bg_card'], foreground=CORES['text_dark']
                  ).pack(side="left", padx=(0, 5))
        fornecedores = self.dao.listar_fornecedores_select()
        self._forn_map = {f["nome"]: f["id"] for f in fornecedores}
        opcoes = ["Todos os emitentes"] + [f["nome"] for f in fornecedores]
        valor_inicial = self._emitente_filtro_nome if self._emitente_filtro_nome else "Todos os emitentes"
        self.emitente_var = tk.StringVar(value=valor_inicial)
        combo = ttk.Combobox(filtros2, textvariable=self.emitente_var, values=opcoes,
                             state="readonly", width=28)
        combo.pack(side="left", padx=(0, 16))
        combo.bind("<<ComboboxSelected>>", lambda e: self._carregar_notas())

        ttk.Label(filtros2, text="Período de:",
                  background=CORES['bg_card'], foreground=CORES['text_dark']
                  ).pack(side="left", padx=(0, 5))
        self.data_ini_var = tk.StringVar()
        ttk.Entry(filtros2, textvariable=self.data_ini_var, width=12).pack(side="left", padx=(0, 8))
        ttk.Label(filtros2, text="até:",
                  background=CORES['bg_card'], foreground=CORES['text_dark']
                  ).pack(side="left", padx=(0, 5))
        self.data_fim_var = tk.StringVar()
        ttk.Entry(filtros2, textvariable=self.data_fim_var, width=12).pack(side="left")
        for var in (self.data_ini_var, self.data_fim_var):
            var.trace_add("write", lambda *_: self._carregar_notas())

        # ── Treeview ──────────────────────────────────────────────────────────
        self._criar_treeview(self.card)

        # ── Ações ─────────────────────────────────────────────────────────────
        acoes = ttk.Frame(self.card, style="Card.TFrame")
        acoes.pack(fill="x", pady=(12, 0))

        ttk.Button(acoes, text="✏️ Editar", style="Secondary.TButton",
                   command=self.editar_nota_selecionada).pack(side="left", padx=(0, 6))
        ttk.Button(acoes, text="🗑️ Excluir", style="Danger.TButton",
                   command=self.excluir_nota_selecionada).pack(side="left")

        self.tree.bind("<Double-1>", lambda _e: self.abrir_recibo_selecionado())

        self._carregar_notas()

    def _criar_treeview(self, parent):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "NotasFiscais.Treeview",
            background="white", foreground=CORES['text_dark'],
            rowheight=30, fieldbackground="white",
            font=('Segoe UI', 9), borderwidth=0
        )
        style.configure(
            "NotasFiscais.Treeview.Heading",
            background=CORES['primary'], foreground="white",
            font=('Segoe UI', 9, 'bold'), relief="flat", padding=(8, 8)
        )
        style.map("NotasFiscais.Treeview",
                  background=[("selected", CORES['secondary'])],
                  foreground=[("selected", "white")])

        tree_frame = ttk.Frame(parent, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True)

        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("numero", "emitente", "competencia", "emissao", "valor", "status", "recibos"),
            show="headings", style="NotasFiscais.Treeview",
            selectmode="browse", yscrollcommand=scroll_y.set
        )
        scroll_y.config(command=self.tree.yview)

        cols = [
            ("numero", "Nº NF", 80, "w"),
            ("emitente", "Emitente", 240, "w"),
            ("competencia", "Competência", 100, "w"),
            ("emissao", "Emissão", 100, "w"),
            ("valor", "Valor", 110, "e"),
            ("status", "Status", 110, "center"),
            ("recibos", "👁 Recibos", 80, "center"),
        ]
        for key, label, width, anchor in cols:
            self.tree.heading(key, text=label, anchor="w" if anchor == "w" else anchor)
            self.tree.column(key, width=width, anchor=anchor, stretch=(key == "emitente"))

        self.tree.tag_configure("pago", foreground=CORES['success'])
        self.tree.tag_configure("ok", foreground=CORES['primary'])
        self.tree.tag_configure("pendente", foreground=CORES['warning'])

        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.pack(fill="both", expand=True)

    def _parse_date_filtro(self, s):
        s = (s or "").strip()
        if not s:
            return None
        try:
            return datetime.strptime(s, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return None

    def _carregar_notas(self):
        if not hasattr(self, "tree"):
            return

        emitente_sel = self.emitente_var.get()
        emitente_id = None
        if emitente_sel and emitente_sel != "Todos os emitentes":
            emitente_id = self._forn_map.get(emitente_sel)
        elif self._emitente_filtro_id:
            emitente_id = self._emitente_filtro_id

        busca = self.busca_var.get().strip()
        status = self.status_var.get()
        filtro_status = None if status == "todos" else status
        data_ini = self._parse_date_filtro(self.data_ini_var.get())
        data_fim = self._parse_date_filtro(self.data_fim_var.get())

        notas = self.dao.listar_notas(
            filtro_status=filtro_status, busca=busca or None,
            emitente_id=emitente_id, data_ini=data_ini, data_fim=data_fim
        )

        self._update_stats(emitente_id, busca, data_ini, data_fim)

        self.tree.delete(*self.tree.get_children())
        for nota in notas:
            pago = bool(nota["pago"])
            qtd = nota.get("qtd_recibos", 0)
            if pago:
                status_key, status_txt = "pago", "✅ Pago"
            elif qtd:
                status_key, status_txt = "ok", "📎 Ok"
            else:
                status_key, status_txt = "pendente", "⏳ Pendente"

            self.tree.insert("", "end", iid=str(nota["id"]), tags=(status_key,), values=(
                nota["numero"], nota["emitente"], nota["competencia"],
                _fmt_data_br(nota["data_emissao"]), _fmt_brl(nota["valor"]),
                status_txt, f"👁 {qtd}" if qtd else "—"
            ))

    def _on_tree_click(self, event):
        """Clique na coluna 'Recibos' abre direto o último recibo anexado,
        sem precisar passar pelo diálogo de Recibo/Pagamento."""
        if self.tree.identify_region(event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#7":
            return
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        recibos = self.dao.listar_recibos(int(row_id))
        if not recibos:
            return
        arquivo = recibos[0]["arquivo"]
        if os.path.exists(arquivo):
            _abrir_arquivo(arquivo)
        else:
            messagebox.showwarning("Arquivo não encontrado",
                                   "O arquivo do recibo não foi encontrado no disco.")

    def _update_stats(self, emitente_id=None, busca=None, data_ini=None, data_fim=None):
        for w in self.stats_frame.winfo_children():
            w.destroy()

        if emitente_id or busca or data_ini or data_fim:
            notas = self.dao.listar_notas(emitente_id=emitente_id, busca=busca or None,
                                          data_ini=data_ini, data_fim=data_fim)
            total = len(notas)
            pendentes = sum(1 for n in notas if not n["pago"] and not n.get("qtd_recibos"))
            ok = sum(1 for n in notas if not n["pago"] and n.get("qtd_recibos"))
            pagos = sum(1 for n in notas if n["pago"])
            val_pend = sum(n["valor"] for n in notas if not n["pago"] and not n.get("qtd_recibos"))
            val_ok = sum(n["valor"] for n in notas if not n["pago"] and n.get("qtd_recibos"))
            val_pago = sum(n["valor"] for n in notas if n["pago"])
        else:
            s = self.dao.get_stats()
            total = s["total"] or 0
            pendentes = s["pendentes"] or 0
            ok = s["ok"] or 0
            pagos = s["pagos"] or 0
            val_pend = s["valor_pendente"] or 0
            val_ok = s["valor_ok"] or 0
            val_pago = s["valor_pago"] or 0

        cards = [
            ("Total de NFs", str(total), CORES['primary']),
            ("Pendentes", str(pendentes), CORES['warning']),
            ("Ok", str(ok), CORES['primary']),
            ("Pagas", str(pagos), CORES['success']),
            ("Valor Pendente", _fmt_brl(val_pend), CORES['danger']),
            ("Valor Ok", _fmt_brl(val_ok), CORES['primary']),
            ("Valor Pago", _fmt_brl(val_pago), CORES['success']),
        ]
        for label, value, color in cards:
            card = ttk.Frame(self.stats_frame, style="Card.TFrame",
                             relief="solid", borderwidth=1)
            card.pack(side="left", padx=(0, 10), fill="y")
            inner = ttk.Frame(card, style="Card.TFrame")
            inner.pack(padx=16, pady=10)
            ttk.Label(inner, text=label, font=('Segoe UI', 8),
                      background=CORES['bg_card'], foreground=CORES['text_light']).pack(anchor="w")
            ttk.Label(inner, text=value, font=('Segoe UI', 14, 'bold'),
                      background=CORES['bg_card'], foreground=color).pack(anchor="w")

    def _limpar_filtros(self):
        self._emitente_filtro_id = None
        self._emitente_filtro_nome = None
        self.emitente_var.set("Todos os emitentes")
        self.busca_var.set("")
        self.status_var.set("todos")
        self.data_ini_var.set("")
        self.data_fim_var.set("")
        self._carregar_notas()

    def _nota_selecionada(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione uma nota fiscal na lista.")
            return None
        return int(sel[0])

    # ─────────────────────────────────────────────────────────────────────────
    # AÇÕES
    # ─────────────────────────────────────────────────────────────────────────

    def nova_nota(self):
        NotaFiscalFormDialog(self.parent_frame, self.dao, on_save=self._on_nota_salva)

    def editar_nota_selecionada(self):
        nota_id = self._nota_selecionada()
        if nota_id is None:
            return
        NotaFiscalFormDialog(self.parent_frame, self.dao, nota_id=nota_id, on_save=self._on_nota_salva)

    def abrir_recibo_selecionado(self):
        nota_id = self._nota_selecionada()
        if nota_id is None:
            return
        ReciboNotaDialog(self.parent_frame, self.dao, nota_id, self.recibos_dir,
                         on_close=self._carregar_notas)

    def excluir_nota_selecionada(self):
        nota_id = self._nota_selecionada()
        if nota_id is None:
            return
        nota = self.dao.get_nota(nota_id)
        numero = nota["numero"] if nota else ""
        if messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja excluir a nota fiscal Nº {numero}?\n\nEsta ação não pode ser desfeita.",
            icon="warning"
        ):
            self.dao.excluir_nota(nota_id)
            self._carregar_notas()

    def abrir_importacao_lote(self):
        ImportacaoLoteNFDialog(self.parent_frame, self.dao, on_concluido=self._on_nota_salva)

    def abrir_relatorio(self):
        from telas.tela_relatorio_notas_fiscais import TelaRelatorioNotasFiscais
        TelaRelatorioNotasFiscais(self.parent_frame)

    def _on_nota_salva(self):
        self.dao.importar_emitentes_das_notas()
        if self._aba_atual == "notas":
            self._mostrar_aba("notas")
