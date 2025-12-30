import tkinter as tk
from tkinter import ttk, messagebox
from dao.centro_custo_dao import CentroCustoDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path
from PIL import Image, ImageTk

class CentrosCustoEmbed:
    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.dao = CentroCustoDAO()
        self.atual_id = None
        self.criar_interface()
        self.carregar()

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
        caminho_icone = resource_path("Icones/centro_custo_azul.png")
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
            text="Centros de Custo",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")
        
        ttk.Label(
            title_frame,
            text="Cadastro de centros de custo utilizados nas diárias",
            font=('Segoe UI', 9),
            background=CORES['bg_main'],
            foreground=CORES['text_light']
        ).pack(anchor="w")

        card = ttk.Frame(main_frame, style="Card.TFrame", padding=30)
        card.pack(fill="both", expand=True)

        self.lista = tk.Listbox(card, height=12)
        self.lista.pack(fill="x")
        self.lista.bind("<<ListboxSelect>>", self.selecionar)

        ttk.Label(
            card,
            text="Nome do Centro de Custo:",
            font=('Segoe UI', 9),
            foreground=CORES['text_dark'],
            background=CORES['bg_card']
        ).pack(anchor="w")

        self.entry = ttk.Entry(card)
        self.entry.pack(fill="x", pady=15)

        ttk.Button(card, text="💾 Salvar", style="Primary.TButton", command=self.salvar)\
            .pack(pady=10)

        ttk.Button(card, text="🗑 Excluir", style="Danger.TButton", command=self.excluir)\
            .pack(pady=20)
        
        

    def carregar(self):
        self.lista.delete(0, tk.END)
        self.dados = self.dao.listar()
        for c in self.dados:
            self.lista.insert(tk.END, c[1])

    def selecionar(self, _):
        idx = self.lista.curselection()
        if not idx:
            return
        self.atual_id = self.dados[idx[0]][0]
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.dados[idx[0]][1])

    def salvar(self):
        valor = self.entry.get().strip()
        if not valor:
            messagebox.showwarning("Atenção", "Preencha o campo com o nome do Centro de Custo.")
            return
        if self.atual_id:
            self.dao.atualizar(self.atual_id, valor)
        else:
            self.dao.salvar(valor)
        self.carregar()
        messagebox.showinfo("Sucesso", "Centro de Custo salvo com sucesso.")
        self.entry.delete(0, tk.END)

    def excluir(self):
        if not self.atual_id:
            messagebox.showinfo("Atenção", "É necessário selecionar um centro de custo para excluir.")
            return
        if self.atual_id and messagebox.askyesno("Confirmar", "Excluir centro de custo?"):
            self.dao.excluir(self.atual_id)
            self.atual_id = None
            self.entry.delete(0, tk.END)
            self.carregar()

   