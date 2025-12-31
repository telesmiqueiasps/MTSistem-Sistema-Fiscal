import tkinter as tk
from tkinter import ttk, messagebox
from dao.diaria_dao import DiariaDAO
import os
from datetime import datetime
from utils.auxiliares import resource_path
from utils.constantes import CORES


class TelaEmitirDiaria:
    def __init__(self, parent, callback_atualizar=None):
        self.parent = parent
        self.dao = DiariaDAO()
        self.callback_atualizar = callback_atualizar

        self.janela = tk.Toplevel(parent)
        self.janela.title("Emitir Diária")
        self.janela.geometry("600x650")
        self.janela.configure(bg=CORES['bg_main'])
        
        self.tipo_diaria = tk.StringVar()
        self.diaristas = {}
        self.centros = {}

        self.janela.iconbitmap(resource_path("Icones/logo.ico"))
        self.centralizar()
        self.criar_interface()

    def centralizar(self):
        self.janela.update_idletasks()
        w, h = 600, 650
        x = (self.janela.winfo_screenwidth() // 2) - (w // 2)
        y = (self.janela.winfo_screenheight() // 2) - (h // 2)
        self.janela.geometry(f"{w}x{h}+{x}+{y}")   

    def criar_interface(self):
        container = ttk.Frame(self.janela, padding=20, style="Main.TFrame")
        container.pack(fill="both", expand=True)

        self.criar_selecao_tipo(container)

        self.form_area = ttk.Frame(container, style="Main.TFrame", padding=15)
        self.form_area.pack(fill="both", expand=True, pady=10)

    # =====================================================
    def criar_selecao_tipo(self, parent):
        box = ttk.Frame(parent, style="Main.TFrame", padding=10)
        box.pack(fill="x", pady=(0, 10))

        ttk.Radiobutton(
            box,
            text="Diária COM horas extras",
            style="Custom.TCheckbutton",
            variable=self.tipo_diaria,
            value="com_hora",
            command=self.atualizar_formulario
        ).pack(side="left", padx=10)

        ttk.Radiobutton(
            box,
            text="Diária SEM horas extras",
            style="Custom.TCheckbutton",
            variable=self.tipo_diaria,
            value="sem_hora",
            command=self.atualizar_formulario
        ).pack(side="left", padx=10)

    def atualizar_formulario(self):
        for w in self.form_area.winfo_children():
            w.destroy()

        if self.tipo_diaria.get() == "com_hora":
            self.form_com_horas_extras()
        elif self.tipo_diaria.get() == "sem_hora":
            self.form_sem_horas_extras()

    def text_area(self, parent, label, height=3, row=0, col=0, colspan=1):
        frame = tk.Frame(parent, bg=CORES['bg_card'])
        frame.grid(row=row, column=col, columnspan=colspan, sticky="ew", padx=5, pady=5)

        tk.Label(frame, text=label, background=CORES['bg_card']).pack(anchor="w")

        text = tk.Text(frame, height=height, wrap="word")
        text.pack(fill="x", pady=(0, 10))

        return text

    # =====================================================
    def campos_comuns(self, parent):
        self.carregar_diaristas()
        self.carregar_centros()

        # Configurar grid
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        # Linha 0: Diarista (ocupa 2 colunas)
        self.campo_diarista_com_busca(parent, row=0, col=0, colspan=2)
        
        # Linha 1: CPF | Centro de custo
        self.entry_cpf = self.entry(parent, "CPF", readonly=True, row=1, col=0)
        self.combo_centro = self.combo(parent, "Centro de custo", list(self.centros.keys()), row=1, col=1)
        
        # Linha 2: Qtd diárias
        self.entry_qtd = self.entry(parent, "Quantidade de diárias", row=2, col=0)

    # =====================================================
    def form_com_horas_extras(self):
        self.campos_comuns(self.form_area)

        # Linha 2 col 1: Tipo de valor
        self.combo_tipo_valor = self.combo(
            self.form_area,
            "Tipo de valor",
            ["Valor padrão", "Valor diferente"],
            row=2, col=1
        )
        self.combo_tipo_valor.bind("<<ComboboxSelected>>", self.aplicar_valor_diaria)

        # Linha 3: Valor unitário | Valor total
        self.entry_vlr_unit = self.entry(self.form_area, "Valor unitário", row=3, col=0)
        self.entry_total = self.entry(self.form_area, "Valor total", readonly=True, row=3, col=1)
        
        # Linha 4: Descrição (ocupa 2 colunas)
        self.text_descricao = self.text_area(
            self.form_area, "Descrição", height=4, row=4, col=0, colspan=2
        )

        # sempre que mudar centro de custo, atualiza descrição
        self.combo_centro.bind("<<ComboboxSelected>>", self.atualizar_descricao_padrao)

        self.bind_calculos()

        # Linha 5: Botão (ocupa 2 colunas)
        self.botao_gerar(self.form_area, row=5)

    def form_sem_horas_extras(self):
        self.campos_comuns(self.form_area)

        # Linha 2 col 1: Valor da diária
        self.entry_vlr_unit = self.entry(self.form_area, "Valor da diária", row=2, col=1)
        
        # Linha 3: Valor total
        self.entry_total = self.entry(self.form_area, "Valor total", readonly=True, row=3, col=0)
        
        # Linha 4: Descrição (ocupa 2 colunas)
        self.text_descricao = self.text_area(
            self.form_area, "Descrição", height=4, row=4, col=0, colspan=2
        )

        self.bind_calculos()

        # Linha 5: Botão (ocupa 2 colunas)
        self.botao_gerar(self.form_area, row=5)

    # =====================================================
    def atualizar_descricao_padrao(self, event=None):
        if self.tipo_diaria.get() != "com_hora":
            return

        centro = self.combo_centro.get()
        if not centro:
            return

        descricao = f"Serviço prestado na produção de {centro}"

        self.text_descricao.delete("1.0", tk.END)
        self.text_descricao.insert(tk.END, descricao)

    def bind_calculos(self):
        self.entry_qtd.var.trace_add("write", self.calcular_total)
        self.entry_vlr_unit.var.trace_add("write", self.calcular_total)

    def to_float(self, valor):
        return float(str(valor).replace(",", "."))


    # =====================================================
    def campo_diarista_com_busca(self, parent, row=0, col=0, colspan=1):
        frame = tk.Frame(parent, bg=CORES['bg_card'])
        frame.grid(row=row, column=col, columnspan=colspan, sticky="ew", padx=5, pady=5)

        tk.Label(frame, text="Diarista", background=CORES['bg_card']).pack(anchor="w")

        self.var_busca = tk.StringVar()
        self.entry_busca = ttk.Entry(frame, textvariable=self.var_busca)
        self.entry_busca.pack(fill="x", pady=(0, 5))

        self.listbox = tk.Listbox(frame, height=4)
        self.listbox.pack(fill="x", pady=(0, 10))

        self.entry_busca.bind("<KeyRelease>", self.filtrar_diaristas)
        self.listbox.bind("<<ListboxSelect>>", self.selecionar_diarista)

    def filtrar_diaristas(self, event=None):
        texto = self.var_busca.get().lower()
        self.listbox.delete(0, tk.END)

        for nome in self.diaristas:
            if texto in nome.lower():
                self.listbox.insert(tk.END, nome)

    def selecionar_diarista(self, event=None):
        if not self.listbox.curselection():
            return

        nome = self.listbox.get(self.listbox.curselection())
        self.var_busca.set(nome)
        self.listbox.delete(0, tk.END)

        diarista_id = self.diaristas[nome]
        cpf = self.dao.buscar_cpf_diarista(diarista_id)

        self.entry_cpf.configure(state="normal")
        self.entry_cpf.var.set(cpf)
        self.entry_cpf.configure(state="readonly")

    # =====================================================
    def carregar_diaristas(self):
        self.diaristas.clear()
        for id_, nome in self.dao.listar_diaristas():
            self.diaristas[nome] = id_

    def carregar_centros(self):
        self.centros.clear()
        for id_, centro in self.dao.listar_centros_custo():
            self.centros[centro] = id_


    def calcular_total(self, *args):
        try:
            qtd_diarias = self.to_float(self.entry_qtd.var.get())
            valor_unit = self.to_float(self.entry_vlr_unit.var.get())

            if qtd_diarias <= 0 or valor_unit <= 0:
                return

            total = qtd_diarias * valor_unit

            if self.tipo_diaria.get() == "com_hora":
                valores = self.dao.buscar_valores_diaria()
                if not valores:
                    return

                _, _, valor_hora_extra, horas_por_diaria = valores

                horas_extras = qtd_diarias * self.to_float(horas_por_diaria)
                total += horas_extras * self.to_float(valor_hora_extra)

            self.entry_total.configure(state="normal")
            self.entry_total.var.set(f"{total:.2f}".replace(".", ","))
            self.entry_total.configure(state="readonly")

        except Exception:
            pass        

    def aplicar_valor_diaria(self, event=None):
        valores = self.dao.buscar_valores_diaria()
        if not valores:
            return

        valor_padrao, valor_diferente, _, _ = valores

        valor = valor_padrao if self.combo_tipo_valor.get() == "Valor padrão" else valor_diferente

        valor = float(str(valor).replace(",", "."))

        self.entry_vlr_unit.var.set(f"{valor:.2f}")

    # =====================================================
    def botao_gerar(self, parent, row=0):
        btn_frame = tk.Frame(parent, bg=CORES['bg_card'])
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            btn_frame,
            text="🧾 Gerar Diária",
            style="Primary.TButton",
            command=self.gerar_diaria
        ).pack()

    def gerar_diaria(self):
        try:
            nome = self.var_busca.get()
            if not nome:
                messagebox.showwarning("Atenção", "Selecione um diarista.")
                return

            cpf = self.entry_cpf.var.get()
            qtd_diarias = self.to_float(self.entry_qtd.var.get())
            valor_unit = self.to_float(self.entry_vlr_unit.var.get())
            valor_total = self.to_float(self.entry_total.var.get())

            centro = self.combo_centro.get()
            descricao = self.text_descricao.get("1.0", "end").strip()

            tipo_diaria = self.tipo_diaria.get()
            tipo_valor = self.combo_tipo_valor.get() if tipo_diaria == "com_hora" else "Valor direto"

            vlr_diaria_hora = 0
            vlr_horas_extras = 0
            qtd_horas = 0

            if tipo_diaria == "com_hora":
                _, _, valor_hora_extra, horas_por_diaria = self.dao.buscar_valores_diaria()

                horas_por_diaria = self.to_float(horas_por_diaria)
                valor_hora_extra = self.to_float(valor_hora_extra)

                # ✔ Quantidade total de horas
                qtd_horas = qtd_diarias * horas_por_diaria

                # ✔ Montante total das diárias
                vlr_diaria_hora = qtd_diarias * valor_unit

                # ✔ Montante total das horas extras
                vlr_horas_extras = qtd_horas * valor_hora_extra


            dados_db = {
                "tipo_diaria": tipo_diaria,
                "diarista": nome,
                "cpf": cpf,
                "qtd_diarias": qtd_diarias,
                "tipo_valor": tipo_valor,
                "vlr_diaria_hora": vlr_diaria_hora,
                "vlr_horas_extras": vlr_horas_extras,
                "qtd_horas": qtd_horas,
                "vlr_unitario": valor_unit,
                "centro_custo": centro,
                "vlr_total": valor_total,
                "descricao": descricao,
                "data_emissao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "caminho_arquivo": None
            }

            id_diaria = self.dao.salvar_diaria(dados_db)

            if self.callback_atualizar:
                self.callback_atualizar()

            # 🔑 IMPORTANTE: usar o ROOT do sistema
            from telas.tela_recibo_diaria import TelaReciboDiaria

            dados_recibo = {
                "id": id_diaria,
                "nome": nome,
                "cpf": cpf,
                "centro": centro,
                "qtd_diarias": qtd_diarias,
                "vlr_unitario": valor_unit,
                "vlr_diaria_hora": vlr_diaria_hora,
                "vlr_horas_extras": vlr_horas_extras,
                "valor_total": valor_total,
                "descricao": descricao,
                "data_emissao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tipo_diaria": tipo_diaria
            }

            messagebox.showinfo("Sucesso", "Diária gerada com sucesso!")
            # ⬇️ Usa o root principal
            recibo = TelaReciboDiaria(self.parent, dados_recibo)
            recibo.janela.lift()
            recibo.janela.focus_force()

            # Agora sim pode fechar a janela de emissão
            self.janela.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar diária:\n{e}")



    # =====================================================
    def entry(self, parent, label, readonly=False, row=0, col=0):
        frame = tk.Frame(parent, bg=CORES['bg_card'])
        frame.grid(row=row, column=col, sticky="ew", padx=5, pady=5)

        tk.Label(frame, text=label, background=CORES['bg_card']).pack(anchor="w")

        var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=var)
        if readonly:
            entry.configure(state="readonly")

        entry.pack(fill="x", pady=(0, 10))
        entry.var = var
        return entry

    def combo(self, parent, label, valores, row=0, col=0):
        frame = tk.Frame(parent, bg=CORES['bg_card'])
        frame.grid(row=row, column=col, sticky="ew", padx=5, pady=5)

        tk.Label(frame, text=label, background=CORES['bg_card']).pack(anchor="w")

        combo = ttk.Combobox(frame, values=valores, state="readonly")
        combo.pack(fill="x", pady=(0, 10))
        return combo