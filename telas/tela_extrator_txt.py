import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import pandas as pd
from utils.constantes import CORES
from utils.auxiliares import resource_path

# =====================================================
# Extração Informações TXT → Excel
# =====================================================

class ExtratorFiscalAppEmbed:
    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.arquivo_pdf = None
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


        caminho_icone = resource_path("Icones/txt_azul.png")
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
            text="Extração TXT → Excel",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")

        ttk.Label(
            title_frame,
            text="Extraia informações fiscais de arquivos TXT para planilhas Excel",
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
            text="Configuração da Extração",
            font=('Segoe UI', 14, 'bold'),
            background=CORES['bg_card'],
            foreground=CORES['primary']
        ).pack(anchor="w", pady=(0, 25))
        
        # Campos de entrada
        self.lbl_arquivo = self.criar_campo(
            card, 
            "Arquivo TXT (.txt)", 
            "Selecione o arquivo TXT para processamento",
            self.selecionar_txt
        )
        
        
        # Botão executar
        btn_frame = ttk.Frame(card, style='Card.TFrame')
        btn_frame.pack(fill="x", pady=(20, 0))
        
        ttk.Button(
            btn_frame,
            text="▶ Executar Extração e Exportar Excel",
            style='Primary.TButton',
            command=self.processar
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

    def selecionar_txt(self):
        arquivo = filedialog.askopenfilename(filetypes=[("Arquivos TXT", "*.txt")])
        if arquivo:
            self.lbl_arquivo.delete(0, tk.END)
            self.lbl_arquivo.insert(0, arquivo)
    
    def linha_valida(self, linha):
        """
        Linha válida:
        |dd/mm/aa|...
        """
        return bool(re.match(r"^\|\d{2}/\d{2}/\d{2}\|", linha))

    

    def processar(self):
        # Validação
        if not self.lbl_arquivo.get():
            messagebox.showwarning("Atenção", "Selecione um arquivo TXT.")
            return
        

        salvar_em = filedialog.asksaveasfilename(
            title="Salvar arquivo Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )    
        
        if not salvar_em:
            return

        dados = []
        nota_atual = None  # guarda a última nota válida

        try:
            with open(self.lbl_arquivo.get(), "r", encoding="latin-1") as f:
                for linha in f:
                    linha = linha.rstrip()

                    partes = [p.strip() for p in linha.split("|")]

                    # proteção mínima
                    if len(partes) < 9:
                        continue

                    # tenta capturar valor contábil (pode existir em linhas filhas)
                    valor_txt = partes[8]
                    valor_txt = valor_txt.replace(".", "").replace(",", ".")

                    try:
                        valor = float(valor_txt)
                    except ValueError:
                        valor = 0.0

                    # linha principal: começa com |dd/mm/aa|
                    if self.linha_valida(linha):
                        numero = partes[4].lstrip("0")
                        data_emissao = partes[5]

                        nota_atual = {
                            "Numero": numero,
                            "Data de Emissao": data_emissao,
                            "Valor": valor
                        }
                        dados.append(nota_atual)

                    # linha complementar: soma ao valor da última nota
                    else:
                        if nota_atual and valor > 0:
                            nota_atual["Valor"] += valor

            if not dados:
                messagebox.showwarning(
                    "Aviso",
                    "Nenhum documento fiscal válido foi encontrado."
                )
                return

            df = pd.DataFrame(dados)

            df["Data de Emissao"] = pd.to_datetime(
                df["Data de Emissao"],
                dayfirst=True,
                errors="coerce"
            )

            df.to_excel(salvar_em, index=False)

            messagebox.showinfo(
                "Sucesso",
                f"Arquivo exportado com sucesso!\n\n"
                f"Registros extraídos: {len(df)}"
            )

        except Exception as e:
            messagebox.showerror("Erro", str(e))  