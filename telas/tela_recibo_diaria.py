import tkinter as tk
from tkinter import ttk
import tempfile
import os
from PIL import ImageGrab


class TelaReciboDiaria(tk.Toplevel):
    def __init__(self, parent, dados):
        super().__init__(parent)

        self.title("Recibo de Diária")
        self.geometry("600x750")
        self.dados = dados

        self.criar_layout()

    def criar_layout(self):
        self.frame = ttk.Frame(self, padding=30)
        self.frame.pack(fill="both", expand=True)

        ttk.Label(
            self.frame,
            text="RECIBO DE DIÁRIA",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=10)

        self.linha("Diarista", self.dados["nome"])
        self.linha("CPF", self.dados["cpf"])
        self.linha("Centro de custo", self.dados["centro"])
        self.linha("Qtd. Diárias", self.dados["qtd_diarias"])
        self.linha("Valor Diária", f"R$ {self.dados['vlr_unitario']:.2f}")
        if self.dados["tipo_diaria"] == "com_hora":
            self.linha("Qtd. Horas Extras", self.dados["qtd_horas"])
            self.linha("Valor Diárias", f"R$ {self.dados['vlr_diaria_hora']:.2f}")
            self.linha("Valor Horas Extras", f"R$ {self.dados['vlr_horas_extras']:.2f}")
        self.linha("Valor Total", f"R$ {self.dados['valor_total']:.2f}")

        if self.dados.get("descricao"):
            ttk.Label(self.frame, text="Descrição").pack(anchor="w", pady=(10, 0))
            ttk.Label(
                self.frame,
                text=self.dados["descricao"],
                wraplength=500
            ).pack(anchor="w")

        ttk.Separator(self.frame).pack(fill="x", pady=20)

        botoes = ttk.Frame(self.frame)
        botoes.pack()

        ttk.Button(
            botoes,
            text="🖨 Imprimir",
            command=self.imprimir
        ).pack(side="left", padx=10)

        ttk.Button(
            botoes,
            text="💾 Salvar PDF",
            command=self.salvar_pdf
        ).pack(side="left", padx=10)

    def linha(self, label, valor):
        ttk.Label(
            self.frame,
            text=f"{label}: {valor}",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=2)

    # =====================================================
    def imprimir(self):
        from services.recibo_diaria_service import gerar_pdf_recibo_diaria
        gerar_pdf_recibo_diaria(self.dados, salvar=False, abrir=True)


    def salvar_pdf(self):
        from services.recibo_diaria_service import gerar_pdf_recibo_diaria
        gerar_pdf_recibo_diaria(self.dados, salvar=True, abrir=True)


    
