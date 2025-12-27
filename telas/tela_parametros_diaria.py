import tkinter as tk
from tkinter import ttk, messagebox
from dao.valores_diaria_dao import ValoresDiariaDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path


class TelaParametrosDiaria:
    def __init__(self, parent):
        self.dao = ValoresDiariaDAO()

        self.janela = tk.Toplevel(parent)
        self.janela.title("Parâmetros de Diária")
        self.janela.geometry("500x350")
        self.janela.configure(bg=CORES['bg_main'])

        self.janela.iconbitmap(resource_path("Icones/logo.ico"))
        self.centralizar()
        self.criar_interface()
        self.carregar()

    def centralizar(self):
        self.janela.update_idletasks()
        w, h = 500, 350
        x = (self.janela.winfo_screenwidth() // 2) - (w // 2)
        y = (self.janela.winfo_screenheight() // 2) - (h // 2)
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

    def criar_interface(self):
        container = ttk.Frame(self.janela, padding=20, style="Main.TFrame")
        container.pack(fill="both", expand=True)

        card = ttk.Frame(container, style="Card.TFrame")
        card.pack(fill="both", expand=True)

        ttk.Label(
            card,
            text="Valores Padrão",
            font=('Segoe UI', 14, 'bold'),
            foreground=CORES['primary'],
            background=CORES['bg_card']
        ).pack(anchor="w")

        self.entry_padrao = self.criar_campo(card, "Valor padrão")
        self.entry_diferente = self.criar_campo(card, "Valor diferente")
        self.entry_extra = self.criar_campo(card, "Valor hora extra")

        ttk.Button(
            card,
            text="Salvar parâmetros",
            style="Primary.TButton",
            command=self.salvar
        ).pack(pady=20)


    def criar_campo(self, parent, label):
        ttk.Label(parent, text=label, background=CORES['bg_card']).pack(anchor="w", pady=(10, 0))
        entry = ttk.Entry(parent)
        entry.pack(fill="x")
        return entry

    def carregar(self):
        dados = self.dao.buscar()
        if dados:
            self.entry_padrao.insert(0, dados[1])
            self.entry_diferente.insert(0, dados[2])
            self.entry_extra.insert(0, dados[3])

    def salvar(self):
        self.dao.salvar(
            self.entry_padrao.get(),
            self.entry_diferente.get(),
            self.entry_extra.get()
        )
        messagebox.showinfo("Sucesso", "Parâmetros salvos")
        self.janela.destroy()