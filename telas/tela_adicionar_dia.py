import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from dao.producao_dao import ProducaoDAO
from dao.diarista_dao import DiaristaDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path


class TelaAdicionarDia:
    def __init__(self, parent, producao_id, callback_atualizar=None):
        self.parent = parent
        self.producao_id = producao_id
        self.callback_atualizar = callback_atualizar
        self.dao = ProducaoDAO()
        self.diarista_dao = DiaristaDAO()
        self.diaristas = []
        self.divisoes = []

        self.janela = tk.Toplevel(parent)
        self.janela.title("Adicionar Dia de Produção")
        self.janela.geometry("800x800")
        self.janela.configure(bg=CORES['bg_main'])

        try:
            caminho_icone = resource_path("Icones/logo.ico")
            self.janela.iconbitmap(caminho_icone)
        except Exception:
            pass

        self.centralizar()
        self.criar_interface()
        self.carregar_diaristas()

    def centralizar(self):
        self.janela.update_idletasks()
        w = self.janela.winfo_width()
        h = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

    # ─────────────────────────────────────────────────────────────────────────
    # INTERFACE
    # ─────────────────────────────────────────────────────────────────────────

    def criar_interface(self):
        # Frame principal com scroll
        main_canvas = tk.Canvas(self.janela, bg=CORES['bg_card'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.janela, orient="vertical", command=main_canvas.yview)

        scroll_frame = tk.Frame(main_canvas, bg=CORES['bg_card'])
        scroll_frame.bind("<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))

        main_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            if main_canvas.winfo_exists():
                main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        main_canvas.bind("<Destroy>", lambda e: main_canvas.unbind_all("<MouseWheel>"))

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content = tk.Frame(scroll_frame, bg=CORES['bg_card'])
        content.pack(fill="both", expand=True, padx=30, pady=30)

        # Título
        tk.Label(content, text="Adicionar Dia de Produção",
                 font=('Segoe UI', 18, 'bold'),
                 bg=CORES['bg_card'],
                 fg=CORES['primary']).pack(pady=(0, 25))

        # Data
        data_frame = tk.Frame(content, bg=CORES['bg_card'])
        data_frame.pack(fill="x", pady=(0, 20))

        tk.Label(data_frame, text="Data da Produção:",
                 font=('Segoe UI', 10),
                 bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(side="left", padx=(0, 10))

        self.date_producao = DateEntry(
            data_frame, font=('Segoe UI', 11),
            background=CORES['primary'], foreground='white',
            borderwidth=1, date_pattern='dd/mm/yyyy'
        )
        self.date_producao.pack(side="left")

        # Total de sacos do dia
        total_frame = tk.Frame(content, bg=CORES['bg_card'])
        total_frame.pack(fill="x", pady=(0, 20))

        tk.Label(total_frame, text="Total de Sacos Produzidos no Dia:",
                 font=('Segoe UI', 10),
                 bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(side="left", padx=(0, 10))

        self.entry_total_sacos = tk.Entry(total_frame, font=('Segoe UI', 11),
                                           relief='solid', bd=1, width=15)
        self.entry_total_sacos.pack(side="left")

        self.lbl_valor_dia = tk.Label(total_frame, text="",
                                       font=('Segoe UI', 10, 'bold'),
                                       bg=CORES['bg_card'],
                                       fg=CORES['success'])
        self.lbl_valor_dia.pack(side="left", padx=(15, 0))

        self.entry_total_sacos.bind('<KeyRelease>', self.atualizar_valor_dia)

        # Pergunta sobre divisão
        divisao_frame = tk.Frame(content, bg=CORES['bg_card'])
        divisao_frame.pack(fill="x", pady=(0, 20))

        tk.Label(divisao_frame, text="Houve divisão de produção?",
                 font=('Segoe UI', 10),
                 bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(side="left", padx=(0, 15))

        self.var_tem_divisao = tk.BooleanVar(value=False)

        tk.Radiobutton(divisao_frame, text="Não - Todos produziram junto",
                       variable=self.var_tem_divisao, value=False,
                       font=('Segoe UI', 10), bg=CORES['bg_card'],
                       command=self.toggle_divisao).pack(side="left", padx=5)

        tk.Radiobutton(divisao_frame, text="Sim - Houve divisões",
                       variable=self.var_tem_divisao, value=True,
                       font=('Segoe UI', 10), bg=CORES['bg_card'],
                       command=self.toggle_divisao).pack(side="left", padx=5)

        # Frame para produção única (sem divisão)
        self.frame_unica = tk.Frame(content, bg=CORES['bg_card'])

        # Frame para divisões
        self.frame_divisoes = tk.Frame(content, bg=CORES['bg_card'])

        self.criar_frame_producao_unica()
        self.criar_frame_divisoes()

        self.toggle_divisao()

        # Botões finais
        btn_frame = tk.Frame(content, bg=CORES['bg_card'])
        btn_frame.pack(fill="x", pady=(30, 0))

        tk.Button(btn_frame, text="Cancelar",
                  font=('Segoe UI', 10),
                  bg=CORES['text_light'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=25, pady=10,
                  command=self.janela.destroy).pack(side="right", padx=5)

        tk.Button(btn_frame, text="💾 Salvar Dia de Produção",
                  font=('Segoe UI', 10, 'bold'),
                  bg=CORES['success'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=25, pady=10,
                  command=self.salvar).pack(side="right", padx=5)

    # ─────────────────────────────────────────────────────────────────────────
    # FRAME PRODUÇÃO ÚNICA
    # ─────────────────────────────────────────────────────────────────────────

    def criar_frame_producao_unica(self):
        tk.Label(self.frame_unica, text="Buscar e adicionar participantes:",
                 font=('Segoe UI', 11, 'bold'),
                 bg=CORES['bg_card'],
                 fg=CORES['primary']).pack(anchor="w", pady=(10, 5))

        tk.Label(self.frame_unica,
                 text="💡 O valor total do dia será dividido igualmente entre os participantes",
                 font=('Segoe UI', 8, 'italic'),
                 bg=CORES['bg_card'],
                 fg=CORES['text_light']).pack(anchor="w", pady=(0, 10))

        # Campo de busca
        busca_frame = tk.Frame(self.frame_unica, bg=CORES['bg_card'])
        busca_frame.pack(fill="x", pady=(0, 5))

        tk.Label(busca_frame, text="🔍", font=('Segoe UI', 12),
                 bg=CORES['bg_card']).pack(side="left", padx=(0, 5))

        self.var_busca_unica = tk.StringVar()
        entry_busca = tk.Entry(busca_frame, textvariable=self.var_busca_unica,
                               font=('Segoe UI', 10), relief='solid', bd=1)
        entry_busca.pack(side="left", fill="x", expand=True)
        entry_busca.insert(0, "Digite o nome para buscar...")
        entry_busca.config(fg=CORES['text_light'])

        def on_focus_in(e):
            if entry_busca.get() == "Digite o nome para buscar...":
                entry_busca.delete(0, tk.END)
                entry_busca.config(fg=CORES['text_dark'])

        def on_focus_out(e):
            if not entry_busca.get():
                entry_busca.insert(0, "Digite o nome para buscar...")
                entry_busca.config(fg=CORES['text_light'])

        entry_busca.bind("<FocusIn>", on_focus_in)
        entry_busca.bind("<FocusOut>", on_focus_out)

        # Lista de resultados da busca
        tk.Label(self.frame_unica, text="Resultados da busca:",
                 font=('Segoe UI', 9),
                 bg=CORES['bg_card'],
                 fg=CORES['text_dark']).pack(anchor="w", pady=(10, 5))

        lista_frame = tk.Frame(self.frame_unica, bg=CORES['bg_card'])
        lista_frame.pack(fill="both", expand=True)

        scroll_lista = ttk.Scrollbar(lista_frame, orient="vertical")
        scroll_lista.pack(side="right", fill="y")

        self.lista_busca_unica = tk.Listbox(lista_frame, height=6,
                                             font=('Segoe UI', 9),
                                             yscrollcommand=scroll_lista.set,
                                             relief='solid', bd=1)
        self.lista_busca_unica.pack(side="left", fill="both", expand=True)
        scroll_lista.config(command=self.lista_busca_unica.yview)

        # Botão adicionar
        tk.Button(self.frame_unica, text="➕ Adicionar Selecionado",
                  font=('Segoe UI', 9, 'bold'),
                  bg=CORES['secondary'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=15, pady=8,
                  command=self.adicionar_participante_unica).pack(pady=(10, 5))

        # Container de participantes adicionados
        tk.Label(self.frame_unica, text="Participantes selecionados:",
                 font=('Segoe UI', 9, 'bold'),
                 bg=CORES['bg_card'],
                 fg=CORES['primary']).pack(anchor="w", pady=(15, 5))

        self.participantes_container_unica = tk.Frame(self.frame_unica,
                                                      bg='white',
                                                      relief='solid', bd=1)
        self.participantes_container_unica.pack(fill="both", expand=True)

        self.lbl_vazio_unica = tk.Label(self.participantes_container_unica,
                                        text="Nenhum participante adicionado ainda",
                                        font=('Segoe UI', 9, 'italic'),
                                        bg='white',
                                        fg=CORES['text_light'],
                                        pady=20)
        self.lbl_vazio_unica.pack()

        self.diaristas_vars_unica = {}
        self.participantes_ids_unica = set()

        def atualizar_lista_unica(*args):
            termo = self.var_busca_unica.get().lower()
            if termo == "digite o nome para buscar...":
                termo = ""

            self.lista_busca_unica.delete(0, tk.END)
            for diarista in self.diaristas:
                diarista_id, diarista_nome, diarista_cpf = diarista[:3]

                if diarista_id in self.participantes_ids_unica:
                    continue

                if termo in diarista_nome.lower() or termo in diarista_cpf:
                    self.lista_busca_unica.insert(tk.END,
                                                  f"{diarista_nome} - CPF: {diarista_cpf}")

        self.var_busca_unica.trace('w', atualizar_lista_unica)
        atualizar_lista_unica()

    def adicionar_participante_unica(self):
        if not self.lista_busca_unica.curselection():
            messagebox.showwarning("Atenção", "Selecione um diarista da lista!")
            return

        item_selecionado = self.lista_busca_unica.get(self.lista_busca_unica.curselection()[0])

        diarista = None
        for d in self.diaristas:
            if f"{d[1]} - CPF: {d[2]}" == item_selecionado:
                diarista = d
                break

        if not diarista:
            return

        diarista_id, diarista_nome, diarista_cpf = diarista[:3]

        if diarista_id in self.participantes_ids_unica:
            messagebox.showwarning("Atenção", "Este diarista já foi adicionado!")
            return

        self.participantes_ids_unica.add(diarista_id)
        var = tk.BooleanVar(value=True)
        self.diaristas_vars_unica[diarista_id] = var

        if hasattr(self, 'lbl_vazio_unica') and self.lbl_vazio_unica.winfo_exists():
            self.lbl_vazio_unica.destroy()

        linha = tk.Frame(self.participantes_container_unica, bg='white')
        linha.pack(fill="x", padx=10, pady=5)

        tk.Label(linha, text=f"{diarista_nome} - CPF: {diarista_cpf}",
                 font=('Segoe UI', 9), bg='white',
                 anchor='w').pack(side="left", fill="x", expand=True)

        def remover():
            self.participantes_ids_unica.remove(diarista_id)
            self.diaristas_vars_unica.pop(diarista_id, None)
            linha.destroy()

            if len(self.participantes_ids_unica) == 0:
                self.lbl_vazio_unica = tk.Label(self.participantes_container_unica,
                                                text="Nenhum participante adicionado ainda",
                                                font=('Segoe UI', 9, 'italic'),
                                                bg='white',
                                                fg=CORES['text_light'],
                                                pady=20)
                self.lbl_vazio_unica.pack()

            self.var_busca_unica.set(self.var_busca_unica.get())

        tk.Button(linha, text="❌", font=('Segoe UI', 8),
                  bg=CORES['danger'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=8, pady=2,
                  command=remover).pack(side="right")

        self.var_busca_unica.set(self.var_busca_unica.get())

    # ─────────────────────────────────────────────────────────────────────────
    # FRAME DIVISÕES
    # ─────────────────────────────────────────────────────────────────────────

    def criar_frame_divisoes(self):
        tk.Label(self.frame_divisoes, text="Configure as divisões de produção:",
                 font=('Segoe UI', 11, 'bold'),
                 bg=CORES['bg_card'],
                 fg=CORES['primary']).pack(anchor="w", pady=(10, 10))

        self.divisoes_container = tk.Frame(self.frame_divisoes, bg=CORES['bg_card'])
        self.divisoes_container.pack(fill="both", expand=True)

        tk.Button(self.frame_divisoes, text="➕ Adicionar Divisão",
                  font=('Segoe UI', 10),
                  bg=CORES['secondary'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=15, pady=8,
                  command=self.adicionar_divisao).pack(pady=(10, 0))

    def adicionar_divisao(self):
        divisao_id = len(self.divisoes)

        divisao_frame = tk.Frame(self.divisoes_container,
                                 bg=CORES['bg_main'],
                                 relief='solid', bd=1)
        divisao_frame.pack(fill="x", pady=5)

        inner = tk.Frame(divisao_frame, bg=CORES['bg_main'])
        inner.pack(fill="both", expand=True, padx=15, pady=10)

        # Cabeçalho
        header = tk.Frame(inner, bg=CORES['bg_main'])
        header.pack(fill="x", pady=(0, 10))

        tk.Label(header, text=f"Divisão {divisao_id + 1}",
                 font=('Segoe UI', 11, 'bold'),
                 bg=CORES['bg_main'],
                 fg=CORES['primary']).pack(side="left")

        if divisao_id > 0:
            tk.Button(header, text="🗑️ Remover",
                      font=('Segoe UI', 9),
                      bg=CORES['danger'], fg='white',
                      relief='flat', cursor='hand2',
                      padx=10, pady=5,
                      command=lambda: self.remover_divisao(divisao_frame, divisao_id)
                      ).pack(side="right")

        # Quantidade de sacos
        qtd_frame = tk.Frame(inner, bg=CORES['bg_main'])
        qtd_frame.pack(fill="x", pady=(0, 10))

        tk.Label(qtd_frame, text="Quantidade de sacos desta divisão:",
                 font=('Segoe UI', 9),
                 bg=CORES['bg_main']).pack(side="left", padx=(0, 10))

        entry_qtd = tk.Entry(qtd_frame, font=('Segoe UI', 10), width=10)
        entry_qtd.pack(side="left")

        # Descrição
        desc_frame = tk.Frame(inner, bg=CORES['bg_main'])
        desc_frame.pack(fill="x", pady=(0, 10))

        tk.Label(desc_frame, text="Descrição (opcional):",
                 font=('Segoe UI', 9),
                 bg=CORES['bg_main']).pack(side="left", padx=(0, 10))

        entry_desc = tk.Entry(desc_frame, font=('Segoe UI', 10), width=30)
        entry_desc.pack(side="left")

        # Participantes
        tk.Label(inner, text="Buscar e adicionar participantes:",
                 font=('Segoe UI', 9, 'bold'),
                 bg=CORES['bg_main']).pack(anchor="w", pady=(5, 5))

        tk.Label(inner,
                 text="💡 O valor desta divisão será dividido igualmente entre os selecionados",
                 font=('Segoe UI', 8, 'italic'),
                 bg=CORES['bg_main'],
                 fg=CORES['text_light']).pack(anchor="w", pady=(0, 5))

        # Campo de busca
        busca_frame = tk.Frame(inner, bg=CORES['bg_main'])
        busca_frame.pack(fill="x", pady=(0, 5))

        tk.Label(busca_frame, text="🔍", font=('Segoe UI', 11),
                 bg=CORES['bg_main']).pack(side="left", padx=(0, 5))

        var_busca = tk.StringVar()
        entry_busca = tk.Entry(busca_frame, textvariable=var_busca,
                               font=('Segoe UI', 9),
                               relief='solid', bd=1)
        entry_busca.pack(side="left", fill="x", expand=True)

        lista = tk.Listbox(inner, height=5, font=('Segoe UI', 9),
                           relief='solid', bd=1)
        lista.pack(fill="x", pady=(5, 5))

        participantes_container = tk.Frame(inner, bg='white',
                                           relief='solid', bd=1)
        participantes_container.pack(fill="x", pady=(5, 0))

        lbl_vazio = tk.Label(participantes_container,
                             text="Nenhum participante adicionado ainda",
                             font=('Segoe UI', 9, 'italic'),
                             bg='white',
                             fg=CORES['text_light'],
                             pady=15)
        lbl_vazio.pack()

        participantes_vars = {}
        participantes_ids = set()

        def atualizar_lista(*args):
            termo = var_busca.get().lower()
            lista.delete(0, tk.END)
            for d in self.diaristas:
                diarista_id, diarista_nome, diarista_cpf = d[:3]

                if diarista_id in participantes_ids:
                    continue

                if termo in diarista_nome.lower() or termo in diarista_cpf:
                    lista.insert(tk.END, f"{diarista_nome} - CPF: {diarista_cpf}")

        def adicionar_participante():
            if not lista.curselection():
                messagebox.showwarning("Atenção", "Selecione um diarista da lista!")
                return

            item_selecionado = lista.get(lista.curselection()[0])

            diarista = None
            for d in self.diaristas:
                if f"{d[1]} - CPF: {d[2]}" == item_selecionado:
                    diarista = d
                    break

            if not diarista:
                return

            diarista_id, diarista_nome = diarista[0], diarista[1]

            if diarista_id in participantes_ids:
                return

            participantes_ids.add(diarista_id)
            var = tk.BooleanVar(value=True)
            participantes_vars[diarista_id] = var

            if lbl_vazio.winfo_exists():
                lbl_vazio.destroy()

            linha = tk.Frame(participantes_container, bg='white')
            linha.pack(fill="x", padx=10, pady=3)

            tk.Label(linha, text=diarista_nome,
                     font=('Segoe UI', 9),
                     bg='white', width=35,
                     anchor='w').pack(side="left")

            def remover_participante():
                participantes_ids.remove(diarista_id)
                participantes_vars.pop(diarista_id, None)
                linha.destroy()

                if len(participantes_ids) == 0:
                    lbl_vazio_novo = tk.Label(participantes_container,
                                              text="Nenhum participante adicionado ainda",
                                              font=('Segoe UI', 9, 'italic'),
                                              bg='white',
                                              fg=CORES['text_light'],
                                              pady=15)
                    lbl_vazio_novo.pack()

                atualizar_lista()

            tk.Button(linha, text="❌", font=('Segoe UI', 8),
                      bg=CORES['danger'], fg='white',
                      relief='flat', cursor='hand2',
                      padx=6, pady=2,
                      command=remover_participante).pack(side="right")

            atualizar_lista()

        var_busca.trace('w', atualizar_lista)

        tk.Button(inner, text="➕ Adicionar Selecionado",
                  font=('Segoe UI', 9),
                  bg=CORES['secondary'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=12, pady=6,
                  command=adicionar_participante).pack(pady=(5, 10))

        atualizar_lista()

        divisao_data = {
            'frame': divisao_frame,
            'entry_qtd': entry_qtd,
            'entry_desc': entry_desc,
            'participantes_vars': participantes_vars
        }

        self.divisoes.append(divisao_data)

    def remover_divisao(self, frame, divisao_id):
        frame.destroy()
        if divisao_id < len(self.divisoes):
            self.divisoes.pop(divisao_id)
        self.renumerar_divisoes()

    def renumerar_divisoes(self):
        for i, divisao in enumerate(self.divisoes):
            for widget in divisao['frame'].winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Frame):
                            for label in child.winfo_children():
                                if isinstance(label, tk.Label) and "Divisão" in label.cget("text"):
                                    label.config(text=f"Divisão {i + 1}")

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def carregar_diaristas(self):
        self.diaristas = self.diarista_dao.listar(apenas_ativos=True)

    def toggle_divisao(self):
        if self.var_tem_divisao.get():
            self.frame_unica.pack_forget()
            self.frame_divisoes.pack(fill="both", expand=True, pady=(10, 0))
            if not self.divisoes:
                self.adicionar_divisao()
        else:
            self.frame_divisoes.pack_forget()
            self.frame_unica.pack(fill="both", expand=True, pady=(10, 0))
            self.divisoes = []
            for widget in self.divisoes_container.winfo_children():
                widget.destroy()

    def atualizar_valor_dia(self, event=None):
        try:
            total_sacos = int(self.entry_total_sacos.get())
            valor_saco = self.dao.get_valor_saco_atual()
            valor_total = total_sacos * valor_saco
            self.lbl_valor_dia.config(text=f"💰 Valor do dia: R$ {valor_total:.2f}")
        except Exception:
            self.lbl_valor_dia.config(text="")

    # ─────────────────────────────────────────────────────────────────────────
    # SALVAR
    # ─────────────────────────────────────────────────────────────────────────

    def salvar(self):
        # Valida data e total
        try:
            total_sacos = int(self.entry_total_sacos.get())
            if total_sacos <= 0:
                raise ValueError()
        except Exception:
            messagebox.showwarning("Atenção", "Informe um total de sacos válido!")
            return

        data_producao = self.date_producao.get_date().strftime('%Y-%m-%d')
        valor_saco = self.dao.get_valor_saco_atual()

        divisoes_data = []

        if not self.var_tem_divisao.get():
            # ── Produção única ────────────────────────────────────────────────
            selecionados = [d_id for d_id, var in self.diaristas_vars_unica.items() if var.get()]

            if not selecionados:
                messagebox.showwarning("Atenção", "Selecione pelo menos um diarista!")
                return

            # Calcula valor total e divide igualmente
            valor_total_dia = total_sacos * valor_saco
            valor_por_pessoa = round(valor_total_dia / len(selecionados), 2)

            participantes = []
            for d_id in selecionados:
                participantes.append({
                    'diarista_id': d_id,
                    'valor_receber': valor_por_pessoa
                })

            divisoes_data.append({
                'quantidade_sacos': total_sacos,
                'descricao': 'Produção completa',
                'participantes': participantes
            })
        else:
            # ── Com divisões ──────────────────────────────────────────────────
            total_divisoes = 0

            for divisao in self.divisoes:
                try:
                    qtd_sacos = int(divisao['entry_qtd'].get())
                    if qtd_sacos <= 0:
                        raise ValueError()
                except Exception:
                    messagebox.showwarning("Atenção",
                                           "Informe quantidades válidas para todas as divisões!")
                    return

                total_divisoes += qtd_sacos

                selecionados = [d_id for d_id, var in divisao['participantes_vars'].items() if var.get()]

                if not selecionados:
                    messagebox.showwarning("Atenção",
                                           "Cada divisão deve ter pelo menos um participante!")
                    return

                # Calcula valor da divisão e divide igualmente
                valor_divisao = qtd_sacos * valor_saco
                valor_por_pessoa = round(valor_divisao / len(selecionados), 2)

                participantes = []
                for d_id in selecionados:
                    participantes.append({
                        'diarista_id': d_id,
                        'valor_receber': valor_por_pessoa
                    })

                divisoes_data.append({
                    'quantidade_sacos': qtd_sacos,
                    'descricao': divisao['entry_desc'].get().strip() or f"Divisão {len(divisoes_data) + 1}",
                    'participantes': participantes
                })

            if total_divisoes != total_sacos:
                messagebox.showwarning(
                    "Atenção",
                    f"A soma das divisões ({total_divisoes}) não corresponde "
                    f"ao total de sacos ({total_sacos})!"
                )
                return

        # Salva no DAO
        if self.dao.adicionar_dia_producao(self.producao_id, data_producao,
                                           total_sacos, divisoes_data):
            messagebox.showinfo("Sucesso", "Dia de produção adicionado com sucesso!")
            if self.callback_atualizar:
                self.callback_atualizar()
            self.janela.destroy()
        else:
            messagebox.showerror("Erro", "Erro ao adicionar dia de produção!")