import tkinter as tk
from tkinter import ttk, messagebox
from dao.empresa_dao import EmpresaDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path
from PIL import Image, ImageTk

class TelaEmpresa:

    def __init__(self, parent):
        self.dao = EmpresaDAO()
        self.empresa = self.dao.buscar_empresa()
        self.janela = tk.Toplevel(parent)
        self.janela.title("Cadastro da Empresa")
        self.janela.geometry("600x600")
        self.janela.configure(bg=CORES['bg_main'])

        caminho_icone = resource_path("Icones/logo.ico")
        self.janela.iconbitmap(caminho_icone)

        self.vars = {}
        self.centralizar()
        self.criar_interface()

        if self.empresa:
            self.preencher_campos()

    def centralizar(self):
        self.janela.update_idletasks()
        w = self.janela.winfo_width()
        h = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

    def criar_interface(self):
        container = ttk.Frame(self.janela, padding=30, style="Main.TFrame")
        container.pack(fill="both", expand=True, pady=(0, 8))

        # Header
        header_frame = ttk.Frame(container, style='Main.TFrame')
        header_frame.pack(fill="x", pady=(0, 8))

        header_container = ttk.Frame(header_frame, style='Main.TFrame')
        header_container.pack(fill="x")

        left_header = ttk.Frame(header_container, style='Main.TFrame')
        left_header.pack(side="left")

        caminho_icone = resource_path("Icones/editar_empresa_azul.png")
        img = Image.open(caminho_icone)
        img = img.resize((32, 32), Image.LANCZOS)
        self.icon_header = ImageTk.PhotoImage(img)

        ttk.Label(left_header, image=self.icon_header, background=CORES['bg_main']).pack(side="left", padx=(0, 15))

        titulo = "Editar Empresa" if self.empresa else "Cadastrar Empresa"
        ttk.Label(
            left_header,
            text=titulo,
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")

        # Card principal
        card = ttk.Frame(container, padding=20, style="Card.TFrame")
        card.pack(fill="x")

        # Campos em linha única (largos)
        self.criar_campo_largo(card, "Razão Social", "razao_social")
        self.criar_campo_largo(card, "Nome Fantasia", "nome_fantasia")

        # Linha dupla: CNPJ + Inscrição Estadual
        self.criar_linha_dupla(
            card,
            ("CNPJ/CPF", "cnpj"),
            ("Inscrição Estadual", "inscricao_estadual")
        )

        self.criar_campo_largo(card, "Endereço", "endereco")

        # Linha dupla: CEP + Cidade
        self.criar_linha_dupla(
            card,
            ("CEP", "cep"),
            ("Cidade", "cidade")
        )

        # Linha dupla: UF + Contato
        self.criar_linha_dupla(
            card,
            ("UF", "uf"),
            ("Contato", "contato")
        )

        # Botão salvar
        ttk.Button(
            card,
            text="💾 Salvar",
            style="Primary.TButton",
            command=self.salvar
        ).pack(pady=20)


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
            self.janela.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar empresa:\n{e}")

    def criar_campo_largo(self, parent, label, chave):
        """Campo que ocupa a linha inteira"""
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(fill="x", pady=8)

        ttk.Label(frame, text=label, background=CORES['bg_card'], foreground=CORES['text_dark']).pack(anchor="w")
        
        var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(fill="x", pady=(4, 0))
        
        self.vars[chave] = var


    def criar_linha_dupla(self, parent, campo1, campo2):
        """
        Cria dois campos lado a lado
        campo1 e campo2 = (label_texto, chave_no_dict)
        """
        linha = ttk.Frame(parent, style="Card.TFrame")
        linha.pack(fill="x", pady=8)

        # Coluna esquerda
        col_esq = ttk.Frame(linha, style="Card.TFrame")
        col_esq.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Label(col_esq, text=campo1[0], background=CORES['bg_card'], foreground=CORES['text_dark']).pack(anchor="w")
        var1 = tk.StringVar()
        entry1 = ttk.Entry(col_esq, textvariable=var1)
        entry1.pack(fill="x", pady=(4, 0))
        self.vars[campo1[1]] = var1

        # Coluna direita
        col_dir = ttk.Frame(linha, style="Card.TFrame")
        col_dir.pack(side="right", fill="x", expand=True, padx=(10, 0))

        ttk.Label(col_dir, text=campo2[0], background=CORES['bg_card'], foreground=CORES['text_dark']).pack(anchor="w")
        var2 = tk.StringVar()
        entry2 = ttk.Entry(col_dir, textvariable=var2)
        entry2.pack(fill="x", pady=(4, 0))
        self.vars[campo2[1]] = var2