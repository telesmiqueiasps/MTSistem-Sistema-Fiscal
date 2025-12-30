import tkinter as tk
from tkinter import ttk, messagebox
from dao.empresa_dao import EmpresaDAO
from utils.constantes import CORES

class TelaEmpresa(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.dao = EmpresaDAO()
        self.empresa = self.dao.buscar_empresa()

        self.title("Cadastro da Empresa")
        self.geometry("600x550")
        self.configure(bg=CORES['bg_main'])


        self.vars = {}
        self.criar_interface()

        if self.empresa:
            self.preencher_campos()

    def criar_interface(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        titulo = "Editar Empresa" if self.empresa else "Cadastrar Empresa"
        ttk.Label(
            frame,
            text=titulo,
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(0, 20))

        self.criar_campo(frame, "Razão Social", "razao_social")
        self.criar_campo(frame, "Nome Fantasia", "nome_fantasia")
        self.criar_campo(frame, "CNPJ", "cnpj")
        self.criar_campo(frame, "Inscrição Estadual", "inscricao_estadual")
        self.criar_campo(frame, "Endereço", "endereco")
        self.criar_campo(frame, "CEP", "cep")
        self.criar_campo(frame, "Cidade", "cidade")
        self.criar_campo(frame, "UF", "uf")
        self.criar_campo(frame, "Contato", "contato")

        ttk.Button(
            frame,
            text="💾 Salvar",
            style="Primary.TButton",
            command=self.salvar
        ).pack(pady=20)

    def criar_campo(self, parent, label, chave):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=5)

        ttk.Label(frame, text=label).pack(anchor="w")

        var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(fill="x")

        self.vars[chave] = var

    def preencher_campos(self):
        for chave, var in self.vars.items():
            var.set(self.empresa.get(chave, ""))

    def salvar(self):
        dados = {chave: var.get().strip() for chave, var in self.vars.items()}

        if not dados["razao_social"] or not dados["cnpj"]:
            messagebox.showwarning(
                "Atenção",
                "Razão Social e CNPJ são obrigatórios."
            )
            return

        try:
            if self.empresa:
                dados["id"] = self.empresa["id"]
                self.dao.atualizar_empresa(dados)
                msg = "Empresa atualizada com sucesso!"
            else:
                self.dao.salvar_empresa(dados)
                msg = "Empresa cadastrada com sucesso!"

            messagebox.showinfo("Sucesso", msg)
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar empresa:\n{e}")
