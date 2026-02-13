import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from dao.producao_dao import ProducaoDAO
from telas.tela_nova_producao import TelaNovaProducao
from telas.tela_detalhes_producao import TelaDetalhesProducao
from services.recibo_producao_service import ReciboProducaoService
from telas.tela_relatorio_producoes import TelaRelatorioProducoes
from utils.constantes import CORES
from utils.auxiliares import resource_path
from PIL import Image, ImageTk


def formatar_data_br(data):
    if not data:
        return None
    if isinstance(data, (datetime, date)):
        return data.strftime("%d-%m-%Y")
    return datetime.strptime(data, "%Y-%m-%d").strftime("%d-%m-%Y")


class ProducoesPrincipalEmbed:
    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.dao = ProducaoDAO()
        self.recibo_producao_service = ReciboProducaoService(self.dao)

        # Guarda todas as produções carregadas para filtragem local
        self._producoes_cache = []

        self.criar_interface()
        self.carregar_producoes()

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
            caminho_icone = resource_path("Icones/producao_azul.png")
            img = Image.open(caminho_icone).resize((32, 32), Image.LANCZOS)
            self.icon_header = ImageTk.PhotoImage(img)
            ttk.Label(left_header, image=self.icon_header,
                      background=CORES['bg_main']).pack(side="left", padx=(0, 15))
        except Exception:
            pass

        title_frame = ttk.Frame(left_header, style='Main.TFrame')
        title_frame.pack(side="left")

        ttk.Label(title_frame, text="Gestão de Produções",
                  font=('Segoe UI', 18, 'bold'),
                  background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(anchor="w")

        ttk.Label(title_frame,
                  text="Controle de produções e pagamentos por sacos produzidos",
                  font=('Segoe UI', 9),
                  background=CORES['bg_main'],
                  foreground=CORES['text_light']).pack(anchor="w")

        right_header = ttk.Frame(header_frame, style='Main.TFrame')
        right_header.pack(side="right")

        ttk.Button(right_header, text="➕ Nova Produção",
                   style="Primary.TButton",
                   command=self.nova_producao).pack(side="left", padx=5)
        
        ttk.Button(right_header, text="📊 Relatório",
                   style="Add.TButton",
                   command=self.abrir_relatorio).pack(side="left", padx=5)

        ttk.Button(right_header, text="🔄 Atualizar",
                   style="Secondary.TButton",
                   command=self.carregar_producoes).pack(side="left", padx=5)

        

        # ── Card principal ────────────────────────────────────────────────────
        card = ttk.Frame(main_frame, style="Card.TFrame", padding=25)
        card.pack(fill="both", expand=True)

        # ── Barra de filtros ──────────────────────────────────────────────────
        filtros_frame = ttk.Frame(card, style="Card.TFrame")
        filtros_frame.pack(fill="x", pady=(0, 15))

        # --- Status ---
        ttk.Label(filtros_frame, text="Status:",
                  font=('Segoe UI', 10),
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(side="left", padx=(0, 8))

        self.filtro_var = tk.StringVar(value="todas")
        for texto, valor in [("Todas", "todas"), ("Abertas", "abertas"), ("Fechadas", "fechadas")]:
            ttk.Radiobutton(filtros_frame, text=texto,
                            variable=self.filtro_var, value=valor,
                            command=self.aplicar_filtros).pack(side="left", padx=4)

        # Separador vertical
        ttk.Separator(filtros_frame, orient="vertical").pack(
            side="left", fill="y", padx=15, pady=2)

        # --- Busca por nome ---
        ttk.Label(filtros_frame, text="🔍 Nome:",
                  font=('Segoe UI', 10),
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(side="left", padx=(0, 5))

        self.busca_nome_var = tk.StringVar()
        self.busca_nome_var.trace_add("write", lambda *_: self.aplicar_filtros())
        entry_nome = ttk.Entry(filtros_frame, textvariable=self.busca_nome_var, width=22)
        entry_nome.pack(side="left", padx=(0, 15))

        # --- Busca por data de início ---
        ttk.Label(filtros_frame, text="📅 Data início:",
                  font=('Segoe UI', 10),
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(side="left", padx=(0, 5))

        self.busca_data_var = tk.StringVar()
        self.busca_data_var.trace_add("write", lambda *_: self.aplicar_filtros())
        entry_data = ttk.Entry(filtros_frame, textvariable=self.busca_data_var, width=13)
        entry_data.pack(side="left", padx=(0, 5))
        ttk.Label(filtros_frame, text="(DD-MM-AAAA)",
                  font=('Segoe UI', 8),
                  background=CORES['bg_card'],
                  foreground=CORES['text_light']).pack(side="left")

        # Botão limpar filtros
        ttk.Button(filtros_frame, text="✖ Limpar",
                   style="Secondary.TButton",
                   command=self.limpar_filtros).pack(side="right")

        # ── Contador de resultados ────────────────────────────────────────────
        self.label_total = ttk.Label(card, text="",
                                     font=('Segoe UI', 9),
                                     background=CORES['bg_card'],
                                     foreground=CORES['text_light'])
        self.label_total.pack(anchor="w", pady=(0, 8))

        # ── Estilo do Treeview ────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use('clam')

        style.configure(
            "Producoes.Treeview",
            background="white",
            foreground=CORES['text_dark'],
            rowheight=32,
            fieldbackground="white",
            font=('Segoe UI', 9),
            borderwidth=0
        )
        style.configure(
            "Producoes.Treeview.Heading",
            background=CORES['primary'],
            foreground="white",
            font=('Segoe UI', 9, 'bold'),
            relief="flat",
            padding=(10, 8)
        )
        style.map(
            "Producoes.Treeview",
            background=[("selected", CORES['secondary'])],
            foreground=[("selected", "white")]
        )
        style.map(
            "Producoes.Treeview.Heading",
            background=[("active", CORES['primary'])]
        )

        # ── Treeview ──────────────────────────────────────────────────────────
        tree_frame = ttk.Frame(card, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True)

        colunas = ("nome", "status", "data_inicio", "data_fim", "total_sacos", "valor_total")

        # Scrollbars
        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        scroll_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=colunas,
            show="headings",
            style="Producoes.Treeview",
            selectmode="browse",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        # Cabeçalhos
        self.tree.heading("nome",        text="Nome da Produção", anchor="w",
                          command=lambda: self._ordenar("nome"))
        self.tree.heading("status",      text="Status",           anchor="w",
                          command=lambda: self._ordenar("status"))
        self.tree.heading("data_inicio", text="Data Início",      anchor="w",
                          command=lambda: self._ordenar("data_inicio"))
        self.tree.heading("data_fim",    text="Data Fim",         anchor="w",
                          command=lambda: self._ordenar("data_fim"))
        self.tree.heading("total_sacos", text="Total Sacos",      anchor="w",
                          command=lambda: self._ordenar("total_sacos"))
        self.tree.heading("valor_total", text="Valor Total (R$)", anchor="e",
                          command=lambda: self._ordenar("valor_total"))

        # Larguras
        self.tree.column("nome",        width=220, minwidth=140, stretch=True,  anchor="w")
        self.tree.column("status",      width=110, minwidth=80,  stretch=False, anchor="w")
        self.tree.column("data_inicio", width=110, minwidth=90,  stretch=False, anchor="w")
        self.tree.column("data_fim",    width=110, minwidth=90,  stretch=False, anchor="w")
        self.tree.column("total_sacos", width=110, minwidth=80,  stretch=False, anchor="w")
        self.tree.column("valor_total", width=140, minwidth=100, stretch=False, anchor="e")

        # Tags zebra (sem cores por status para manter consistência visual)
        self.tree.tag_configure("par",   background="#f8f9fa")
        self.tree.tag_configure("impar", background="white")

        self.tree.pack(fill="both", expand=True)

        # ── Barra de ações (rodapé) ───────────────────────────────────────────
        acoes_frame = ttk.Frame(card, style="Card.TFrame")
        acoes_frame.pack(fill="x", pady=(12, 0))

        ttk.Button(acoes_frame, text="📄 Gerar Recibo",
                   style="Primary.TButton",
                   command=self._acao_recibo).pack(side="left", padx=(0, 6))

        ttk.Button(acoes_frame, text="🗑️ Excluir",
                   style="Danger.TButton",
                   command=self._acao_excluir).pack(side="left")

        # Duplo clique abre detalhes
        self.tree.bind("<Double-1>", lambda _e: self._acao_detalhes())

        # Controle de ordenação
        self._ordem_coluna = None
        self._ordem_reversa = False

    # ─────────────────────────────────────────────────────────────────────────
    # CARREGAMENTO / FILTRAGEM
    # ─────────────────────────────────────────────────────────────────────────

    def carregar_producoes(self):
        """Busca todos os dados do DAO e armazena no cache, depois filtra."""
        self._producoes_cache = self.dao.listar_producoes()
        self.aplicar_filtros()

    def aplicar_filtros(self):
        """Filtra o cache em memória e atualiza a Treeview."""
        filtro_status = self.filtro_var.get()
        termo_nome   = self.busca_nome_var.get().strip().lower()
        termo_data   = self.busca_data_var.get().strip()

        resultado = []
        for p in self._producoes_cache:
            # Filtro de status
            if filtro_status == "abertas"  and p['status'] != 'aberta':
                continue
            if filtro_status == "fechadas" and p['status'] != 'fechada':
                continue

            # Filtro por nome (case-insensitive, parcial)
            if termo_nome and termo_nome not in p['nome'].lower():
                continue

            # Filtro por data de início (parcial: "04-2025" encontra "10-04-2025")
            if termo_data:
                data_br = formatar_data_br(p['data_inicio']) or ""
                if termo_data not in data_br:
                    continue

            resultado.append(p)

        self._popular_tree(resultado)

    def _popular_tree(self, producoes):
        """Limpa e repovoa a Treeview com a lista fornecida."""
        # Salva id selecionado para restaurar após refresh
        selecionado = self._id_selecionado()

        self.tree.delete(*self.tree.get_children())

        for i, p in enumerate(producoes):
            data_fim_br = formatar_data_br(p['data_fim']) or "—"
            tag_zebra = "par" if i % 2 == 0 else "impar"

            iid = str(p['id'])
            self.tree.insert(
                "", "end", iid=iid,
                values=(
                    p['nome'],
                    "✅ Aberta" if p['status'] == 'aberta' else "🔒 Fechada",
                    formatar_data_br(p['data_inicio']) or "—",
                    data_fim_br,
                    p['total_sacos'],
                    f"{p['valor_total']:.2f}",
                ),
                tags=(tag_zebra,)
            )

        # Restaura seleção se ainda existir
        if selecionado and self.tree.exists(selecionado):
            self.tree.selection_set(selecionado)
            self.tree.see(selecionado)

        total = len(producoes)
        self.label_total.config(
            text=f"{total} produção{'ões' if total != 1 else ''} encontrada{'s' if total != 1 else ''}"
        )

    def limpar_filtros(self):
        self.filtro_var.set("todas")
        self.busca_nome_var.set("")
        self.busca_data_var.set("")
        self.aplicar_filtros()

    # ─────────────────────────────────────────────────────────────────────────
    # ORDENAÇÃO
    # ─────────────────────────────────────────────────────────────────────────

    def _ordenar(self, coluna):
        """Ordena a Treeview pela coluna clicada (toggle asc/desc)."""
        if self._ordem_coluna == coluna:
            self._ordem_reversa = not self._ordem_reversa
        else:
            self._ordem_coluna = coluna
            self._ordem_reversa = False

        indices_col = {
            "nome": 0, "status": 1, "data_inicio": 2,
            "data_fim": 3, "total_sacos": 4, "valor_total": 5
        }
        col_idx = indices_col[coluna]

        itens = [(self.tree.set(k, coluna), k) for k in self.tree.get_children("")]

        # Conversão numérica onde aplicável
        def chave(item):
            v = item[0]
            if coluna in ("total_sacos", "valor_total"):
                try:
                    return float(v.replace(",", "."))
                except ValueError:
                    return 0.0
            # Data no formato DD-MM-AAAA → converte para AAAA-MM-DD para ordenar
            if coluna in ("data_inicio", "data_fim") and v and v != "—":
                partes = v.split("-")
                if len(partes) == 3:
                    return f"{partes[2]}-{partes[1]}-{partes[0]}"
            return v.lower()

        itens.sort(key=chave, reverse=self._ordem_reversa)

        for index, (_, k) in enumerate(itens):
            self.tree.move(k, "", index)
            # Re-aplica zebra
            tag_zebra = "par" if index % 2 == 0 else "impar"
            self.tree.item(k, tags=(tag_zebra,))

        # Indicador visual no cabeçalho
        seta = " ▲" if not self._ordem_reversa else " ▼"
        for c in ("nome", "status", "data_inicio", "data_fim", "total_sacos", "valor_total"):
            textos = {
                "nome": "Nome da Produção", "status": "Status",
                "data_inicio": "Data Início", "data_fim": "Data Fim",
                "total_sacos": "Total Sacos", "valor_total": "Valor Total (R$)"
            }
            self.tree.heading(c, text=textos[c] + (seta if c == coluna else ""))

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _id_selecionado(self):
        """Retorna o iid (= id da produção como str) da linha selecionada, ou None."""
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _producao_selecionada(self):
        """Retorna o id (int) da produção selecionada ou None."""
        iid = self._id_selecionado()
        return int(iid) if iid else None

    def _producao_dados(self):
        """Retorna dict da produção selecionada do cache, ou None."""
        pid = self._producao_selecionada()
        if pid is None:
            return None
        return next((p for p in self._producoes_cache if p['id'] == pid), None)

    # ─────────────────────────────────────────────────────────────────────────
    # AÇÕES DA BARRA DE RODAPÉ
    # ─────────────────────────────────────────────────────────────────────────

    def _acao_detalhes(self):
        pid = self._producao_selecionada()
        if pid is None:
            messagebox.showwarning("Atenção", "Selecione uma produção na lista.")
            return
        self.ver_detalhes(pid)

    def _acao_recibo(self):
        dados = self._producao_dados()
        if dados is None:
            messagebox.showwarning("Atenção", "Selecione uma produção na lista.")
            return
        if dados['status'] != 'fechada':
            messagebox.showwarning("Atenção",
                                   "O recibo só está disponível para produções fechadas.")
            return
        self.gerar_recibo(dados['id'])

    def _acao_excluir(self):
        dados = self._producao_dados()
        if dados is None:
            messagebox.showwarning("Atenção", "Selecione uma produção na lista.")
            return
        self.excluir_producao(dados['id'], dados['nome'])

    # ─────────────────────────────────────────────────────────────────────────
    # NAVEGAÇÃO / OPERAÇÕES (mantidas idênticas ao original)
    # ─────────────────────────────────────────────────────────────────────────

    def abrir_relatorio(self):
        TelaRelatorioProducoes(self.parent_frame)

    def nova_producao(self):
        TelaNovaProducao(self.parent_frame, self.carregar_producoes)

    def ver_detalhes(self, producao_id):
        self.sistema_fiscal.limpar_content_area()
        TelaDetalhesProducao(self.sistema_fiscal.content_area,
                             producao_id, self.voltar_para_lista)

    def voltar_para_lista(self):
        self.sistema_fiscal.limpar_content_area()
        ProducoesPrincipalEmbed(self.sistema_fiscal.content_area, self.sistema_fiscal)

    def gerar_recibo(self, producao_id):
        try:
            arquivo = self.recibo_producao_service.gerar_recibo_geral(
                producao_id, salvar=False, abrir=True)
            if not arquivo:
                return
            messagebox.showinfo("Sucesso", "Recibo gerado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar recibo: {str(e)}")

    def excluir_producao(self, producao_id, producao_nome):
        resposta = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a produção '{producao_nome}'?\n\n"
            "⚠️ ATENÇÃO: Esta ação NÃO pode ser desfeita!\n\n"
            "Serão excluídos:\n"
            "• Todos os dias de produção\n"
            "• Todas as divisões e participantes\n"
            "• Todos os totais calculados\n\n"
            "Deseja continuar?"
        )
        if resposta:
            if self.dao.excluir_producao(producao_id):
                messagebox.showinfo("Sucesso",
                                    f"Produção '{producao_nome}' excluída com sucesso!")
                self.carregar_producoes()
            else:
                messagebox.showerror("Erro",
                                     "Erro ao excluir a produção. Tente novamente.")