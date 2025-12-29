import tkinter as tk
from tkinter import ttk, messagebox
import os
from dao.diaria_dao import DiariaDAO
from telas.tela_emitir_diaria import TelaEmitirDiaria
from telas.tela_recibo_diaria import TelaReciboDiaria
from utils.auxiliares import CORES, resource_path
from PIL import Image, ImageTk 


class DiariasEmitidasEmbed:
    def __init__(self, parent_frame, sistema_fiscal):
        self.parent_frame = parent_frame
        self.sistema_fiscal = sistema_fiscal
        self.dao = DiariaDAO()

        self.criar_interface()
        self.atualizar_lista()

    def criar_interface(self):
        for w in self.parent_frame.winfo_children():
            w.destroy()

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

        right_header = ttk.Frame(header_container, style='Main.TFrame')
        right_header.pack(side="right")

        caminho_icone = resource_path("Icones/diarias_azul.png")
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
            text="Diarias Emitidas",
            font=('Segoe UI', 18, 'bold'),
            background=CORES['bg_main'],
            foreground=CORES['text_dark']
        ).pack(anchor="w")

        ttk.Label(
            title_frame,
            text="Gestão e emissão de diárias",
            font=('Segoe UI', 9),
            background=CORES['bg_main'],
            foreground=CORES['text_light']
        ).pack(anchor="w")    

        buttons_frame = ttk.Frame(right_header, style='Main.TFrame')
        buttons_frame.pack(side="left")

        ttk.Button(
            buttons_frame,
            text="➕ Emitir Diária",
            style="Add.TButton",
            command=self.abrir_emissao
        ).pack(pady=5, padx=5, side="right")

        ttk.Button(
            buttons_frame,
            text="🗑 Excluir Diária",
            style="Danger.TButton",
            command=self.excluir_diaria
        ).pack(pady=5, padx=5, side="right")

        ttk.Button(
            buttons_frame,
            text="👁️Visualizar",
            style="Primary.TButton",
            command=self.abrir_recibo
        ).pack(pady=5, padx=5, side="right")

        # 🔍 Busca por digitação
        self.var_busca = tk.StringVar()
        busca = ttk.Entry(main_frame, textvariable=self.var_busca)
        busca.pack(fill="x", pady=10)
        busca.bind("<KeyRelease>", lambda e: self.atualizar_lista())

        # 📊 Tabela
        self.tree = ttk.Treeview(
            main_frame,
            columns=("nome", "cpf", "valor", "data"),
            show="headings",
            height=15
        )

        self.tree.heading("nome", text="Diarista")
        self.tree.heading("cpf", text="CPF")
        self.tree.heading("valor", text="Valor Total")
        self.tree.heading("data", text="Data")

        self.tree.column("valor", anchor="e")

        self.tree.pack(fill="both", expand=True)


    # =====================================================
    def atualizar_lista(self):
        filtro = self.var_busca.get()

        self.tree.delete(*self.tree.get_children())

        for d in self.dao.listar_diarias(filtro):
            self.tree.insert(
                "",
                "end",
                values=(
                    d["diarista"],
                    d["cpf"],
                    f"R$ {d['vlr_total']:.2f}".replace(".", ","),
                    d["data_emissao"]
                ),
                tags=(str(d["id"]), d["caminho_arquivo"])
            )


    def abrir_emissao(self):
        # 🔁 Passa callback para atualizar a lista
        TelaEmitirDiaria(
            parent=self.parent_frame,
            callback_atualizar=self.atualizar_lista
        )

    def abrir_recibo(self):
        item = self.tree.focus()
        if not item:
            messagebox.showwarning("Atenção", "Selecione uma diária.")
            return

        tags = self.tree.item(item, "tags")

        if not tags:
            messagebox.showerror("Erro", "Identificação da diária não encontrada.")
            return

        id_diaria = tags[0]  # agora só precisamos do ID

        dados = self.dao.buscar_diaria_por_id(id_diaria)
        if not dados:
            messagebox.showerror("Erro", "Não foi possível carregar a diária.")
            return

        from telas.tela_recibo_diaria import TelaReciboDiaria
        TelaReciboDiaria(self.parent_frame, dados)



    def excluir_diaria(self):
        item = self.tree.focus()
        if not item:
            messagebox.showwarning("Atenção", "Selecione uma diária.")
            return

        tags = self.tree.item(item, "tags")

        if not tags or len(tags) < 2:
            messagebox.showerror(
                "Erro",
                "Não foi possível identificar os dados da diária selecionada."
            )
            return

        id_diaria = tags[0]
        caminho_pdf = tags[1]

        confirmar = messagebox.askyesno(
            "Confirmação",
            "Tem certeza que deseja excluir esta diária?\n\nEssa ação não poderá ser desfeita."
        )

        if not confirmar:
            return

        try:
            self.dao.excluir_diaria(id_diaria)

            if caminho_pdf and os.path.exists(caminho_pdf):
                os.remove(caminho_pdf)

            self.atualizar_lista()

            messagebox.showinfo("Sucesso", "Diária excluída com sucesso.")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir diária:\n{e}")
