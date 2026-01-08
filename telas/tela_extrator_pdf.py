import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pdfplumber
import pandas as pd
from PIL import Image, ImageTk
from utils.constantes import CORES
from utils.auxiliares import resource_path


# =========================
# VERSÃO EMBED DO EXTRATOR PDF
# =========================
class ExtratorFiscalPDFAppEmbed:
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

        caminho_icone = resource_path("Icones/pdf_azul.png")
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
            text="Extração PDF → Excel",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")

        ttk.Label(
            title_frame,
            text="Extraia informações fiscais de relatórios em PDF",
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

        self.lbl_pdf = self.criar_campo(
            card,
            "Arquivo PDF (.pdf)",
            "Selecione o relatório fiscal em PDF para processamento",
            self.selecionar_pdf
        )

        separator = ttk.Frame(card, height=2, style='Card.TFrame')
        separator.pack(fill="x", pady=30)

        btn_frame = ttk.Frame(card, style='Card.TFrame')
        btn_frame.pack(fill="x")

        ttk.Button(
            btn_frame,
            text="▶ Executar Extração e Exportar Excel",
            style='Primary.TButton',
            command=self.processar
        ).pack(fill="x", ipady=8)

    def criar_campo(self, parent, titulo, subtitulo, comando):
        campo_frame = ttk.Frame(parent, style='Card.TFrame')
        campo_frame.pack(fill="x")

        ttk.Label(
            campo_frame,
            text=titulo,
            font=('Segoe UI', 11, 'bold'),
            background=CORES['bg_card'],
            foreground=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(
            campo_frame,
            text=subtitulo,
            font=('Segoe UI', 9),
            background=CORES['bg_card'],
            foreground=CORES['text_light']
        ).pack(anchor="w", pady=(0, 12))

        input_frame = ttk.Frame(campo_frame, style='Card.TFrame')
        input_frame.pack(fill="x")

        entry = ttk.Entry(input_frame, font=('Segoe UI', 10))
        entry.pack(side="left", fill="x", expand=True, ipady=8)

        ttk.Button(
            input_frame,
            text="📁 Selecionar Arquivo",
            style='Secondary.TButton',
            command=comando
        ).pack(side="right", padx=(15, 0))

        return entry

    def selecionar_pdf(self):
        arquivo = filedialog.askopenfilename(
            title="Selecione o arquivo PDF",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
        )
        if arquivo:
            self.lbl_pdf.delete(0, tk.END)
            self.lbl_pdf.insert(0, arquivo)

    def processar(self):
        caminho_pdf = self.lbl_pdf.get()
        if not caminho_pdf:
            messagebox.showwarning("Atenção", "Selecione um arquivo PDF.")
            return

        salvar_em = filedialog.asksaveasfilename(
            title="Salvar planilha como",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if not salvar_em:
            return

        dados = []
        nota_atual = {
            "Fornecedor": None,
            "Data de Emissao": None,
            "Pedido": None,
            "Quantidade": 0.0,
            "Despesa Acessoria": 0.0
        }


        try:
            with pdfplumber.open(caminho_pdf) as pdf:
                for page in pdf.pages:
                    texto = page.extract_text()
                    if not texto:
                        continue

                    for linha in texto.split("\n"):
                        linha = linha.strip()

                        if linha.startswith("Fornecedor:"):
                            nota_atual["Fornecedor"] = linha.replace("Fornecedor:", "").strip()

                        if "Emissão:" in linha:
                            data = re.search(r"\d{2}/\d{2}/\d{4}", linha)
                            if data:
                                nota_atual["Data de Emissao"] = data.group()

                        # Linha de item começa com código numérico
                        if re.match(r"^\d{3,}", linha):
                            numeros = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", linha)

                            if numeros:
                                qtd = float(numeros[0].replace(".", "").replace(",", "."))
                                nota_atual["Quantidade"] += qtd

                        if re.search(r"Despesa\s+Acess[oó]ria", linha, re.IGNORECASE):
                            valor_match = re.search(r"\d{1,3}(?:\.\d{3})*,\d{2}", linha)
                            if valor_match:
                                nota_atual["Despesa Acessoria"] = float(
                                    valor_match.group().replace(".", "").replace(",", ".")
                                )


                        pedido_match = re.search(r"\b(\d{6})/\d{2}\b", linha)
                        if pedido_match and nota_atual["Pedido"] is None:
                            nota_atual["Pedido"] = pedido_match.group(1)

                        if linha.startswith("TOTAL DA NOTA:"):
                            numero_match = re.search(r"/\s*(\d+)", linha)

                            valores = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", linha)

                            if len(valores) >= 2:
                                total = float(valores[-1].replace(".", "").replace(",", "."))
                                despesa_acessoria = float(valores[-2].replace(".", "").replace(",", "."))
                            else:
                                total = 0.0
                                despesa_acessoria = 0.0

                            dados.append({
                                "Numero": numero_match.group(1) if numero_match else None,
                                "Pedido": nota_atual["Pedido"],
                                "Data de Emissao": nota_atual["Data de Emissao"],
                                "Fornecedor": nota_atual["Fornecedor"],
                                "Quantidade": nota_atual["Quantidade"],
                                "Despesa Acessoria": despesa_acessoria,
                                "Valor": total
                            })

                            nota_atual = {
                                "Fornecedor": None,
                                "Data de Emissao": None,
                                "Pedido": None,
                                "Quantidade": 0.0,
                                "Despesa Acessoria": 0.0
                            }



            if not dados:
                messagebox.showwarning("Aviso", "Nenhuma nota encontrada no arquivo PDF.")
                return

            df = pd.DataFrame(dados)
            df["Data de Emissao"] = pd.to_datetime(df["Data de Emissao"], dayfirst=True, errors="coerce")
            df.to_excel(salvar_em, index=False)

            messagebox.showinfo(
                "Sucesso", 
                f"Extração concluída com sucesso!\n\nNotas extraídas: {len(df)}\nArquivo salvo em:\n{salvar_em}"
            )

        except Exception as e:
            messagebox.showerror("Erro ao processar", f"Ocorreu um erro durante a extração:\n\n{str(e)}")

