import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from tkcalendar import DateEntry
from dao.servico_dao import ServicoDAO
from dao.diarista_dao import DiaristaDAO
from dao.centro_custo_dao import CentroCustoDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path



class TelaNovoServico:
    def __init__(self, parent, callback_atualizar=None, servico_id=None):
        self.parent = parent
        self.callback_atualizar = callback_atualizar
        self.servico_id = servico_id
        self.diaristas_dict = {}
        self.dao = ServicoDAO()
        self.diarista_dao = DiaristaDAO()
        self.centro_custo_dao = CentroCustoDAO()
        
        # Cria janela modal
        self.janela = tk.Toplevel(parent)
        self.janela.title("Editar Serviço" if servico_id else "Novo Serviço")
        self.janela.geometry("660x700")
        self.janela.configure(bg=CORES['bg_main'])
        
        caminho_icone = resource_path("Icones/logo.ico")
        self.janela.iconbitmap(caminho_icone)
        
    
        self.centralizar()
        self.criar_interface()
        self.carregar_combos()
        
        if servico_id:
            self.carregar_dados_servico()

    def centralizar(self):
        self.janela.update_idletasks()
        w = self.janela.winfo_width()
        h = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")    
    
    def criar_interface(self):
        # Frame principal com scroll
        main_canvas = tk.Canvas(self.janela, bg=CORES['bg_card'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.janela, orient="vertical", command=main_canvas.yview)
        
        scroll_frame = tk.Frame(main_canvas, bg=CORES['bg_card'])
        scroll_frame.bind("<Configure>", 
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        
        main_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Conteúdo
        content = tk.Frame(scroll_frame, bg=CORES['bg_card'])
        content.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Título
        tk.Label(
            content,
            text="Editar Serviço" if self.servico_id else "Cadastrar Novo Serviço",
            font=('Segoe UI', 18, 'bold'),
            bg=CORES['bg_card'],
            fg=CORES['primary']
        ).pack(pady=(0, 30))
        
        # Diarista
        tk.Label(
            content,
            text="Diarista: *",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 5))
        
        # Campo de busca
        self.entry_diarista = tk.Entry(
            content,
            font=('Segoe UI', 11),
            relief='solid',
            bd=1
        )
        self.entry_diarista.pack(fill="x", ipady=6)

        # Lista de resultados
        self.lista_diaristas_box = tk.Listbox(
            content,
            font=('Segoe UI', 10),
            height=6,
            relief='solid',
            bd=1
        )
        self.lista_diaristas_box.pack(fill="x", pady=(5, 20))

        self.lista_diaristas_box.bind("<<ListboxSelect>>", self.selecionar_diarista)
        self.entry_diarista.bind("<KeyRelease>", self.filtrar_diaristas)

        
        # ==============================
        # Linha com duas colunas
        # ==============================
        linha_dupla = tk.Frame(content, bg=CORES['bg_card'])
        linha_dupla.pack(fill="x", pady=(0, 20))

        col_esquerda = tk.Frame(linha_dupla, bg=CORES['bg_card'])
        col_esquerda.pack(side="left", fill="x", expand=True, padx=(0, 10))

        col_direita = tk.Frame(linha_dupla, bg=CORES['bg_card'])
        col_direita.pack(side="left", fill="x", expand=True)

        # ==============================
        # Data do Serviço (Esquerda)
        # ==============================
        tk.Label(
            col_esquerda,
            text="Data do Serviço: *",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 5))

        self.date_servico = DateEntry(
            col_esquerda,
            font=('Segoe UI', 11),
            background=CORES['primary'],
            foreground='white',
            borderwidth=1,
            date_pattern='dd/mm/yyyy',
            locale='pt_BR'
        )
        self.date_servico.pack(fill="x", ipady=5)

        # ==============================
        # Centro de Custo (Direita)
        # ==============================
        tk.Label(
            col_direita,
            text="Centro de Custo: *",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 5))

        self.combo_centro_custo = ttk.Combobox(
            col_direita,
            font=('Segoe UI', 10),
            state="readonly"
        )
        self.combo_centro_custo.pack(fill="x", ipady=5)

        
        # Valor
        tk.Label(
            content,
            text="Valor (R$): *",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 5))
        
        self.entry_valor = tk.Entry(
            content,
            font=('Segoe UI', 11),
            relief='solid',
            bd=1
        )
        self.entry_valor.pack(fill="x", ipady=8, pady=(0, 20))
        self.entry_valor.insert(0, "0.00")
        
        # Descrição do Serviço
        tk.Label(
            content,
            text="Descrição do Serviço: *",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 5))
        
        self.text_descricao = tk.Text(
            content,
            font=('Segoe UI', 10),
            relief='solid',
            bd=1,
            height=5,
            wrap='word'
        )
        self.text_descricao.pack(fill="x", pady=(0, 20))
        
        
        # Botões
        btn_frame = tk.Frame(content, bg=CORES['bg_card'])
        btn_frame.pack(fill="x", pady=(10, 0))

        # Frame interno centralizado
        btn_container = tk.Frame(btn_frame, bg=CORES['bg_card'])
        btn_container.pack(anchor="center")

        tk.Button(
            btn_container,
            text="Cancelar",
            font=('Segoe UI', 10),
            bg=CORES['text_light'],
            fg='white',
            relief='flat',
            cursor='hand2',
            padx=25,
            pady=10,
            command=self.janela.destroy
        ).pack(side="left", padx=8)

        tk.Button(
            btn_container,
            text="💾 Salvar Serviço",
            font=('Segoe UI', 10, 'bold'),
            bg=CORES['success'],
            fg='white',
            relief='flat',
            cursor='hand2',
            padx=25,
            pady=10,
            command=self.salvar
        ).pack(side="left", padx=8)

    
    def carregar_combos(self):
        diaristas = self.diarista_dao.listar()
        self.lista_diaristas = diaristas

        # Preenche lista inicialmente
        self.atualizar_listbox(diaristas)

        centros = self.centro_custo_dao.listar()
        self.centros_dict = {c[1]: c[0] for c in centros}
        self.combo_centro_custo['values'] = list(self.centros_dict.keys())



    def filtrar_diaristas(self, event):
        texto = self.entry_diarista.get().lower()

        filtrados = [
            d for d in self.lista_diaristas
            if texto in d[1].lower()
        ]

        self.atualizar_listbox(filtrados)

    def atualizar_listbox(self, lista):
        self.lista_diaristas_box.delete(0, tk.END)

        for d in lista:
            self.lista_diaristas_box.insert(tk.END, f"{d[1]} - CPF: {d[2]}")

    def selecionar_diarista(self, event):
        selecao = self.lista_diaristas_box.curselection()
        if selecao:
            texto = self.lista_diaristas_box.get(selecao[0])
            self.entry_diarista.delete(0, tk.END)
            self.entry_diarista.insert(0, texto)


    
    def carregar_dados_servico(self):
        """Carrega dados do serviço para edição"""
        servico = self.dao.buscar(self.servico_id)
        if not servico:
            messagebox.showerror("Erro", "Serviço não encontrado!")
            self.janela.destroy()
            return
        
        # servico: (id, data_servico, diarista_nome, diarista_cpf, centro_custo, 
        #           valor, descricao, observacoes, diarista_id, centro_custo_id)
        
        # Define diarista
        diarista_texto = f"{servico[2]} - CPF: {servico[3]}"
        if diarista_texto in self.diaristas_dict:
            self.combo_diarista.set(diarista_texto)
        
        # Define data
        try:
            data_obj = datetime.strptime(servico[1], '%Y-%m-%d')
            self.date_servico.set_date(data_obj)
        except:
            pass
        
        # Define centro de custo
        if servico[4] in self.centros_dict:
            self.combo_centro_custo.set(servico[4])
        
        # Define valor
        self.entry_valor.delete(0, tk.END)
        self.entry_valor.insert(0, f"{servico[5]:.2f}")
        
        # Define descrição
        self.text_descricao.delete("1.0", "end")
        self.text_descricao.insert("1.0", servico[6])
        
        # Define observações
        if servico[7]:
            self.text_observacoes.delete("1.0", "end")
            self.text_observacoes.insert("1.0", servico[7])
    
    def salvar(self):
        # =========================
        # VALIDAR DIARISTA
        # =========================
        nome_digitado = self.entry_diarista.get().strip()

        if not nome_digitado:
            messagebox.showwarning("Atenção", "Selecione um diarista!")
            self.entry_diarista.focus()
            return

        diarista_id = None

        for d in self.lista_diaristas:
            texto_formatado = f"{d[1]} - CPF: {d[2]}"
            if nome_digitado == texto_formatado:
                diarista_id = d[0]
                break

        if diarista_id is None:
            messagebox.showwarning("Atenção", "Diarista não cadastrado!")
            self.entry_diarista.focus()
            return


        # =========================
        # VALIDAR CENTRO DE CUSTO
        # =========================
        centro_texto = self.combo_centro_custo.get().strip()

        if not centro_texto:
            messagebox.showwarning("Atenção", "Selecione um centro de custo!")
            self.combo_centro_custo.focus()
            return

        if centro_texto not in self.centros_dict:
            messagebox.showwarning("Atenção", "Centro de custo inválido!")
            self.combo_centro_custo.focus()
            return

        centro_custo_id = self.centros_dict[centro_texto]


        # =========================
        # VALIDAR VALOR
        # =========================
        try:
            valor = float(self.entry_valor.get().replace(',', '.'))
            if valor <= 0:
                raise ValueError()
        except:
            messagebox.showwarning("Atenção", "Informe um valor válido!")
            self.entry_valor.focus()
            return


        # =========================
        # VALIDAR DESCRIÇÃO
        # =========================
        descricao = self.text_descricao.get("1.0", "end-1c").strip()

        if not descricao:
            messagebox.showwarning("Atenção", "Informe a descrição do serviço!")
            self.text_descricao.focus()
            return


        # =========================
        # COLETAR DEMAIS DADOS
        # =========================
        data_servico = self.date_servico.get_date().strftime('%Y-%m-%d')
        


        # =========================
        # SALVAR OU ATUALIZAR
        # =========================
        if self.servico_id:
            sucesso = self.dao.atualizar(
                self.servico_id,
                diarista_id,
                centro_custo_id,
                data_servico,
                valor,
                descricao
            )
            mensagem_sucesso = "Serviço atualizado com sucesso!"
        else:
            sucesso = self.dao.salvar(
                diarista_id,
                centro_custo_id,
                data_servico,
                valor,
                descricao
            )
            mensagem_sucesso = "Serviço cadastrado com sucesso!"

        if sucesso:
            messagebox.showinfo("Sucesso", mensagem_sucesso)
            if self.callback_atualizar:
                self.callback_atualizar()
            self.janela.destroy()
        else:
            messagebox.showerror("Erro", "Erro ao salvar serviço!")
