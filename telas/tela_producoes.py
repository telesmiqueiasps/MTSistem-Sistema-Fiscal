import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from dao.producao_dao import ProducaoDAO
from telas.tela_nova_producao import TelaNovaProducao
from telas.tela_detalhes_producao import TelaDetalhesProducao
from services.recibo_producao_service import ReciboProducaoService
from utils.constantes import CORES
from utils.auxiliares import resource_path
from PIL import Image, ImageTk
from datetime import datetime, date

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
        
        self.criar_interface()
        self.carregar_producoes()
    
    def criar_interface(self):
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
        
        # ÍCONE DO HEADER
        try:
            caminho_icone = resource_path("Icones/producao_azul.png")
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
            text="Gestão de Produções",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")
        
        ttk.Label(
            title_frame,
            text="Controle de produções e pagamentos por sacos produzidos",
            font=('Segoe UI', 9),
            background=CORES['bg_main'],
            foreground=CORES['text_light']
        ).pack(anchor="w")
        
        # Botões do header
        right_header = ttk.Frame(header_container, style='Main.TFrame')
        right_header.pack(side="right")
        
        ttk.Button(
            right_header,
            text="➕ Nova Produção",
            style="Primary.TButton",
            command=self.nova_producao
        ).pack(side="left", padx=5)
        
        ttk.Button(
            right_header,
            text="🔄 Atualizar",
            style="Secondary.TButton",
            command=self.carregar_producoes
        ).pack(side="left", padx=5)
        
        # Card principal
        card = ttk.Frame(main_frame, style="Card.TFrame", padding=30)
        card.pack(fill="both", expand=True)
        
        # Filtros
        filtro_frame = ttk.Frame(card, style="Card.TFrame")
        filtro_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            filtro_frame,
            text="Filtrar:",
            font=('Segoe UI', 10),
            background=CORES['bg_card'],
            foreground=CORES['text_dark']
        ).pack(side="left", padx=(0, 15))
        
        self.filtro_var = tk.StringVar(value="todas")
        
        ttk.Radiobutton(
            filtro_frame,
            text="Todas",
            variable=self.filtro_var,
            value="todas",
            command=self.carregar_producoes
        ).pack(side="left", padx=5)
        
        ttk.Radiobutton(
            filtro_frame,
            text="Abertas",
            variable=self.filtro_var,
            value="abertas",
            command=self.carregar_producoes
        ).pack(side="left", padx=5)
        
        ttk.Radiobutton(
            filtro_frame,
            text="Fechadas",
            variable=self.filtro_var,
            value="fechadas",
            command=self.carregar_producoes
        ).pack(side="left", padx=5)
        
        # Frame para lista com scroll
        lista_container = ttk.Frame(card, style="Card.TFrame")
        lista_container.pack(fill="both", expand=True)
        
        # Canvas e scrollbar
        canvas = tk.Canvas(
            lista_container,
            bg=CORES['bg_card'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(lista_container, orient="vertical", command=canvas.yview)
        
        self.scroll_frame = ttk.Frame(canvas, style="Card.TFrame")
        
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def carregar_producoes(self):
        # Limpa frame
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # Carrega produções
        filtro = self.filtro_var.get()
        if filtro == "abertas":
            producoes = self.dao.listar_producoes(apenas_abertas=True)
        elif filtro == "fechadas":
            producoes = [p for p in self.dao.listar_producoes() if p['status'] == 'fechada']
        else:
            producoes = self.dao.listar_producoes()
        
        if not producoes:
            ttk.Label(
                self.scroll_frame,
                text="Nenhuma produção encontrada",
                font=('Segoe UI', 11),
                background=CORES['bg_card'],
                foreground=CORES['text_light']
            ).pack(pady=40)
            return
        
        # Cria cards de produção
        for producao in producoes:
            self.criar_card_producao(producao)
    
    def criar_card_producao(self, producao):
        # Card frame
        card_frame = tk.Frame(
            self.scroll_frame,
            bg='white',
            relief='solid',
            bd=1,
            highlightbackground=CORES['border'],
            highlightthickness=1
        )
        card_frame.pack(fill="x", pady=8, padx=2)
        
        # Padding interno
        inner = tk.Frame(card_frame, bg='white')
        inner.pack(fill="x", padx=20, pady=15)
        
        # Lado esquerdo - informações
        left_frame = tk.Frame(inner, bg='white')
        left_frame.pack(side="left", fill="x", expand=True)
        
        # Nome e status
        title_container = tk.Frame(left_frame, bg='white')
        title_container.pack(fill="x", anchor="w")
        
        tk.Label(
            title_container,
            text=producao['nome'],
            font=('Segoe UI', 13, 'bold'),
            bg='white',
            fg=CORES['text_dark']
        ).pack(side="left")
        
        # Badge de status
        status_color = CORES['success'] if producao['status'] == 'aberta' else CORES['text_light']
        status_text = "ABERTA" if producao['status'] == 'aberta' else "FECHADA"
        
        status_label = tk.Label(
            title_container,
            text=status_text,
            font=('Segoe UI', 8, 'bold'),
            bg=status_color,
            fg='white',
            padx=10,
            pady=3
        )
        status_label.pack(side="left", padx=12)
        
        # Informações
        info_text = f"📅 Início: {formatar_data_br(producao['data_inicio'])}"
        if producao['data_fim']:
            info_text += f"  •  Fim: {formatar_data_br(producao['data_fim'])}"
        info_text += f"  •  📦 {producao['total_sacos']} sacos  •  💰 R$ {producao['valor_total']:.2f}"
        
        tk.Label(
            left_frame,
            text=info_text,
            font=('Segoe UI', 9),
            bg='white',
            fg=CORES['text_light']
        ).pack(anchor="w", pady=(8, 0))
        
        # Lado direito - botões
        btn_frame = tk.Frame(inner, bg='white')
        btn_frame.pack(side="right", padx=(15, 0))
        
        # Botão Ver Detalhes
        ttk.Button(
            btn_frame,
            text="👁️ Detalhes",
            style="Primary.TButton",
            command=lambda: self.ver_detalhes(producao['id'])
        ).pack(side="left", padx=3)

        # Botão Excluir
        ttk.Button(
            btn_frame,
            text="🗑️ Excluir",
            style="Danger.TButton",
            command=lambda: self.excluir_producao(producao['id'], producao['nome'])
        ).pack(side="left", padx=3)
        
        # Botão Recibo (só se fechada)
        if producao['status'] == 'fechada':
            ttk.Button(
                btn_frame,
                text="📄 Recibo",
                style="Warning.TButton",
                command=lambda: self.gerar_recibo(producao['id'])
            ).pack(side="left", padx=3)

            
        
        # Hover effect
        def on_enter(e):
            card_frame.config(bg=CORES['bg_card_hover'])
            inner.config(bg=CORES['bg_card_hover'])
            left_frame.config(bg=CORES['bg_card_hover'])
            title_container.config(bg=CORES['bg_card_hover'])
            btn_frame.config(bg=CORES['bg_card_hover'])
            for widget in title_container.winfo_children():
                if isinstance(widget, tk.Label) and widget != status_label:
                    widget.config(bg=CORES['bg_card_hover'])
            for widget in left_frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(bg=CORES['bg_card_hover'])
        
        def on_leave(e):
            card_frame.config(bg='white')
            inner.config(bg='white')
            left_frame.config(bg='white')
            title_container.config(bg='white')
            btn_frame.config(bg='white')
            for widget in title_container.winfo_children():
                if isinstance(widget, tk.Label) and widget != status_label:
                    widget.config(bg='white')
            for widget in left_frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(bg='white')
        
        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)
    
    def nova_producao(self):
        TelaNovaProducao(self.parent_frame, self.carregar_producoes)
    
    def ver_detalhes(self, producao_id):
        # Limpa content area do sistema fiscal
        self.sistema_fiscal.limpar_content_area()
        # Abre tela de detalhes
        TelaDetalhesProducao(self.sistema_fiscal.content_area, producao_id, self.voltar_para_lista)
    
    def voltar_para_lista(self):
        # Limpa e recria a tela de lista
        self.sistema_fiscal.limpar_content_area()
        ProducoesPrincipalEmbed(self.sistema_fiscal.content_area, self.sistema_fiscal)
    
    def gerar_recibo(self, producao_id):
        try:
            arquivo = self.recibo_producao_service.gerar_recibo_geral(producao_id, salvar=False, abrir=True)
            if not arquivo:
                return 
            messagebox.showinfo(
                "Sucesso",
                "Recibo gerado com sucesso!"
            )
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar recibo: {str(e)}")

    def excluir_producao(self, producao_id, producao_nome):
        """Exclui uma produção após confirmação"""
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
                messagebox.showinfo(
                    "Sucesso",
                    f"Produção '{producao_nome}' excluída com sucesso!"
                )
                self.carregar_producoes()
            else:
                messagebox.showerror(
                    "Erro",
                    "Erro ao excluir a produção. Tente novamente."
                )        