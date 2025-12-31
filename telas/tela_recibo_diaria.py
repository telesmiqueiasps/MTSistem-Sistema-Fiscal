import tkinter as tk
from tkinter import ttk
import tempfile
import os
from PIL import ImageGrab, Image, ImageTk
from utils.constantes import CORES
from utils.auxiliares import resource_path


class TelaReciboDiaria:
    def __init__(self, parent, dados):

        self.janela = tk.Toplevel(parent)
        self.janela.title("Resumo de Diária")
        self.janela.geometry("600x650")
        self.janela.configure(bg=CORES['bg_main'])

        caminho_icone = resource_path("Icones/logo.ico")
        self.janela.iconbitmap(caminho_icone)

        self.dados = dados

        self.centralizar()
        self.criar_layout()

    def centralizar(self):
        self.janela.update_idletasks()
        w = self.janela.winfo_width()
        h = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")    

    def criar_layout(self):
        self.frame = ttk.Frame(self.janela, padding=30, style="Main.TFrame")
        self.frame.pack(fill="both", expand=True)

        # =========================
        # Título
        # =========================
        ttk.Label(
            self.frame,
            text="RESUMO DE DIÁRIA",
            background=CORES['bg_main'],
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(0, 15))

        ttk.Separator(self.frame).pack(fill="x", pady=20)

        # =========================
        # Destaque Diarista
        # =========================
        frame_diarista = ttk.Frame(self.frame, style="Main.TFrame")
        frame_diarista.pack(fill="x", pady=(0, 10))

        ttk.Label(
            frame_diarista,
            text="DIARISTA",
            font=("Segoe UI", 9, "bold"),
            foreground=CORES["secondary"],
            background=CORES["bg_main"]
        ).pack(anchor="w")

        ttk.Label(
            frame_diarista,
            text=self.dados["nome"],
            font=("Segoe UI", 13, "bold"),
            foreground=CORES["primary"],
            background=CORES["bg_main"]
        ).pack(anchor="w")

        # =========================
        # Dados principais
        # =========================
        self.linha("CPF", self.dados["cpf"])
        self.linha("Centro de custo", self.dados["centro"])
        self.linha("Qtd. Diárias", self.dados["qtd_diarias"])
        self.linha("Valor Diária", f"R$ {self.dados['vlr_unitario']:.2f}")

        if self.dados["tipo_diaria"] == "com_hora":
            self.linha("Qtd. Horas Extras", self.dados["qtd_horas"])
            self.linha("Valor Diárias", f"R$ {self.dados['vlr_diaria_hora']:.2f}")
            self.linha("Valor Horas Extras", f"R$ {self.dados['vlr_horas_extras']:.2f}")

        # =========================
        # Destaque Valor Total
        # =========================
        frame_total = ttk.Frame(self.frame, padding=12, style="Main.TFrame")
        frame_total.pack(fill="x", pady=15)

        ttk.Label(
            frame_total,
            text="VALOR TOTAL",
            font=("Segoe UI", 10, "bold"),
            foreground=CORES["secondary"],
            background=CORES["bg_main"]
        ).pack()

        ttk.Label(
            frame_total,
            text=f"R$ {self.dados['valor_total']:.2f}",
            font=("Segoe UI", 18, "bold"),
            foreground="#0A7D00",
            background=CORES["bg_main"]
        ).pack()

        # =========================
        # Descrição
        # =========================
        if self.dados.get("descricao"):
            ttk.Label(
                self.frame,
                text="Descrição",
                font=("Segoe UI", 10, "bold"),
                background=CORES['bg_main']
            ).pack(anchor="w", pady=(5, 0))

            ttk.Label(
                self.frame,
                text=self.dados["descricao"],
                background=CORES['bg_main'],
                wraplength=500
            ).pack(anchor="w")

        self.linha("Data de Emissão", self.dados["data_emissao"])

        # =========================
        # Ações
        # =========================
        ttk.Separator(self.frame).pack(fill="x", pady=20)

        botoes = ttk.Frame(self.frame, style="Main.TFrame")
        botoes.pack()

        ttk.Button(
            botoes,
            text="🖨 Imprimir Recibo",
            style="Add.TButton",
            command=self.imprimir
        ).pack(side="left", padx=10)

        ttk.Button(
            botoes,
            text="💾 Salvar PDF",
            style="Danger.TButton",
            command=self.salvar_pdf
        ).pack(side="left", padx=10)

    def linha(self, label, valor):
        frame = ttk.Frame(self.frame, style="Main.TFrame")
        frame.pack(fill="x", pady=2)

        ttk.Label(
            frame,
            text=f"{label}:",
            font=("Segoe UI", 10, "bold"),
            background=CORES['bg_main']
        ).pack(side="left")

        ttk.Label(
            frame,
            text=f" {valor}",
            font=("Segoe UI", 10),
            background=CORES['bg_main']
        ).pack(side="left")


    # =====================================================
    def imprimir(self):
        from services.recibo_diaria_service import gerar_pdf_recibo_diaria
        gerar_pdf_recibo_diaria(self.dados, salvar=False, abrir=True)


    def salvar_pdf(self):
        from services.recibo_diaria_service import gerar_pdf_recibo_diaria
        gerar_pdf_recibo_diaria(self.dados, salvar=True, abrir=True)


    
