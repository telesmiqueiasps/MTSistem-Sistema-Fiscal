import tkinter as tk
from tkinter import ttk, messagebox
import os
from dao.diaria_dao import DiariaDAO
from telas.tela_emitir_diaria import TelaEmitirDiaria
from utils.auxiliares import CORES, resource_path
from PIL import Image, ImageTk 
from datetime import datetime, timedelta


class DiariasEmitidasEmbed:
    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.dao = DiariaDAO()

        self.criar_interface()
        self.atualizar_lista()

    def criar_interface(self):
        for w in self.parent_frame.winfo_children():
            w.destroy()

        # Frame principal
        main_frame = ttk.Frame(self.parent_frame, style='Main.TFrame')
        main_frame.pack(fill="both", expand=True, padx=50, pady=30)

        # Header
        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.pack(fill="x", pady=(0, 30))

        header_container = ttk.Frame(header_frame, style='Main.TFrame')
        header_container.pack(fill="x")

        # Ícone e título
        left_header = ttk.Frame(header_container, style='Main.TFrame')
        left_header.pack(side="left")

        right_header = ttk.Frame(header_container, style='Main.TFrame')
        right_header.pack(side="right")

        caminho_icone = resource_path("Icones/diarias_azul.png")
        img = Image.open(caminho_icone)
        img = img.resize((40, 40), Image.LANCZOS)
        self.icon_header = ImageTk.PhotoImage(img)

        ttk.Label(
            left_header,
            image=self.icon_header,
            background=CORES['bg_main']
        ).pack(side="left", padx=(0, 15))

        title_frame = ttk.Frame(left_header, style='Main.TFrame')
        title_frame.pack(side="left")

        ttk.Label(
            title_frame,
            text="Diarias Emitidas",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")

        ttk.Label(
            title_frame,
            text="Gestão e emissão de diárias",
            font=('Segoe UI', 9),
            background=CORES['bg_main'],
            foreground=CORES['text_light']
        ).pack(anchor="w")    

        buttons_frame = ttk.Frame(right_header, style='Main.TFrame')
        buttons_frame.pack(side="left")

        ttk.Button(
            buttons_frame,
            text="📊 Relatório",
            style="Add.TButton",
            command=self.abrir_relatorio
        ).pack(pady=5, padx=5, side="right")


        ttk.Button(
            buttons_frame,
            text="🗑 Excluir Diária",
            style="Danger.TButton",
            command=self.excluir_diaria
        ).pack(pady=5, padx=5, side="right")

        ttk.Button(
            buttons_frame,
            text="➕ Emitir Diária",
            style="Primary.TButton",
            command=self.abrir_emissao
        ).pack(pady=5, padx=5, side="right")

        # Botão parametros
        btn_parametros = tk.Button(
            buttons_frame,
            text="⚙️ Ajustes",
            font=('Segoe UI', 9),
            bg=CORES['bg_main'],
            fg=CORES['primary'],
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=8,
            command=self.chamar_tela_parametros
        )

        btn_parametros.pack()

        def parametros_hover_enter(e):
            btn_parametros.config(bg=CORES['bg_card_hover'])
        
        def parametros_hover_leave(e):
            btn_parametros.config(bg=CORES['bg_main'])

        btn_parametros.bind("<Enter>", parametros_hover_enter)
        btn_parametros.bind("<Leave>", parametros_hover_leave)

        ttk.Label(
            main_frame,
            text="🔍Buscar:",
            font=('Segoe UI', 9),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")

        # 🔍 Busca por digitação
        self.var_busca = tk.StringVar()
        busca = ttk.Entry(main_frame, textvariable=self.var_busca)
        busca.pack(fill="x", pady=10)
        busca.bind("<KeyRelease>", lambda e: self.atualizar_lista())

        # 📅 Filtro por período
        ttk.Label(
            main_frame,
            text="📅 Período:",
            font=('Segoe UI', 9),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")

        self.combo_periodo = ttk.Combobox(
            main_frame,
            values=["Todos", "Hoje", "Última Semana", "Último Mês"],
            state="readonly",
            width=20
        )
        self.combo_periodo.set("Todos")
        self.combo_periodo.pack(fill="x", pady=(0, 10))

        self.combo_periodo.bind("<<ComboboxSelected>>", lambda e: self.atualizar_lista())


        # =====================================================
        # 🎨 Estilo do Treeview (Diárias)
        # =====================================================
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Diarias.Treeview",
            background="white",
            foreground=CORES['text_dark'],
            rowheight=32,
            fieldbackground="white",
            font=("Segoe UI", 9),
            borderwidth=0
        )

        style.configure(
            "Diarias.Treeview.Heading",
            background=CORES['primary'],
            foreground="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=(10, 8)
        )

        style.map(
            "Diarias.Treeview",
            background=[("selected", CORES['secondary'])],
            foreground=[("selected", "white")]
        )

        style.map(
            "Diarias.Treeview.Heading",
            background=[("active", CORES['primary'])]
        )

        scroll_y = ttk.Scrollbar(main_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        scroll_x = ttk.Scrollbar(main_frame, orient="horizontal")
        scroll_x.pack(side="bottom", fill="x")


        # 📊 Tabela
        self.tree = ttk.Treeview(
            main_frame,
            columns=("nome", "cpf", "qtd_diarias", "valor", "descricao", "data"),
            show="headings",
            height=15,
            style="Diarias.Treeview",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)


        # Cabeçalhos
        self.tree.heading("nome", text="Diarista", anchor="w")
        self.tree.heading("cpf", text="CPF", anchor="center")
        self.tree.heading("qtd_diarias", text="Qtd. Diárias", anchor="center")
        self.tree.heading("valor", text="Valor Total", anchor="e")
        self.tree.heading("descricao", text="Descrição", anchor="w")
        self.tree.heading("data", text="Data", anchor="center")


        # Colunas (largura e alinhamento)
        self.tree.column("nome", width=200, minwidth=180, stretch=False)
        self.tree.column("cpf", width=110, minwidth=100, stretch=False, anchor="center")
        self.tree.column("qtd_diarias", width=100, minwidth=90, stretch=False, anchor="center")
        self.tree.column("valor", width=110, minwidth=100, stretch=False, anchor="e")
        self.tree.column("descricao", width=250, minwidth=150, stretch=True)
        self.tree.column("data", width=120, minwidth=110, stretch=False, anchor="center")

        #Zebra
        self.tree.tag_configure("par", background="#f8f9fa")
        self.tree.tag_configure("impar", background="white")

        # Descrição ocupa o espaço restante
        self.tree.column("descricao", width=200, anchor="w", stretch=True)

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>", self._duplo_clique)


    def _duplo_clique(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.abrir_recibo()

    def get_filtro_periodo(self):
        """Retorna data_inicio e data_fim baseado no período selecionado"""
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

        
    # =====================================================
    def atualizar_lista(self):
        filtro_nome = self.var_busca.get().strip()
        data_inicio, data_fim = self.get_filtro_periodo()

        self.tree.delete(*self.tree.get_children())

        for i, d in enumerate(
            self.dao.listar_diarias(
                filtro_nome=filtro_nome,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
        ):
            tag_cor = "par" if i % 2 == 0 else "impar"

            self.tree.insert(
                "",
                "end",
                values=(
                    d["diarista"],
                    d["cpf"],
                    d["qtd_diarias"],
                    f"R$ {d['vlr_total']:.2f}".replace(".", ","),
                    d["descricao"],
                    d["data_emissao"]
                ),
                tags=(tag_cor, str(d["id"]))
            )



    def abrir_emissao(self):
        # 🔁 Passa callback para atualizar a lista
        TelaEmitirDiaria(
            parent=self.parent_frame,
            callback_atualizar=self.atualizar_lista
        )

    def abrir_recibo(self):
        item = self.tree.focus()

        if not item:
            messagebox.showwarning("Atenção", "Selecione uma diária.")
            return

        tags = self.tree.item(item, "tags")

        if not tags:
            messagebox.showerror("Erro", "Identificação da diária não encontrada.")
            return

        id_diaria = tags[1] if len(tags) > 1 else tags[0]

        dados = self.dao.buscar_diaria_por_id(id_diaria)

        if not dados:
            messagebox.showerror("Erro", "Não foi possível carregar a diária.")
            return

        # 🚀 AGORA CHAMA DIRETO O SERVICE
        from services.recibo_diaria_service import gerar_pdf_recibo_diaria

        gerar_pdf_recibo_diaria(
            dados,
            salvar=False,   # arquivo temporário
            abrir=True      # já abre automaticamente
        )



    def excluir_diaria(self):
        item = self.tree.focus()
        if not item:
            messagebox.showwarning("Atenção", "Selecione uma diária.")
            return

        tags = self.tree.item(item, "tags")

        if not tags or len(tags) < 2:
            messagebox.showerror(
                "Erro",
                "Não foi possível identificar os dados da diária selecionada."
            )
            return

        id_diaria = tags[0]
        caminho_pdf = tags[1]

        confirmar = messagebox.askyesno(
            "Confirmação",
            "Tem certeza que deseja excluir esta diária?\n\nEssa ação não poderá ser desfeita."
        )

        if not confirmar:
            return

        try:
            self.dao.excluir_diaria(id_diaria)

            if caminho_pdf and os.path.exists(caminho_pdf):
                os.remove(caminho_pdf)

            self.atualizar_lista()

            messagebox.showinfo("Sucesso", "Diária excluída com sucesso.")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir diária:\n{e}")

    def abrir_relatorio(self):
        from telas.tela_relatorio_diarias import TelaRelatorioDiarias
        TelaRelatorioDiarias(self.parent_frame)

    def chamar_tela_parametros(self):
        from telas.tela_parametros_diaria import TelaParametrosDiaria

        TelaParametrosDiaria(self.parent_frame)