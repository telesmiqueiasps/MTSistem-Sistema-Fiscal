import tkinter as tk
from tkinter import ttk
from tkinter import ttk, messagebox
from utils.constantes import CORES
from utils.auxiliares import resource_path, configurar_estilo, sistema_esta_desatualizado, atualizacao_liberada, executar_atualizacao
from dao.usuario_dao import UsuarioDAO
from PIL import Image, ImageTk

# =====================================================
# Extração Informações PDF → Excel
# =====================================================
class SistemaFiscal:
    def __init__(self, root, usuario_id, usuario_nome, versao_remota):
        self.root = root
        self.usuario_id = usuario_id
        self.usuario_nome = usuario_nome
        self.dao = UsuarioDAO()
        self.versao_remota = versao_remota
        self.desatualizado = sistema_esta_desatualizado(self.dao)
        self.atualizacao_liberada = atualizacao_liberada(self.dao)
        self.usuario_admin = self.dao.usuario_admin(self.usuario_id)
        self.mensagem_update = self.dao.get_config(
            "mensagem_update",
            "⚠️ Sistema desatualizado"
        )
        root.title("MT Sistem - Sistema Fiscal")
        
        # Janela maximizada
        root.state('zoomed')
        root.minsize(1000, 600)
        root.resizable(True, True)
        root.configure(bg=CORES['bg_main'])

        # ÍCONE DA JANELA
        caminho_icone = resource_path("Icones/logo.ico")
        self.root.iconbitmap(caminho_icone)

        configurar_estilo()
        
        # Container para o conteúdo dinâmico
        self.content_area = None
        
        self.criar_interface()
    

    def abrir_extrator(self):
        from telas.tela_extrator_txt import ExtratorFiscalAppEmbed
        self.limpar_content_area()
        ExtratorFiscalAppEmbed(self.content_area, self)

    def abrir_triagem(self):
        from telas.tela_triagem import TriagemSPEDEmbed
        self.limpar_content_area()
        TriagemSPEDEmbed(self.content_area, self)

    def abrir_comparador(self):
        from telas.tela_comparador import ComparadorNotasEmbed
        self.limpar_content_area()
        ComparadorNotasEmbed(self.content_area, self)

    def abrir_extrator_pdf(self):
        from telas.tela_extrator_pdf import ExtratorFiscalPDFAppEmbed
        self.limpar_content_area()
        ExtratorFiscalPDFAppEmbed(self.content_area, self)

    def abrir_diaristas(self):
        from telas.tela_diaristas import DiaristasEmbed
        self.limpar_content_area()
        DiaristasEmbed(self.content_area, self)

    def abrir_centros_custo(self):
        from telas.tela_centros_custo import CentrosCustoEmbed
        self.limpar_content_area()
        CentrosCustoEmbed(self.content_area, self)
           
    def abrir_diarias(self):
        from telas.tela_diarias_emitidas import DiariasEmitidasEmbed
        self.limpar_content_area()
        DiariasEmitidasEmbed(self.content_area, self)

    def abrir_producao(self):
        from telas.tela_producoes import ProducoesPrincipalEmbed
        self.limpar_content_area()
        ProducoesPrincipalEmbed(self.content_area, self)

    def voltar_home(self):
        self.limpar_content_area()
        self.mostrar_home()

    def limpar_content_area(self):
        """Limpa a área de conteúdo"""
        if self.content_area:
            for widget in self.content_area.winfo_children():
                widget.destroy()
                

    def criar_interface(self):
        from telas.tela_usuarios_admin import TelaUsuariosAdmin
        from telas.tela_configuracoes import TelaConfiguracoesSistema
        from telas.tela_empresa import TelaEmpresa

        # =========================
        # CONTAINER PRINCIPAL
        # =========================
        main_container = ttk.Frame(self.root, style='Main.TFrame')
        main_container.pack(fill="both", expand=True)

        # =========================
        # SIDEBAR LATERAL
        # =========================
        sidebar = tk.Frame(main_container, bg=CORES['primary'], width=280)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # =========================
        # TOPO FIXO (Logo + Título)
        # =========================
        logo_frame = tk.Frame(sidebar, bg=CORES['primary'])
        logo_frame.pack(fill="x", pady=(30, 20))

        caminho_logo = resource_path("Icones/logo_branca.png")
        img = Image.open(caminho_logo)
        img = img.resize((60, 60), Image.LANCZOS)
        self.logo_img = ImageTk.PhotoImage(img)

        tk.Label(logo_frame, image=self.logo_img, bg=CORES['primary']).pack()

        tk.Label(
            logo_frame,
            text="Sistema Fiscal",
            font=('Segoe UI', 16, 'bold'),
            bg=CORES['primary'],
            fg='white'
        ).pack(pady=(10, 5))

        tk.Label(
            logo_frame,
            text="MT Sistem",
            font=('Segoe UI', 9),
            bg=CORES['primary'],
            fg='white'
        ).pack()

        # Separador
        tk.Frame(sidebar, bg='white', height=1).pack(fill="x", pady=10, padx=20)

        # =========================
        # ÁREA ROLÁVEL DO MENU
        # =========================
        menu_container = tk.Frame(sidebar, bg=CORES['primary'])
        menu_container.pack(fill="both", expand=True)

        # Canvas + Scrollbar
        canvas = tk.Canvas(menu_container, bg=CORES['primary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(menu_container, orient="vertical", command=canvas.yview, width=12)
        self.menu_scrollable = tk.Frame(canvas, bg=CORES['primary'])

        # === CORREÇÃO PRINCIPAL: largura fixa igual à sidebar ===
        self.menu_scrollable.config(width=280)  # Mesma largura da sidebar
        canvas.create_window((0, 0), window=self.menu_scrollable, anchor="nw", width=280)

        self.menu_scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll só quando o mouse estiver sobre a sidebar
        def _ativar_scroll(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def _desativar_scroll(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        menu_container.bind("<Enter>", _ativar_scroll)
        menu_container.bind("<Leave>", _desativar_scroll)

        # =========================
        # CONTEÚDO DO MENU (agora dentro da área rolável)
        # =========================
        menu_frame = self.menu_scrollable  # Tudo vai aqui agora!

        dao = UsuarioDAO()
        is_admin = dao.is_admin(self.usuario_id)
        permissoes = dao.permissoes_usuario(self.usuario_id)

        # Botão Home
        self.criar_menu_item(menu_frame, "Início", self.voltar_home, icone="inicio.png")

        tk.Label(
            menu_frame,
            text="MÓDULOS",
            font=('Segoe UI', 8, 'bold'),
            bg=CORES['primary'],
            fg='#a0aec0',
            anchor='w'
        ).pack(fill="x", pady=(15, 8), padx=15)

        # Módulos
        if is_admin or "abrir_extrator" in permissoes:
            self.criar_menu_item(menu_frame, "Extrator TXT → Excel", self.abrir_extrator, icone="txt.png")

        if is_admin or "abrir_comparador" in permissoes:
            self.criar_menu_item(menu_frame, "Comparador SEFAZ", self.abrir_comparador, icone="comparador.png")

        if is_admin or "abrir_triagem" in permissoes:
            self.criar_menu_item(menu_frame, "Triagem SPED", self.abrir_triagem, icone="sped.png")

        if is_admin or "abrir_extrator_pdf" in permissoes:
            self.criar_menu_item(menu_frame, "Extrator PDF → Excel", self.abrir_extrator_pdf, icone="pdf.png")

        if is_admin or "abrir_diaristas" in permissoes:
            self.criar_menu_item(menu_frame, "Cadastro de Diaristas", self.abrir_diaristas, icone="diarista.png")

        if is_admin or "abrir_centros_custo" in permissoes:
            self.criar_menu_item(menu_frame, "Centros de Custo", self.abrir_centros_custo, icone="centro_custo.png")

        if is_admin or "abrir_diarias" in permissoes:
            self.criar_menu_item(menu_frame, "Emissor de Diárias", self.abrir_diarias, icone="diarias.png")

        if is_admin or "abrir_producao" in permissoes:
            self.criar_menu_item(menu_frame, "Controle de Produção", self.abrir_producao, icone="producao.png")
        # Separador antes da administração
        if is_admin:

            tk.Label(
                menu_frame,
                text="ADMINISTRAÇÃO",
                font=('Segoe UI', 8, 'bold'),
                bg=CORES['primary'],
                fg='#a0aec0',
                anchor='w'
            ).pack(fill="x", pady=(15, 8), padx=15)

            self.criar_menu_item(menu_frame, "Usuários", lambda: TelaUsuariosAdmin(self.root), icone="usuarios.png", is_admin_btn=True)
            self.criar_menu_item(menu_frame, "Configurações do Sistema", lambda: TelaConfiguracoesSistema(self.root), icone="config.png", is_admin_btn=True)
            self.criar_menu_item(menu_frame, "Cadastro da Empresa", lambda: TelaEmpresa(self.root), icone="empresa.png", is_admin_btn=True)

        # =========================
        # RODAPÉ FIXO (sempre visível)
        # =========================
        footer_sidebar = tk.Frame(sidebar, bg=CORES['primary'])
        footer_sidebar.pack(fill="x", side="bottom", pady=20)

        tk.Frame(footer_sidebar, bg='white', height=1).pack(fill="x", pady=15, padx=20)

        tk.Label(
            footer_sidebar,
            text=f"👤 {self.usuario_nome}",
            font=('Segoe UI', 9),
            bg=CORES['primary'],
            fg='white'
        ).pack(pady=(0, 10))

        btn_sair = tk.Button(
            footer_sidebar,
            text="🚪 Sair",
            font=('Segoe UI', 9),
            bg='white',
            fg=CORES['primary'],
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=8,
            command=self.sair
        )
        btn_sair.pack()

        def sair_hover_enter(e): btn_sair.config(bg=CORES['bg_card_hover'])
        def sair_hover_leave(e): btn_sair.config(bg='white')

        btn_sair.bind("<Enter>", sair_hover_enter)
        btn_sair.bind("<Leave>", sair_hover_leave)

        # =========================
        # ÁREA DE CONTEÚDO
        # =========================
        self.content_area = ttk.Frame(main_container, style='Main.TFrame')
        self.content_area.pack(side="right", fill="both", expand=True)

        self.mostrar_home()

    def criar_menu_item(self, parent, texto, comando, icone=None, is_admin_btn=False):
        # Frame principal do item (altura fixa pequena e controle total)
        btn = tk.Frame(parent, bg=CORES['primary'], cursor='hand2', height=36)
        btn.pack(fill="x", padx=12, pady=2)  # Menos pady (era 5+2+10 = muito espaço)
        btn.pack_propagate(False)  # Mantém altura fixa

        # Container interno para ícone + texto
        inner = tk.Frame(btn, bg=CORES['primary'])
        inner.pack(fill="both", expand=True, padx=15)

        # Ícone
        lbl_icon = None
        if icone:
            caminho_icone = resource_path(f"Icones/{icone}")
            img = Image.open(caminho_icone)
            img = img.resize((18, 18), Image.LANCZOS)
            icon_img = ImageTk.PhotoImage(img)

            lbl_icon = tk.Label(inner, image=icon_img, bg=CORES['primary'])
            lbl_icon.image = icon_img
            lbl_icon.pack(side="left", padx=(0, 12))

        # Texto
        lbl_text = tk.Label(
            inner,
            text=texto,
            font=('Segoe UI', 10, 'bold') if is_admin_btn else ('Segoe UI', 10),
            bg=CORES['primary'],
            fg='white',
            anchor='w'
        )
        lbl_text.pack(side="left", fill="x", expand=True)

        # Cores do hover
        cor_normal = CORES['primary']
        cor_hover = '#f8f9fa'  # Cor clara suave (ou mude para '#2c313c' se quiser mais escuro)

        # Hover ESTÁVEL: só no frame principal
        def on_enter(e):
            btn.config(bg=cor_hover)
            inner.config(bg=cor_hover)
            lbl_text.config(bg=cor_hover, fg=CORES['primary'])
            if lbl_icon:
                lbl_icon.config(bg=cor_hover)

        def on_leave(e):
            btn.config(bg=cor_normal)
            inner.config(bg=cor_normal)
            lbl_text.config(bg=cor_normal, fg='white')
            if lbl_icon:
                lbl_icon.config(bg=cor_normal)

        # Eventos apenas no btn principal → hover perfeito sem piscar
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        # Clique em qualquer lugar
        def clique(e):
            comando()

        btn.bind("<Button-1>", clique)
        inner.bind("<Button-1>", clique)
        lbl_text.bind("<Button-1>", clique)
        if lbl_icon:
            lbl_icon.bind("<Button-1>", clique)

    
    def mostrar_home(self):
        home_frame = ttk.Frame(self.content_area, style='Main.TFrame')
        home_frame.pack(fill="both", expand=True, padx=50, pady=50)

        ttk.Label(
            home_frame,
            text="Bem-vindo ao Sistema Fiscal",
            font=('Segoe UI', 24, 'bold'),
            foreground=CORES['text_dark'],
            background=CORES['bg_main']
        ).pack(pady=(0, 10))

        linha = ttk.Frame(home_frame, style='Main.TFrame')
        linha.pack(pady=(0, 40))

        ttk.Label(
            linha,
            text="Olá, ",
            font=('Segoe UI', 11),
            foreground=CORES['text_dark'],
            background=CORES['bg_main']
        ).pack(side="left")

        ttk.Label(
            linha,
            text=self.usuario_nome,
            font=('Segoe UI', 11, 'bold'),
            foreground=CORES['primary'],  # cor diferente só no nome
            background=CORES['bg_main']
        ).pack(side="left")

        ttk.Label(
            linha,
            text="! Selecione um módulo no menu lateral para começar.",
            font=('Segoe UI', 11),
            foreground=CORES['text_dark'],
            background=CORES['bg_main']
        ).pack(side="left")


        # =========================
        # AVISO DE ATUALIZAÇÃO
        # =========================
        if self.desatualizado:
            ttk.Label(
                home_frame,
                text=self.mensagem_update,
                foreground="#C0392B",
                font=('Segoe UI', 11, 'bold'),
                wraplength=600,     
                justify="center"
            ).pack(pady=(20, 10))

            btn_atualizar = ttk.Button(
                home_frame,
                text="Atualizar sistema",
                command=lambda: executar_atualizacao(self.dao)
            )

            if self.atualizacao_liberada:
                btn_atualizar.state(["!disabled"])
            else:
                btn_atualizar.state(["disabled"])

            btn_atualizar.pack(pady=5)



        # Cards informativos
        cards_container = ttk.Frame(home_frame, style='Main.TFrame')
        cards_container.pack(fill="both", expand=True)

        # Grid para os cards
        cards_container.grid_columnconfigure(0, weight=1)
        cards_container.grid_columnconfigure(1, weight=1)
        cards_container.grid_rowconfigure(0, weight=1)
        cards_container.grid_rowconfigure(1, weight=1)

        # Card 1
        self.criar_info_card(
            cards_container, 0, 0,
            "📊 Extração Automatizada",
            "Extraia dados fiscais de arquivos TXT e PDF diretamente para Excel com poucos cliques."
        )

        # Card 2
        self.criar_info_card(
            cards_container, 0, 1,
            "🔍 Comparação Inteligente",
            "Compare notas da SEFAZ com seu sistema e identifique divergências rapidamente."
        )

        # Card 3
        self.criar_info_card(
            cards_container, 1, 0,
            "📁 Triagem de Documentos",
            "Organize e mescle automaticamente PDFs de NF-e e CT-e a partir do SPED."
        )

        # Card 4
        self.criar_info_card(
            cards_container, 1, 1,
            "⚡ Gestão Eficiente",
            "Centralize toda gestão fiscal em um único sistema profissional e intuitivo."
        )

        # Rodapé
        footer = ttk.Frame(home_frame, style='Main.TFrame')
        footer.pack(fill="x", pady=(40, 0))
        
        ttk.Label(
            footer,
            text="v1.0 • MTSistem - Desenvolvido e licenciado por Miquéias Teles",
            font=('Segoe UI', 8),
            background=CORES['bg_main'],
            foreground=CORES['text_light']
        ).pack()

    def criar_info_card(self, parent, row, col, titulo, descricao):
        card = tk.Frame(
            parent,
            bg='white',
            highlightthickness=2,
            highlightbackground=CORES['bg_main']
        )
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        inner = tk.Frame(card, bg='white')
        inner.pack(fill="both", expand=True, padx=25, pady=25)

        tk.Label(
            inner,
            text=titulo,
            font=('Segoe UI', 13, 'bold'),
            bg='white',
            fg=CORES['primary'],
            anchor='w'
        ).pack(fill="x", pady=(0, 10))

        tk.Label(
            inner,
            text=descricao,
            font=('Segoe UI', 10),
            bg='white',
            fg=CORES['text_light'],
            anchor='w',
            wraplength=250,
            justify='left'
        ).pack(fill="x")

    def sair(self):
        from telas.tela_login import TelaLogin
        resposta = messagebox.askyesno(
            "Sair do sistema",
            "Deseja sair e voltar para a tela de login?"
        )
        if not resposta:
            return

        self.root.destroy()

        root = tk.Tk()
        TelaLogin(root, versao_remota=self.versao_remota)
        root.mainloop()
