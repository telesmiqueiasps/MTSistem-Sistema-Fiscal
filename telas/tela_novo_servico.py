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
        self.dao = ServicoDAO()
        self.diarista_dao = DiaristaDAO()
        self.centro_custo_dao = CentroCustoDAO()

        # Lista completa de diaristas ativos e set dos selecionados {id: (nome, cpf)}
        self._lista_diaristas = []
        self._selecionados = {}   # {diarista_id: {'nome': ..., 'cpf': ...}}

        self.janela = tk.Toplevel(parent)
        self.janela.title("Editar Serviço" if servico_id else "Novo Serviço")
        self.janela.geometry("680x680")
        self.janela.configure(bg=CORES['bg_main'])
        self.janela.resizable(False, True)

        try:
            self.janela.iconbitmap(resource_path("Icones/logo.ico"))
        except Exception:
            pass

        self.centralizar()
        self.criar_interface()
        self.carregar_combos()

        if servico_id:
            self.carregar_dados_servico()

    # ─────────────────────────────────────────────────────────────────────────

    def centralizar(self):
        self.janela.update_idletasks()
        w, h = 680, 680
        x = (self.janela.winfo_screenwidth()  - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

    # ─────────────────────────────────────────────────────────────────────────
    # INTERFACE
    # ─────────────────────────────────────────────────────────────────────────

    def criar_interface(self):
        # Scroll externo
        outer = tk.Frame(self.janela, bg=CORES['bg_card'])
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=CORES['bg_card'], highlightthickness=0)
        vsb    = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scroll_frame = tk.Frame(canvas, bg=CORES['bg_card'])
        scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        c = tk.Frame(scroll_frame, bg=CORES['bg_card'])
        c.pack(fill="both", expand=True, padx=35, pady=30)

        # Título
        tk.Label(c,
                 text="Editar Serviço" if self.servico_id else "Cadastrar Novo Serviço",
                 font=('Segoe UI', 16, 'bold'),
                 bg=CORES['bg_card'], fg=CORES['primary']).pack(anchor="w", pady=(0, 20))

        # ── Diaristas ─────────────────────────────────────────────────────────
        tk.Label(c, text="Diaristas: *",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(anchor="w")

        diarista_card = tk.Frame(c, bg=CORES['bg_main'],
                                 relief='solid', bd=1)
        diarista_card.pack(fill="x", pady=(4, 15))

        # Busca
        busca_row = tk.Frame(diarista_card, bg=CORES['bg_main'])
        busca_row.pack(fill="x", padx=10, pady=(10, 6))

        tk.Label(busca_row, text="🔍",
                 bg=CORES['bg_main'], fg=CORES['text_dark']).pack(side="left")
        self.entry_busca_diarista = ttk.Entry(busca_row, width=30)
        self.entry_busca_diarista.pack(side="left", padx=(5, 0), fill="x", expand=True)
        self.entry_busca_diarista.bind("<KeyRelease>", self._filtrar_diaristas)

        # Dois painéis lado a lado
        paineis = tk.Frame(diarista_card, bg=CORES['bg_main'])
        paineis.pack(fill="x", padx=10, pady=(0, 10))

        # Disponíveis
        tk.Label(paineis, text="Disponíveis",
                 font=('Segoe UI', 8, 'bold'),
                 bg=CORES['bg_main'], fg=CORES['text_light']).grid(
                     row=0, column=0, sticky="w")

        tk.Label(paineis, text="Selecionados",
                 font=('Segoe UI', 8, 'bold'),
                 bg=CORES['bg_main'], fg=CORES['text_light']).grid(
                     row=0, column=2, sticky="w")

        self.lb_disponiveis = tk.Listbox(
            paineis, height=6, width=28,
            font=('Segoe UI', 9), selectmode="extended",
            relief='solid', bd=1,
            activestyle='dotbox'
        )
        self.lb_disponiveis.grid(row=1, column=0, padx=(0, 5))

        # Botões do meio
        btn_mid = tk.Frame(paineis, bg=CORES['bg_main'])
        btn_mid.grid(row=1, column=1, padx=5)

        tk.Button(btn_mid, text="▶",
                  font=('Segoe UI', 11), bg=CORES['primary'], fg='white',
                  relief='flat', cursor='hand2', width=3,
                  command=self._adicionar_selecionados).pack(pady=4)

        tk.Button(btn_mid, text="◀",
                  font=('Segoe UI', 11), bg=CORES['danger'], fg='white',
                  relief='flat', cursor='hand2', width=3,
                  command=self._remover_selecionados).pack(pady=4)

        self.lb_selecionados = tk.Listbox(
            paineis, height=6, width=28,
            font=('Segoe UI', 9), selectmode="extended",
            relief='solid', bd=1,
            activestyle='dotbox'
        )
        self.lb_selecionados.grid(row=1, column=2, padx=(5, 0))

        # Label de rateio
        self.lbl_rateio = tk.Label(diarista_card, text="",
                                    font=('Segoe UI', 9, 'italic'),
                                    bg=CORES['bg_main'],
                                    fg=CORES['text_light'])
        self.lbl_rateio.pack(anchor="e", padx=10, pady=(0, 8))

        # ── Linha data + centro ───────────────────────────────────────────────
        linha = tk.Frame(c, bg=CORES['bg_card'])
        linha.pack(fill="x", pady=(0, 15))

        col_e = tk.Frame(linha, bg=CORES['bg_card'])
        col_e.pack(side="left", fill="x", expand=True, padx=(0, 10))

        col_d = tk.Frame(linha, bg=CORES['bg_card'])
        col_d.pack(side="left", fill="x", expand=True)

        tk.Label(col_e, text="Data do Serviço: *",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(anchor="w")
        self.date_servico = DateEntry(
            col_e, font=('Segoe UI', 11), width=18,
            background=CORES['primary'], foreground='white',
            borderwidth=1, date_pattern='dd/mm/yyyy', locale='pt_BR'
        )
        self.date_servico.pack(anchor="w", ipady=4)

        tk.Label(col_d, text="Centro de Custo: *",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(anchor="w")
        self.combo_centro = ttk.Combobox(col_d, font=('Segoe UI', 10),
                                          state="readonly")
        self.combo_centro.pack(fill="x", ipady=4)

        # ── Valor ─────────────────────────────────────────────────────────────
        tk.Label(c, text="Valor Total (R$): *",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(anchor="w")
        self.entry_valor = tk.Entry(c, font=('Segoe UI', 11),
                                     relief='solid', bd=1)
        self.entry_valor.pack(fill="x", ipady=7, pady=(2, 15))
        self.entry_valor.insert(0, "0.00")
        self.entry_valor.bind("<KeyRelease>", self._atualizar_rateio)

        # ── Descrição ─────────────────────────────────────────────────────────
        tk.Label(c, text="Descrição do Serviço: *",
                 font=('Segoe UI', 10), bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(anchor="w")
        self.text_descricao = tk.Text(c, font=('Segoe UI', 10),
                                       relief='solid', bd=1,
                                       height=4, wrap='word')
        self.text_descricao.pack(fill="x", pady=(2, 20))

        # ── Botões ────────────────────────────────────────────────────────────
        btn_frame = tk.Frame(c, bg=CORES['bg_card'])
        btn_frame.pack(anchor="center", pady=(5, 0))

        tk.Button(btn_frame, text="Cancelar",
                  font=('Segoe UI', 10), bg=CORES['text_light'], fg='white',
                  relief='flat', cursor='hand2', padx=25, pady=10,
                  command=self.janela.destroy).pack(side="left", padx=8)

        tk.Button(btn_frame, text="💾 Salvar Serviço",
                  font=('Segoe UI', 10, 'bold'), bg=CORES['success'], fg='white',
                  relief='flat', cursor='hand2', padx=25, pady=10,
                  command=self.salvar).pack(side="left", padx=8)

    # ─────────────────────────────────────────────────────────────────────────
    # COMBOS / DIARISTAS
    # ─────────────────────────────────────────────────────────────────────────

    def carregar_combos(self):
        self._lista_diaristas = self.diarista_dao.listar(apenas_ativos=True)
        self._atualizar_lb_disponiveis()

        centros = self.centro_custo_dao.listar()
        self._centros_dict = {c[1]: c[0] for c in centros}
        self.combo_centro['values'] = list(self._centros_dict.keys())

    def _atualizar_lb_disponiveis(self, filtro=""):
        self.lb_disponiveis.delete(0, tk.END)
        for d in self._lista_diaristas:
            if d[0] in self._selecionados:
                continue
            if filtro and filtro not in d[1].lower():
                continue
            self.lb_disponiveis.insert(tk.END, f"{d[1]} — {d[2]}")
            self.lb_disponiveis.itemconfig(tk.END, foreground=CORES['text_dark'])

    def _filtrar_diaristas(self, _=None):
        self._atualizar_lb_disponiveis(
            self.entry_busca_diarista.get().strip().lower())

    def _indices_disponiveis_visiveis(self):
        """Retorna os diaristas atualmente exibidos no lb_disponiveis."""
        filtro = self.entry_busca_diarista.get().strip().lower()
        return [
            d for d in self._lista_diaristas
            if d[0] not in self._selecionados
            and (not filtro or filtro in d[1].lower())
        ]

    def _adicionar_selecionados(self):
        indices = self.lb_disponiveis.curselection()
        if not indices:
            return
        visiveis = self._indices_disponiveis_visiveis()
        for i in indices:
            if i < len(visiveis):
                d = visiveis[i]
                self._selecionados[d[0]] = {'nome': d[1], 'cpf': d[2]}
        self._atualizar_lb_disponiveis(
            self.entry_busca_diarista.get().strip().lower())
        self._atualizar_lb_selecionados()
        self._atualizar_rateio()

    def _remover_selecionados(self):
        indices = self.lb_selecionados.curselection()
        if not indices:
            return
        ids = list(self._selecionados.keys())
        for i in sorted(indices, reverse=True):
            if i < len(ids):
                del self._selecionados[ids[i]]
        self._atualizar_lb_disponiveis(
            self.entry_busca_diarista.get().strip().lower())
        self._atualizar_lb_selecionados()
        self._atualizar_rateio()

    def _atualizar_lb_selecionados(self):
        self.lb_selecionados.delete(0, tk.END)
        for info in self._selecionados.values():
            self.lb_selecionados.insert(tk.END, f"{info['nome']} — {info['cpf']}")

    def _atualizar_rateio(self, _=None):
        qtd = len(self._selecionados)
        if qtd == 0:
            self.lbl_rateio.config(text="")
            return
        try:
            valor = float(self.entry_valor.get().replace(',', '.'))
        except ValueError:
            self.lbl_rateio.config(text="")
            return
        rateio = valor / qtd
        self.lbl_rateio.config(
            text=f"Rateio: R$ {rateio:,.2f} por diarista ({qtd} selecionado{'s' if qtd > 1 else ''})"
                 .replace(',', 'X').replace('.', ',').replace('X', '.')
        )

    # ─────────────────────────────────────────────────────────────────────────
    # EDIÇÃO — carrega dados existentes
    # ─────────────────────────────────────────────────────────────────────────

    def carregar_dados_servico(self):
        servico = self.dao.buscar(self.servico_id)
        if not servico:
            messagebox.showerror("Erro", "Serviço não encontrado!")
            self.janela.destroy()
            return

        # Data
        try:
            self.date_servico.set_date(
                datetime.strptime(servico['data_servico'], '%Y-%m-%d').date())
        except Exception:
            pass

        # Centro de custo
        if servico['centro_custo'] in self._centros_dict:
            self.combo_centro.set(servico['centro_custo'])

        # Valor
        self.entry_valor.delete(0, tk.END)
        self.entry_valor.insert(0, f"{servico['valor']:.2f}")

        # Descrição
        self.text_descricao.delete("1.0", tk.END)
        self.text_descricao.insert("1.0", servico['descricao'])

        # Diaristas
        for p in servico['diaristas']:
            self._selecionados[p['id']] = {'nome': p['nome'], 'cpf': p['cpf']}

        self._atualizar_lb_disponiveis()
        self._atualizar_lb_selecionados()
        self._atualizar_rateio()

    # ─────────────────────────────────────────────────────────────────────────
    # SALVAR
    # ─────────────────────────────────────────────────────────────────────────

    def salvar(self):
        if not self._selecionados:
            messagebox.showwarning("Atenção", "Selecione ao menos um diarista!")
            return

        centro_txt = self.combo_centro.get().strip()
        if not centro_txt or centro_txt not in self._centros_dict:
            messagebox.showwarning("Atenção", "Selecione um centro de custo!")
            return

        try:
            valor = float(self.entry_valor.get().replace(',', '.'))
            if valor <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um valor válido!")
            return

        descricao = self.text_descricao.get("1.0", "end-1c").strip()
        if not descricao:
            messagebox.showwarning("Atenção", "Informe a descrição do serviço!")
            return

        centro_custo_id = self._centros_dict[centro_txt]
        data_servico    = self.date_servico.get_date().strftime('%Y-%m-%d')
        diarista_ids    = list(self._selecionados.keys())

        if self.servico_id:
            ok = self.dao.atualizar(
                self.servico_id, centro_custo_id, data_servico,
                valor, descricao, diarista_ids)
            msg = "Serviço atualizado com sucesso!"
        else:
            ok = self.dao.salvar(
                centro_custo_id, data_servico, valor, descricao, diarista_ids)
            msg = "Serviço cadastrado com sucesso!"

        if ok:
            messagebox.showinfo("Sucesso", msg)
            if self.callback_atualizar:
                self.callback_atualizar()
            self.janela.destroy()
        else:
            messagebox.showerror("Erro", "Erro ao salvar serviço!")