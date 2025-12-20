import tkinter as tk
from tkinter import filedialog, messagebox
import pdfplumber
import pandas as pd
import re
import os


class ExtratorPDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extrator Fiscal PDF → Excel")
        self.root.geometry("600x260")
        self.root.resizable(False, False)

        self.arquivo_pdf = None

        tk.Label(
            root,
            text="Extração Fiscal de Relatório em PDF",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        self.lbl_pdf = tk.Label(root, text="Nenhum PDF selecionado")
        self.lbl_pdf.pack(pady=5)

        tk.Button(
            root,
            text="Selecionar PDF",
            width=40,
            command=self.selecionar_pdf
        ).pack(pady=5)

        tk.Button(
            root,
            text="Processar e Exportar Excel",
            width=40,
            command=self.processar_pdf
        ).pack(pady=15)

    def selecionar_pdf(self):
        arquivo = filedialog.askopenfilename(
            title="Selecionar PDF",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if arquivo:
            self.arquivo_pdf = arquivo
            self.lbl_pdf.config(text=os.path.basename(arquivo))

    def processar_pdf(self):
        if not self.arquivo_pdf:
            messagebox.showwarning("Atenção", "Selecione um arquivo PDF.")
            return

        salvar_em = filedialog.asksaveasfilename(
            title="Salvar Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if not salvar_em:
            return

        dados = []

        # estrutura da nota em processamento
        nota_atual = {
            "Fornecedor": None,
            "Data de Emissao": None,
            "Pedido": None,
            "Quantidade": 0.0
        }

        try:
            with pdfplumber.open(self.arquivo_pdf) as pdf:
                for page in pdf.pages:
                    texto = page.extract_text()
                    if not texto:
                        continue

                    for linha in texto.split("\n"):
                        linha = linha.strip()

                        # ==============================
                        # FORNECEDOR
                        # ==============================
                        if linha.startswith("Fornecedor:"):
                            nota_atual["Fornecedor"] = linha.replace("Fornecedor:", "").strip()

                        # ==============================
                        # DATA DE EMISSÃO
                        # ==============================
                        if "Emissão:" in linha:
                            data = re.search(r"\d{2}/\d{2}/\d{4}", linha)
                            if data:
                                nota_atual["Data de Emissao"] = data.group()

                        # ==============================
                        # LINHA DE PRODUTO
                        # ==============================

                        # QUANTIDADE (primeiro número monetário da linha)
                        if " Kg " in linha or linha.endswith(" Kg") or " Kg" in linha:
                            qtd_match = re.search(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b", linha)
                            if qtd_match:
                                qtd_txt = qtd_match.group()
                                qtd = float(qtd_txt.replace(".", "").replace(",", "."))
                                nota_atual["Quantidade"] += qtd

                        # PEDIDO (formato 000870/01)
                        pedido_match = re.search(r"\b(\d{6})/\d{2}\b", linha)
                        if pedido_match and nota_atual["Pedido"] is None:
                            nota_atual["Pedido"] = pedido_match.group(1)

                        # ==============================
                        # TOTAL DA NOTA (FECHA REGISTRO)
                        # ==============================
                        if linha.startswith("TOTAL DA NOTA:"):
                            numero_nota_match = re.search(
                                r"TOTAL DA NOTA:\s+\d+\s+/\s+(\d+)", linha
                            )

                            valor_txt = linha.split()[-1]
                            valor = float(valor_txt.replace(".", "").replace(",", "."))

                            dados.append({
                                "Numero": numero_nota_match.group(1) if numero_nota_match else None,
                                "Pedido": nota_atual["Pedido"],
                                "Data de Emissao": nota_atual["Data de Emissao"],
                                "Fornecedor": nota_atual["Fornecedor"],
                                "Quantidade": nota_atual["Quantidade"],
                                "Valor": valor
                            })

                            # reset para próxima nota
                            nota_atual = {
                                "Fornecedor": None,
                                "Data de Emissao": None,
                                "Pedido": None,
                                "Quantidade": 0.0
                            }

            if not dados:
                messagebox.showwarning("Aviso", "Nenhuma nota encontrada no PDF.")
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
                f"Extração concluída com sucesso!\n\n"
                f"Notas extraídas: {len(df)}"
            )

        except Exception as e:
            messagebox.showerror("Erro", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = ExtratorPDFApp(root)
    root.mainloop()
