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
        
        # Cria janela modal
        self.janela = tk.Toplevel(parent)
        self.janela.title("Nova Produção")
        self.janela.geometry("500x580")
        self.janela.configure(bg=CORES['bg_main'])
        self.janela.resizable(False, False)
        

        caminho_icone = resource_path("Icones/logo.ico")
        self.janela.iconbitmap(caminho_icone)
        
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
        # Frame principal
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
        
        # Frame de campos
        campos_frame = tk.Frame(main_frame, bg=CORES['bg_card'])
        campos_frame.pack(fill="x")
        
        # Nome da produção
        tk.Label(
            campos_frame,
            text="Nome da Produção:",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(anchor="w", pady=(0, 5))
        
        self.entry_nome = tk.Entry(
            campos_frame,
            font=('Segoe UI', 11),
            relief='solid',
            bd=1
        )
        self.entry_nome.pack(fill="x", ipady=8, pady=(0, 20))
        self.entry_nome.focus()
        
        # Data de início
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
        
        # Valor do saco
        valor_frame = tk.Frame(campos_frame, bg=CORES['bg_card'])
        valor_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            valor_frame,
            text="Valor por Saco (R$):",
            font=('Segoe UI', 10),
            bg=CORES['bg_card'],
            fg=CORES['text_dark']
        ).pack(side="left", padx=(0, 10))
        
        valor_atual = self.dao.get_valor_saco_atual()
        
        self.entry_valor_saco = tk.Entry(
            valor_frame,
            font=('Segoe UI', 11),
            relief='solid',
            bd=1,
            width=15
        )
        self.entry_valor_saco.pack(side="left")
        self.entry_valor_saco.insert(0, f"{valor_atual:.2f}")
        
        tk.Label(
            valor_frame,
            text=f"(Atual: R$ {valor_atual:.2f})",
            font=('Segoe UI', 9),
            bg=CORES['bg_card'],
            fg=CORES['text_light']
        ).pack(side="left", padx=(10, 0))
        
        # Observações
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
        
       # Botões
        btn_frame = tk.Frame(main_frame, bg=CORES['bg_card'])
        btn_frame.pack(fill="x", pady=(10, 0))

        # Frame interno para centralizar
        btn_center = tk.Frame(btn_frame, bg=CORES['bg_card'])
        btn_center.pack(anchor="center")

        btn_cancelar = tk.Button(
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
        )
        btn_cancelar.pack(side="left", padx=5)

        btn_salvar = tk.Button(
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
        )
        btn_salvar.pack(side="left", padx=5)

    
    def salvar(self):
        # Valida campos
        nome = self.entry_nome.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome da produção!")
            self.entry_nome.focus()
            return
        
        try:
            valor_saco = float(self.entry_valor_saco.get().replace(',', '.'))
            if valor_saco <= 0:
                raise ValueError()
        except:
            messagebox.showwarning("Atenção", "Informe um valor válido para o saco!")
            self.entry_valor_saco.focus()
            return
        
        data_inicio = self.date_inicio.get_date().strftime('%Y-%m-%d')
        observacoes = self.text_obs.get("1.0", "end-1c").strip()
        
        # Atualiza valor do saco se mudou
        valor_atual = self.dao.get_valor_saco_atual()
        if abs(valor_saco - valor_atual) > 0.001:
            self.dao.atualizar_valor_saco(valor_saco)
        
        # Cria produção
        producao_id = self.dao.criar_producao(nome, data_inicio, observacoes)
        
        if producao_id:
            messagebox.showinfo("Sucesso", "Produção criada com sucesso!")
            if self.callback_atualizar:
                self.callback_atualizar()
            self.janela.destroy()
        else:
            messagebox.showerror("Erro", "Erro ao criar produção!")