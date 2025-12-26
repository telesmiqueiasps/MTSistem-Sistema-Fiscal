import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from PyPDF2 import PdfMerger
from utils.constantes import CORES
from utils.auxiliares import resource_path, pasta_dados_app

# =====================================================
# TRIAGEM SPED → PDFs
# =====================================================

class TriagemSPEDEmbed:
    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.arquivo_pdf = None
        base_dados = pasta_dados_app()
        self.pasta_padrao = os.path.join(base_dados, "Arquivos Notas PDF")
        os.makedirs(self.pasta_padrao, exist_ok=True)
        self.criar_interface()

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

        caminho_icone = resource_path("Icones/sped_azul.png")
        img = Image.open(caminho_icone)
        img = img.resize((32, 32), Image.LANCZOS)
        self.icon_header = ImageTk.PhotoImage(img)  # manter referência!


        ttk.Label(
            left_header,
            image=self.icon_header,
            background=CORES['bg_main']
        ).pack(side="left", padx=(0, 15))

        title_frame = ttk.Frame(left_header, style='Main.TFrame')
        title_frame.pack(side="left")

        ttk.Label(
            title_frame,
            text="Triagem SPED → PDFs",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")

        ttk.Label(
            title_frame,
            text="Extraia informações do SPED e gere PDFs mesclados das notas fiscais",
            font=('Segoe UI', 9),
            background=CORES['bg_main'],
            foreground=CORES['text_light']
        ).pack(anchor="w")

        # Card de conteúdo
        content_container = ttk.Frame(main_frame, style='Main.TFrame')
        content_container.pack(fill="both", expand=True)

        center_frame = ttk.Frame(content_container, style='Main.TFrame')
        center_frame.pack(expand=True)

        card = ttk.Frame(center_frame, style='Card.TFrame', padding=40)
        card.pack(fill="both", expand=True, ipadx=100)

        ttk.Label(
            card,
            text="Configuração da Triagem SPED",
            font=('Segoe UI', 14, 'bold'),
            background=CORES['bg_card'],
            foreground=CORES['primary']
        ).pack(anchor="w", pady=(0, 25))
        
        # Campos de entrada
        self.entry_sped = self.criar_campo(
            card, 
            "Arquivo SPED (.txt)", 
            "Selecione o arquivo SPED para processamento",
            self.selecionar_sped
        )
        
        self.entry_pdfs = self.criar_campo(
            card,
            "Pasta dos PDFs",
            "Pasta contendo os arquivos PDF das notas",
            self.selecionar_pdfs
        )

        # Agora o entry EXISTE
        self.entry_pdfs.insert(0, self.pasta_padrao)

        
        self.entry_saida = self.criar_campo(
            card, 
            "Pasta de saída", 
            "Local onde os arquivos mesclados serão salvos",
            self.selecionar_saida
        )
        
        # Barra de progresso (inicialmente oculta)
        self.progress_frame = ttk.Frame(card, style='Card.TFrame')
        self.progress_frame.pack(fill="x", pady=(20, 0))
        
        self.progress_label = ttk.Label(
            self.progress_frame,
            text="",
            style='Subtitle.TLabel'
        )
        self.progress_label.pack(anchor="w", pady=(0, 5))
        
        self.progress = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=300
        )
        
        # Botão executar
        btn_frame = ttk.Frame(card, style='Card.TFrame')
        btn_frame.pack(fill="x", pady=(20, 0))
        
        ttk.Button(
            btn_frame,
            text="▶ Executar Triagem e Gerar PDFs",
            style='Primary.TButton',
            command=self.executar
        ).pack(fill="x")

    def criar_campo(self, parent, titulo, subtitulo, comando):
        campo_frame = ttk.Frame(parent, style='Card.TFrame')
        campo_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            campo_frame,
            text=titulo,
            style='Title.TLabel'
        ).pack(anchor="w")
        
        ttk.Label(
            campo_frame,
            text=subtitulo,
            style='Subtitle.TLabel'
        ).pack(anchor="w", pady=(2, 8))
        
        input_frame = ttk.Frame(campo_frame, style='Card.TFrame')
        input_frame.pack(fill="x")
        
        entry = ttk.Entry(input_frame, font=('Segoe UI', 9))
        entry.pack(side="left", fill="x", expand=True, ipady=5)
        
        ttk.Button(
            input_frame,
            text="📁 Selecionar",
            style='Secondary.TButton',
            command=comando
        ).pack(side="right", padx=(10, 0))
        
        return entry

    def selecionar_sped(self):
        arquivo = filedialog.askopenfilename(filetypes=[("Arquivos SPED", "*.txt")])
        if arquivo:
            self.entry_sped.delete(0, tk.END)
            self.entry_sped.insert(0, arquivo)

    def selecionar_pdfs(self):
        pasta_padrao = self.pasta_padrao

        pasta = filedialog.askdirectory(
            title="Selecione a pasta dos PDFs",
            initialdir=pasta_padrao
        )

        if pasta:
            self.entry_pdfs.delete(0, tk.END)
            self.entry_pdfs.insert(0, pasta)

    def selecionar_saida(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.entry_saida.delete(0, tk.END)
            self.entry_saida.insert(0, pasta)

    def extrair_chaves(self, caminho):
        nf, cte = [], []
        with open(caminho, 'r', encoding='latin-1') as f:
            for linha in f:
                c = linha.split('|')
                if len(c) > 10:
                    if c[1] == 'C100' and c[9].isdigit():
                        nf.append(c[9])
                    if c[1] == 'D100' and c[10].isdigit():
                        cte.append(c[10])
        return nf, cte

    def mesclar(self, chaves, pasta, saida):
        merger = PdfMerger()
        for chave in chaves:
            pdf = os.path.join(pasta, f"{chave}.pdf")
            if os.path.exists(pdf):
                merger.append(pdf)
        if merger.pages:
            merger.write(saida)
            merger.close()

    def executar(self):
        # Validação
        if not self.entry_sped.get() or not self.entry_pdfs.get() or not self.entry_saida.get():
            messagebox.showwarning(
                "Campos Obrigatórios",
                "Por favor, preencha todos os campos antes de continuar."
            )
            return
        
        # Mostrar progresso
        self.progress_label.config(text="Processando arquivos SPED...")
        self.progress.pack(fill="x")
        self.progress.start(10)
        self.janela.update()
        
        try:
            nf, cte = self.extrair_chaves(self.entry_sped.get())
            
            self.progress_label.config(text=f"Mesclando {len(nf)} NF-e encontradas...")
            self.janela.update()
            self.mesclar(nf, self.entry_pdfs.get(), os.path.join(self.entry_saida.get(), "NFe_unico.pdf"))
            
            self.progress_label.config(text=f"Mesclando {len(cte)} CT-e encontradas...")
            self.janela.update()
            self.mesclar(cte, self.entry_pdfs.get(), os.path.join(self.entry_saida.get(), "CTe_unico.pdf"))
            
            self.progress.stop()
            self.progress.pack_forget()
            self.progress_label.config(text="")
            
            messagebox.showinfo(
                "✓ Concluído",
                f"PDFs gerados com sucesso!\n\n"
                f"• NF-e processadas: {len(nf)}\n"
                f"• CT-e processadas: {len(cte)}\n\n"
                f"Arquivos salvos em:\n{self.entry_saida.get()}"
            )
        except Exception as e:
            self.progress.stop()
            self.progress.pack_forget()
            self.progress_label.config(text="")
            messagebox.showerror("Erro", f"Ocorreu um erro ao processar:\n{str(e)}")