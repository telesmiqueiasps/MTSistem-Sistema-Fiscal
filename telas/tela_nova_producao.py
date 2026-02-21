import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry
from dao.producao_dao import ProducaoDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path


class TelaNovaProducao:
    def __init__(self, parent, callback_atualizar=None):
        self.parent = parent
        self.callback_atualizar = callback_atualizar
        self.dao = ProducaoDAO()

        # Cache de centros de custo: [{'id': ..., 'centro': ...}, ...]
        self._centros = []

        # Cria janela modal
        self.janela = tk.Toplevel(parent)
        self.janela.title("Nova Produção")
        self.janela.geometry("500x560")
        self.janela.configure(bg=CORES['bg_main'])
        self.janela.resizable(False, False)

        try:
            caminho_icone = resource_path("Icones/logo.ico")
            self.janela.iconbitmap(caminho_icone)
        except Exception:
            pass

        self.centralizar()
        self.criar_interface()

    def centralizar(self):
        self.janela.update_idletasks()
        w = self.janela.winfo_width()
        h = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

    def criar_interface(self):
        main_frame = tk.Frame(self.janela, bg=CORES['bg_main'])
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Título
        tk.Label(
            main_frame,
            text="Criar Nova Produção",
            font=('Segoe UI', 18, 'bold'),
            bg=CORES['bg_card'],
            fg=CORES['primary']
        ).pack(pady=(0, 25))

        campos_frame = tk.Frame(main_frame, bg=CORES['bg_card'])
        campos_frame.pack(fill="x")

        # ── Centro de Custo ───────────────────────────────────────────────────
        tk.Label(
            campos_frame,
            text="Centro de Custo:",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 5))

        self._centros = self.dao.listar_centros_custo()

        if not self._centros:
            tk.Label(
                campos_frame,
                text="⚠️ Nenhum centro de custo cadastrado.",
                font=('Segoe UI', 9),
                bg=CORES['bg_card'],
                fg=CORES.get('danger', 'red')
            ).pack(anchor="w", pady=(0, 20))
            self._combo_centro = None
        else:
            nomes_centros = [c['centro'] for c in self._centros]

            self._combo_centro = ttk.Combobox(
                campos_frame,
                values=nomes_centros,
                font=('Segoe UI', 11),
                state="readonly",
                width=38
            )
            self._combo_centro.pack(anchor="w", pady=(0, 20), ipady=4)
            self._combo_centro.current(0)   # seleciona o primeiro por padrão

        # ── Data de Início ────────────────────────────────────────────────────
        tk.Label(
            campos_frame,
            text="Data de Início:",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 5))

        self.date_inicio = DateEntry(
            campos_frame,
            font=('Segoe UI', 11),
            width=20,
            background=CORES['primary'],
            foreground='white',
            borderwidth=1,
            date_pattern='dd/mm/yyyy',
            locale='pt_BR'
        )
        self.date_inicio.pack(anchor="w", pady=(0, 20))

        # ── Valor por Saco ────────────────────────────────────────────────────
        valor_frame = tk.Frame(campos_frame, bg=CORES['bg_card'])
        valor_frame.pack(fill="x", pady=(0, 20))

        tk.Label(
            valor_frame,
            text="Valor por Saco (R$):",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(side="left", padx=(0, 10))

        self.entry_valor_saco = tk.Entry(
            valor_frame,
            font=('Segoe UI', 11),
            relief='solid',
            bd=1,
            width=15
        )
        self.entry_valor_saco.pack(side="left")
        self.entry_valor_saco.insert(0, "0.45")  # Default value

        tk.Label(
            valor_frame,
            text="(valor independente por produção)",
            font=('Segoe UI', 9),
            bg=CORES['bg_card'],
            fg=CORES['text_light']
        ).pack(side="left", padx=(10, 0))

        # ── Observações ───────────────────────────────────────────────────────
        tk.Label(
            campos_frame,
            text="Observações (opcional):",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 5))

        self.text_obs = tk.Text(
            campos_frame,
            font=('Segoe UI', 10),
            relief='solid',
            bd=1,
            height=4
        )
        self.text_obs.pack(fill="x", pady=(0, 20))

        # ── Botões ────────────────────────────────────────────────────────────
        btn_frame = tk.Frame(main_frame, bg=CORES['bg_card'])
        btn_frame.pack(fill="x", pady=(10, 0))

        btn_center = tk.Frame(btn_frame, bg=CORES['bg_card'])
        btn_center.pack(anchor="center")

        tk.Button(
            btn_center,
            text="Cancelar",
            font=('Segoe UI', 10),
            bg=CORES['text_light'],
            fg='white',
            relief='flat',
            cursor='hand2',
            padx=25,
            pady=10,
            command=self.janela.destroy
        ).pack(side="left", padx=5)

        tk.Button(
            btn_center,
            text="💾 Criar Produção",
            font=('Segoe UI', 10, 'bold'),
            bg=CORES['success'],
            fg='white',
            relief='flat',
            cursor='hand2',
            padx=25,
            pady=10,
            command=self.salvar
        ).pack(side="left", padx=5)

    # ─────────────────────────────────────────────────────────────────────────

    def _centro_selecionado(self):
        """Retorna o dict {id, centro} do item selecionado no combo, ou None."""
        if not self._combo_centro or not self._centros:
            return None
        idx = self._combo_centro.current()
        if idx < 0:
            return None
        return self._centros[idx]

    def salvar(self):
        # Valida centro de custo
        centro = self._centro_selecionado()
        if centro is None:
            messagebox.showwarning(
                "Atenção",
                "Selecione um centro de custo antes de continuar.\n"
                "Caso não existam opções, cadastre um centro de custo primeiro."
            )
            return

        # Valida valor do saco
        try:
            valor_saco = float(self.entry_valor_saco.get().replace(',', '.'))
            if valor_saco <= 0:
                raise ValueError()
        except Exception:
            messagebox.showwarning("Atenção", "Informe um valor válido para o saco!")
            self.entry_valor_saco.focus()
            return

        data_inicio = self.date_inicio.get_date().strftime('%Y-%m-%d')
        observacoes = self.text_obs.get("1.0", "end-1c").strip()

        # Cria produção com valor_saco específico
        producao_id = self.dao.criar_producao(
            centro_custo_id=centro['id'],
            data_inicio=data_inicio,
            valor_saco=valor_saco,  # ← valor específico desta produção
            observacoes=observacoes
        )

        if producao_id:
            messagebox.showinfo("Sucesso", "Produção criada com sucesso!")
            if self.callback_atualizar:
                self.callback_atualizar()
            self.janela.destroy()
        else:
            messagebox.showerror("Erro", "Erro ao criar produção!")