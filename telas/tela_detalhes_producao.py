import tkinter as tk
from tkinter import ttk, messagebox
from dao.producao_dao import ProducaoDAO
from dao.diarista_dao import DiaristaDAO
from telas.tela_adicionar_dia import TelaAdicionarDia
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

class TelaDetalhesProducao:
    def __init__(self, parent_frame, producao_id, callback_voltar=None):
        self.parent_frame = parent_frame
        self.producao_id = producao_id
        self.callback_voltar = callback_voltar
        self.dao = ProducaoDAO()
        self.diarista_dao = DiaristaDAO()
        self.recibo_producao_service = ReciboProducaoService(self.dao)
        
        self.criar_interface()
        self.carregar_dados()
    
    def criar_interface(self):
        # Frame principal
        main_frame = ttk.Frame(self.parent_frame, style='Main.TFrame')
        main_frame.pack(fill="both", expand=True, padx=50, pady=30)
        
        # Header
        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.pack(fill="x", pady=(0, 20))
        
        header_container = ttk.Frame(header_frame, style='Main.TFrame')
        header_container.pack(fill="x")
        
        # Lado esquerdo - botão voltar e título
        left_header = ttk.Frame(header_container, style='Main.TFrame')
        left_header.pack(side="left")
        
        ttk.Button(
            left_header,
            text="← Voltar",
            style="Secondary.TButton",
            command=self.voltar
        ).pack(side="left", padx=(0, 20))
        
        title_frame = ttk.Frame(left_header, style='Main.TFrame')
        title_frame.pack(side="left")
        
        self.lbl_titulo = ttk.Label(
            title_frame,
            text="",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        )
        self.lbl_titulo.pack(side="left")
        
        # Status badge
        self.status_badge = tk.Label(
            title_frame,
            text="",
            font=('Segoe UI', 8, 'bold'),
            padx=10,
            pady=3
        )
        self.status_badge.pack(side="left", padx=15)
        
        # Botões de ação
        right_header = ttk.Frame(header_container, style='Main.TFrame')
        right_header.pack(side="right")
        
        self.btn_adicionar_dia = ttk.Button(
            right_header,
            text="➕ Adicionar Dia",
            style="Primary.TButton",
            command=self.adicionar_dia
        )
        self.btn_adicionar_dia.pack(side="left", padx=5)
        
        self.btn_fechar = ttk.Button(
            right_header,
            text="🔒 Fechar Produção",
            style="Warning.TButton",
            command=self.fechar_producao
        )
        self.btn_fechar.pack(side="left", padx=5)
        
        self.btn_recibo = ttk.Button(
            right_header,
            text="📄 Gerar Recibo",
            style="Primary.TButton",
            command=self.gerar_recibo_geral
        )
        
        # Info card
        info_card = ttk.Frame(main_frame, style="Card.TFrame", padding=20)
        info_card.pack(fill="x", pady=(0, 20))
        
        self.lbl_info = ttk.Label(
            info_card,
            text="",
            font=('Segoe UI', 10),
            background=CORES['bg_card'],
            foreground=CORES['text_dark']
        )
        self.lbl_info.pack()
        
        # Card principal com abas
        card = ttk.Frame(main_frame, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)
        
        # Notebook (abas)
        self.notebook = ttk.Notebook(card)
        self.notebook.pack(fill="both", expand=True)
        
        # Aba: Dias de Produção
        self.frame_dias = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(self.frame_dias, text="📅 Dias de Produção")
        
        # Aba: Totais por Diarista
        self.frame_totais = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(self.frame_totais, text="👥 Totais por Diarista")
        
        self.criar_aba_dias()
        self.criar_aba_totais()
    
    def criar_aba_dias(self):
        # Canvas e scrollbar
        canvas = tk.Canvas(
            self.frame_dias,
            bg=CORES['bg_card'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(self.frame_dias, orient="vertical", command=canvas.yview)
        
        self.scroll_dias = ttk.Frame(canvas, style="Card.TFrame")
        
        self.scroll_dias.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scroll_dias, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def criar_aba_totais(self):
        # Canvas e scrollbar
        canvas = tk.Canvas(
            self.frame_totais,
            bg=CORES['bg_card'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(self.frame_totais, orient="vertical", command=canvas.yview)
        
        self.scroll_totais = ttk.Frame(canvas, style="Card.TFrame")
        
        self.scroll_totais.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scroll_totais, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def carregar_dados(self):
        producao = self.dao.get_producao(self.producao_id)
        if not producao:
            messagebox.showerror("Erro", "Produção não encontrada!")
            self.voltar()
            return
        
        # Atualiza cabeçalho
        self.lbl_titulo.config(text=producao['nome'])
        
        if producao['status'] == 'aberta':
            self.status_badge.config(text="ABERTA", bg=CORES['success'], fg='white')
            self.btn_adicionar_dia.pack(side="left", padx=5)
            self.btn_fechar.pack(side="left", padx=5)
            self.btn_recibo.pack_forget()
        else:
            self.status_badge.config(text="FECHADA", bg=CORES['text_light'], fg='white')
            self.btn_adicionar_dia.pack_forget()
            self.btn_fechar.pack_forget()
            self.btn_recibo.pack(side="left", padx=5)



        # Atualiza info
        info_texto = f"📅 Início: {formatar_data_br(producao['data_inicio'])}"
        if producao['data_fim']:
            info_texto += f"  •  Fim: {formatar_data_br(producao['data_fim'])}"
        info_texto += f"  •  📦 Total: {producao['total_sacos']} sacos  •  💰 Valor: R$ {producao['valor_total']:.2f}"
        self.lbl_info.config(text=info_texto)
        
        # Carrega abas
        self.carregar_dias()
        self.carregar_totais_diaristas()
    
    def carregar_dias(self):
        # Limpa
        for widget in self.scroll_dias.winfo_children():
            widget.destroy()
        
        dias = self.dao.listar_dias_producao(self.producao_id)
        
        if not dias:
            ttk.Label(
                self.scroll_dias,
                text="Nenhum dia de produção registrado",
                font=('Segoe UI', 11),
                background=CORES['bg_card'],
                foreground=CORES['text_light']
            ).pack(pady=30)
            return
        
        for dia in dias:
            self.criar_card_dia(dia)
    
    def criar_card_dia(self, dia):
        card = tk.Frame(
            self.scroll_dias,
            bg='white',
            relief='solid',
            bd=1
        )
        card.pack(fill="x", pady=6, padx=2)
        
        inner = tk.Frame(card, bg='white')
        inner.pack(fill="x", padx=15, pady=12)

        info = tk.Frame(inner, bg='white')
        info.pack(side="left", fill="x", expand=True)

        acoes = tk.Frame(inner, bg='white')
        acoes.pack(side="right")

        
        # Informações
        tk.Label(
            info,
            text=f"📅 {formatar_data_br(dia['data_producao'])}",
            font=('Segoe UI', 11, 'bold'),
            bg='white',
            fg=CORES['text_dark']
        ).pack(anchor="w")

        tk.Label(
            info,
            text=(
                f"📦 {dia['total_sacos_dia']} sacos  •  "
                f"💰 R$ {dia['valor_saco']:.2f}/saco  •  "
                f"Total: R$ {dia['total_sacos_dia'] * dia['valor_saco']:.2f}"
            ),
            font=('Segoe UI', 9),
            bg='white',
            fg=CORES['text_light']
        ).pack(anchor="w", pady=(3, 0))

        
        # Botão deletar (só se aberta)
        producao = self.dao.get_producao(self.producao_id)
        if producao['status'] == 'aberta':
            tk.Button(
                acoes,
                text="🗑️ Excluir",
                font=('Segoe UI', 9),
                bg=CORES['danger'],
                fg='white',
                relief='flat',
                cursor='hand2',
                padx=6,
                pady=3,
                command=lambda d=dia: self.deletar_dia(d['id'])
            ).pack()

    
    def carregar_totais_diaristas(self):
        # Limpa
        for widget in self.scroll_totais.winfo_children():
            widget.destroy()
        
        totais = self.dao.get_totais_diaristas(self.producao_id)
        
        if not totais:
            ttk.Label(
                self.scroll_totais,
                text="Nenhum diarista registrado",
                font=('Segoe UI', 11),
                background=CORES['bg_card'],
                foreground=CORES['text_light']
            ).pack(pady=30)
            return
        
        for total in totais:
            self.criar_card_total_diarista(total)
    
    def criar_card_total_diarista(self, total):
        card = tk.Frame(
            self.scroll_totais,
            bg='white',
            relief='solid',
            bd=1
        )
        card.pack(fill="x", pady=6, padx=2)

        inner = tk.Frame(card, bg='white')
        inner.pack(fill="x", padx=15, pady=12)

        # =========================
        # Colunas
        # =========================
        info = tk.Frame(inner, bg='white')
        info.pack(side="left", fill="x", expand=True)

        acoes = tk.Frame(inner, bg='white')
        acoes.pack(side="right")

        # =========================
        # Nome
        # =========================
        tk.Label(
            info,
            text=total['nome'],
            font=('Segoe UI', 11, 'bold'),
            bg='white',
            fg=CORES['text_dark']
        ).pack(anchor="w")

        # =========================
        # CPF e totais
        # =========================
        tk.Label(
            info,
            text=(
                f"CPF: {total['cpf']}  •  "
                f"📦 {total['total_sacos']} sacos  •  "
                f"💰 R$ {total['valor_total']:.2f}"
            ),
            font=('Segoe UI', 9),
            bg='white',
            fg=CORES['text_light']
        ).pack(anchor="w", pady=(3, 0))

        # =========================
        # Botão recibo
        # =========================
        tk.Button(
            acoes,
            text="📄 Recibo",
            font=('Segoe UI', 9),
            bg=CORES['primary'],
            fg='white',
            relief='flat',
            cursor='hand2',
            padx=10,
            pady=4,
            command=lambda: self.gerar_recibo_individual(total['id'])
        ).pack()

    
    def adicionar_dia(self):
        TelaAdicionarDia(self.parent_frame, self.producao_id, self.carregar_dados)
    
    def deletar_dia(self, dia_id):
        if messagebox.askyesno("Confirmar", "Deseja realmente excluir este dia de produção?"):
            if self.dao.deletar_dia_producao(dia_id):
                messagebox.showinfo("Sucesso", "Dia excluído com sucesso!")
                self.carregar_dados()
            else:
                messagebox.showerror("Erro", "Erro ao excluir dia!")
    
    def fechar_producao(self):
        from datetime import datetime
        
        if messagebox.askyesno("Confirmar", "Deseja realmente fechar esta produção?\n\nApós fechar, não será possível adicionar novos dias."):
            data_fim = datetime.now().strftime('%Y-%m-%d')
            if self.dao.fechar_producao(self.producao_id, data_fim):
                messagebox.showinfo("Sucesso", "Produção fechada com sucesso!")
                self.carregar_dados()
            else:
                messagebox.showerror("Erro", "Erro ao fechar produção!")
    
    def gerar_recibo_geral(self):
        try:
            arquivo = self.recibo_producao_service.gerar_recibo_geral(
                self.producao_id,
                salvar=False,
                abrir=True
            )

            if not arquivo:
                return  # usuário cancelou

            messagebox.showinfo(
                "Sucesso",
                "Recibo geral gerado com sucesso!"
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar recibo: {str(e)}")

    
    def gerar_recibo_individual(self, diarista_id):
        try:
            arquivo = self.recibo_producao_service.gerar_recibo_individual(
                self.producao_id,
                diarista_id,
                salvar=False,
                abrir=True
            )

            if not arquivo:
                return

            messagebox.showinfo(
                "Sucesso",
                "Recibo individual gerado com sucesso!"
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar recibo: {str(e)}")

    
    def voltar(self):
        if self.callback_voltar:
            self.callback_voltar()