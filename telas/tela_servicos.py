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
        return data.strftime("%d-%m-%Y")

    return datetime.strptime(data, "%Y-%m-%d").strftime("%d-%m-%Y")

class ServicosEmbed:
    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.dao = ServicoDAO()
        self.diarista_dao = DiaristaDAO()
        self.centro_custo_dao = CentroCustoDAO()
        
        self.criar_interface()
        self.carregar_servicos()
    
    def criar_interface(self):
        # Frame principal
        main_frame = ttk.Frame(self.parent_frame, style='Main.TFrame')
        main_frame.pack(fill="both", expand=True, padx=50, pady=30)
        
        # Header
        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.pack(fill="x", pady=(0, 20))
        
        header_container = ttk.Frame(header_frame, style='Main.TFrame')
        header_container.pack(fill="x")
        
        # Ícone e título
        left_header = ttk.Frame(header_container, style='Main.TFrame')
        left_header.pack(side="left")
        
        # ÍCONE DO HEADER
        try:
            caminho_icone = resource_path("Icones/servicos_azul.png")
            img = Image.open(caminho_icone)
            img = img.resize((32, 32), Image.LANCZOS)
            self.icon_header = ImageTk.PhotoImage(img)
            
            ttk.Label(
                left_header,
                image=self.icon_header,
                background=CORES['bg_main']
            ).pack(side="left", padx=(0, 15))
        except:
            pass
        
        title_frame = ttk.Frame(left_header, style='Main.TFrame')
        title_frame.pack(side="left")
        
        ttk.Label(
            title_frame,
            text="Emissão de Serviços",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")
        
        ttk.Label(
            title_frame,
            text="Registro e emissão de recibos de serviços prestados",
            font=('Segoe UI', 9),
            background=CORES['bg_main'],
            foreground=CORES['text_light']
        ).pack(anchor="w")
        
        # Botões do header
        right_header = ttk.Frame(header_container, style='Main.TFrame')
        right_header.pack(side="right")
        
        ttk.Button(
            right_header,
            text="➕ Novo Serviço",
            style="Primary.TButton",
            command=self.novo_servico
        ).pack(side="left", padx=5)
        
        ttk.Button(
            right_header,
            text="🔄 Atualizar",
            style="Secondary.TButton",
            command=self.carregar_servicos
        ).pack(side="left", padx=5)
        
        # Card principal
        card = ttk.Frame(main_frame, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)
        
        # Filtros
        filtro_frame = ttk.Frame(card, style="Card.TFrame")
        filtro_frame.pack(fill="x", pady=(0, 15))
        
        # Linha 1 - Busca
        busca_frame = ttk.Frame(filtro_frame, style="Card.TFrame")
        busca_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            busca_frame,
            text="🔍 Buscar:",
            font=('Segoe UI', 10),
            background=CORES['bg_card'],
            foreground=CORES['text_dark']
        ).pack(side="left", padx=(0, 10))
        
        self.var_busca = tk.StringVar()
        self.var_busca.trace('w', lambda *args: self.carregar_servicos())
        
        entry_busca = ttk.Entry(
            busca_frame,
            textvariable=self.var_busca,
            font=('Segoe UI', 10),
            width=40
        )
        entry_busca.pack(side="left", fill="x", expand=True)
        
        ttk.Label(
            busca_frame,
            text="(Nome ou CPF do diarista)",
            font=('Segoe UI', 8, 'italic'),
            background=CORES['bg_card'],
            foreground=CORES['text_light']
        ).pack(side="left", padx=(10, 0))
        
        # Linha 2 - Período
        periodo_frame = ttk.Frame(filtro_frame, style="Card.TFrame")
        periodo_frame.pack(fill="x")
        
        ttk.Label(
            periodo_frame,
            text="📅 Período:",
            font=('Segoe UI', 10),
            background=CORES['bg_card'],
            foreground=CORES['text_dark']
        ).pack(side="left", padx=(0, 10))
        
        self.combo_periodo = ttk.Combobox(
            periodo_frame,
            values=["Todos", "Hoje", "Última Semana", "Último Mês"],
            state="readonly",
            width=18
        )
        self.combo_periodo.set("Todos")
        self.combo_periodo.pack(side="left", padx=5)
        self.combo_periodo.bind("<<ComboboxSelected>>", lambda e: self.carregar_servicos())
        
        # Frame para a tabela
        tabela_container = tk.Frame(card, bg=CORES['bg_card'])
        tabela_container.pack(fill="both", expand=True)

        # Estilo do Treeview
        style = ttk.Style()
        style.theme_use('clam')

        style.configure(
            "Servicos.Treeview",
            background="white",
            foreground=CORES['text_dark'],
            rowheight=32,
            fieldbackground="white",
            font=('Segoe UI', 9),
            borderwidth=0
        )
        style.configure(
            "Servicos.Treeview.Heading",
            background=CORES['primary'],
            foreground="white",
            font=('Segoe UI', 9, 'bold'),
            relief="flat",
            padding=(10, 8)
        )
        style.map(
            "Servicos.Treeview",
            background=[("selected", CORES['secondary'])],
            foreground=[("selected", "white")]
        )
        style.map(
            "Servicos.Treeview.Heading",
            background=[("active", CORES['primary'])]
        )

        # Scrollbars
        scroll_y = ttk.Scrollbar(tabela_container, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        scroll_x = ttk.Scrollbar(tabela_container, orient="horizontal")
        scroll_x.pack(side="bottom", fill="x")

        # Treeview
        colunas = ("data", "diarista", "centro_custo", "descricao", "valor")
        self.tree = ttk.Treeview(
            tabela_container,
            columns=colunas,
            show="headings",
            style="Servicos.Treeview",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        # Cabeçalhos
        self.tree.heading("data",         text="Data",            anchor="w")
        self.tree.heading("diarista",     text="Diarista",        anchor="w")
        self.tree.heading("centro_custo", text="Centro de Custo", anchor="w")
        self.tree.heading("descricao",    text="Descrição",       anchor="w")
        self.tree.heading("valor",        text="Valor",           anchor="e")

        # Larguras das colunas
        self.tree.column("data",         width=100, minwidth=90,  stretch=False)
        self.tree.column("diarista",     width=180, minwidth=140, stretch=False)
        self.tree.column("centro_custo", width=160, minwidth=120, stretch=False)
        self.tree.column("descricao",    width=250, minwidth=150, stretch=True)
        self.tree.column("valor",        width=110, minwidth=90,  stretch=False, anchor="e")

        # Zebra
        self.tree.tag_configure("par",   background="#f8f9fa")
        self.tree.tag_configure("impar", background="white")

        self.tree.pack(fill="both", expand=True)

        # Duplo clique → abre recibo
        self.tree.bind("<Double-1>", self._on_duplo_clique)

        # Armazena dados dos serviços para ações
        self._servicos_map = {}

        # Painel de ações abaixo da tabela
        acoes_frame = tk.Frame(card, bg=CORES['bg_card'])
        acoes_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            acoes_frame,
            text="📄 Recibo",
            style="Primary.TButton",
            command=lambda: self._acao("recibo")
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            acoes_frame,
            text="✏️ Editar",
            style="Secondary.TButton",
            command=lambda: self._acao("editar")
        ).pack(side="left", padx=5)

        ttk.Button(
            acoes_frame,
            text="🗑️ Excluir",
            style="Danger.TButton",
            command=lambda: self._acao("excluir")
        ).pack(side="left", padx=5)

        ttk.Label(
            acoes_frame,
            text="Selecione uma linha • Duplo clique para abrir o recibo",
            font=('Segoe UI', 8, 'italic'),
            background=CORES['bg_card'],
            foreground=CORES['text_light']
        ).pack(side="right")
    
    def get_filtro_periodo(self):
        """Retorna as datas de filtro baseado no período selecionado"""
        periodo = self.combo_periodo.get()
        hoje = datetime.now()
        
        if periodo == "Hoje":
            data_inicio = hoje.strftime('%Y-%m-%d')
            data_fim = hoje.strftime('%Y-%m-%d')
        elif periodo == "Última Semana":
            data_inicio = (hoje - timedelta(days=7)).strftime('%Y-%m-%d')
            data_fim = hoje.strftime('%Y-%m-%d')
        elif periodo == "Último Mês":
            data_inicio = (hoje - timedelta(days=30)).strftime('%Y-%m-%d')
            data_fim = hoje.strftime('%Y-%m-%d')
        else:  # Todos
            data_inicio = None
            data_fim = None
        
        return data_inicio, data_fim
    
    def carregar_servicos(self):
        # Limpa treeview e mapa
        self.tree.delete(*self.tree.get_children())
        self._servicos_map.clear()

        # Filtros
        data_inicio, data_fim = self.get_filtro_periodo()
        servicos = self.dao.listar(
            filtro_data_inicio=data_inicio,
            filtro_data_fim=data_fim
        )

        # Filtro de busca por nome/CPF
        termo = self.var_busca.get().lower().strip()
        if termo:
            servicos = [
                s for s in servicos
                if termo in s[2].lower() or termo in s[3]
            ]

        if not servicos:
            self.tree.insert(
                "", "end",
                values=("—", "Nenhum serviço encontrado", "—", "—", "—"),
                tags=("impar",)
            )
            return

        for i, servico in enumerate(servicos):
            tag = "par" if i % 2 == 0 else "impar"
            
            valor_fmt = (
                f"R$ {servico[5]:,.2f}"
                .replace(',', 'X').replace('.', ',').replace('X', '.')
            )
            iid = self.tree.insert(
                "", "end",
                values=(
                    servico[1],   # data
                    servico[2],   # diarista
                    servico[4],   # centro de custo
                    servico[6],   # descrição
                    valor_fmt     # valor
                ),
                tags=(tag,)
            )
            self._servicos_map[iid] = servico
    
    def _acao(self, tipo):
        """Executa ação sobre a linha selecionada no treeview"""
        servico = self._get_servico_selecionado()
        if not servico:
            messagebox.showwarning("Atenção", "Selecione um serviço na tabela!")
            return

        if tipo == "recibo":
            self.exibir_recibo(servico)
        elif tipo == "editar":
            self.editar_servico(servico[0])
        elif tipo == "excluir":
            self.excluir_servico(servico[0], servico[2])

    def _on_duplo_clique(self, event):
        iid = self.tree.focus()
        if iid and iid in self._servicos_map:
            self.exibir_recibo(self._servicos_map[iid])

    def _get_servico_selecionado(self):
        iid = self.tree.focus()
        return self._servicos_map.get(iid)
    
    def criar_linha_servico(self, servico):
        """Linha da tabela usando grid — alinhada com o cabeçalho"""
        # servico: (id, data, diarista_nome, diarista_cpf, centro_custo,
        #           valor, descricao, observacoes, diarista_id, centro_custo_id)

        bg = 'white'

        linha = tk.Frame(self.scroll_frame, bg=bg, relief='solid', bd=0,
                         highlightbackground=CORES['border'], highlightthickness=1)
        linha.pack(fill="x", pady=0)

        # Mesmas configurações de coluna que o cabeçalho
        for col, (_, largura, peso) in enumerate(self.COLUNAS):
            linha.grid_columnconfigure(col, minsize=largura, weight=peso)
        
        valor_formatado = (
            f"R$ {servico[5]:,.2f}"
            .replace(',', 'X').replace('.', ',').replace('X', '.')
        )

        celulas = [
            (servico[1],        'w', CORES['text_dark'],  False),
            (servico[2],        'w', CORES['text_dark'],  False),
            (servico[4],        'w', CORES['text_dark'],  False),
            (servico[6],        'w', CORES['text_light'], False),
            (valor_formatado,   'e', CORES['success'],    True),
        ]

        labels = []
        for col, (texto, ancora, cor, negrito) in enumerate(celulas):
            lbl = tk.Label(
                linha,
                text=texto,
                font=('Segoe UI', 9, 'bold' if negrito else 'normal'),
                bg=bg,
                fg=cor,
                anchor=ancora,
                padx=10,
                pady=7
            )
            lbl.grid(row=0, column=col, sticky="nsew")
            labels.append(lbl)

        # Célula de ações
        btn_frame = tk.Frame(linha, bg=bg)
        btn_frame.grid(row=0, column=5, sticky="nsew", padx=5, pady=4)

        for texto, cor, cmd in [
            ("📄", CORES['primary'],  lambda s=servico: self.exibir_recibo(s)),
            ("✏️", CORES['secondary'], lambda s=servico: self.editar_servico(s[0])),
            ("🗑️", CORES['danger'],   lambda s=servico: self.excluir_servico(s[0], s[2])),
        ]:
            tk.Button(
                btn_frame,
                text=texto,
                font=('Segoe UI', 9),
                bg=cor,
                fg='white',
                relief='flat',
                cursor='hand2',
                padx=7,
                pady=1,
                command=cmd
            ).pack(side="left", padx=2)

        # Hover
        todos = [linha, btn_frame] + labels

        def on_enter(e):
            for w in todos:
                w.config(bg=CORES['bg_hover'])

        def on_leave(e):
            for w in todos:
                w.config(bg=bg)

        for w in [linha] + labels:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
    
    def novo_servico(self):
        TelaNovoServico(self.parent_frame, self.carregar_servicos)
    
    def editar_servico(self, servico_id):
        TelaNovoServico(self.parent_frame, self.carregar_servicos, servico_id)
    
    def exibir_recibo(self, servico_dados):
        """Gera e abre o recibo temporário em PDF"""
        try:
            arquivo = ReciboServicoService.gerar_recibo_temporario(servico_dados)
            # O arquivo já é aberto automaticamente no service
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar recibo: {str(e)}")
    
    def excluir_servico(self, servico_id, diarista_nome):
        """Exclui um serviço após confirmação"""
        resposta = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o serviço de '{diarista_nome}'?\n\n"
            "Esta ação não pode ser desfeita!"
        )
        
        if resposta:
            if self.dao.excluir(servico_id):
                messagebox.showinfo("Sucesso", "Serviço excluído com sucesso!")
                self.carregar_servicos()
            else:
                messagebox.showerror("Erro", "Erro ao excluir serviço!")