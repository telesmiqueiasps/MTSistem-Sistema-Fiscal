# telas/tela_gestao_empresas.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from dao.empresa_central_dao import EmpresaCentralDAO
from utils.constantes import CORES
from utils.auxiliares import resource_path
import os


class TelaGestaoEmpresas:
    """Tela completa de gestão de empresas com listagem e permissões."""
    
    def __init__(self, parent):
        self.parent = parent
        self.dao = EmpresaCentralDAO()
        self._empresas_cache = []

        self.janela = tk.Toplevel(parent)
        self.janela.title("Gestão de Empresas")
        self.janela.geometry("900x650")
        self.janela.configure(bg='#fafbfc')

        try:
            self.janela.iconbitmap(resource_path("Icones/logo.ico"))
        except Exception:
            pass

        self.centralizar()
        self.criar_interface()
        self.carregar_empresas()

    def centralizar(self):
        self.janela.update_idletasks()
        w, h = 900, 650
        x = (self.janela.winfo_screenwidth() - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

    def criar_interface(self):
        main = tk.Frame(self.janela, bg='#fafbfc')
        main.pack(fill="both", expand=True, padx=35, pady=30)

        # ══════════════════════════════════════════════════════════════════════
        # HEADER
        # ══════════════════════════════════════════════════════════════════════
        header = tk.Frame(main, bg='#fafbfc')
        header.pack(fill="x", pady=(0, 25))

        tk.Label(header, text="Gestão de Empresas",
                 font=('Segoe UI', 18),
                 foreground='#1a1a1a',
                 bg='#fafbfc').pack(side="left")

        tk.Button(header, text="+ Nova Empresa",
                  font=('Segoe UI', 9, 'bold'),
                  bg=CORES['primary'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=18, pady=9,
                  command=self.nova_empresa).pack(side="right")

        # ══════════════════════════════════════════════════════════════════════
        # CARD PRINCIPAL
        # ══════════════════════════════════════════════════════════════════════
        shadow = tk.Frame(main, bg='#e9ecef', height=2)
        shadow.pack(fill="x")

        card = tk.Frame(main, bg='white')
        card.pack(fill="both", expand=True)

        # Treeview
        self._criar_treeview(card)

        # Ações
        acoes = tk.Frame(card, bg='white')
        acoes.pack(fill="x", padx=20, pady=(10, 20))

        tk.Button(acoes, text="✏️ Renomear",
                  font=('Segoe UI', 9),
                  bg='#6c757d', fg='white',
                  relief='flat', cursor='hand2',
                  padx=15, pady=7,
                  command=self.renomear_empresa).pack(side="left", padx=(0, 6))

        tk.Button(acoes, text="👥 Gerenciar Usuários",
                  font=('Segoe UI', 9, 'bold'),
                  bg=CORES['secondary'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=15, pady=7,
                  command=self.gerenciar_usuarios).pack(side="left", padx=(0, 6))

        tk.Button(acoes, text="🗑️ Excluir",
                  font=('Segoe UI', 9),
                  bg=CORES['danger'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=15, pady=7,
                  command=self.excluir_empresa).pack(side="left")

        tk.Label(acoes, text="Duplo clique para gerenciar usuários",
                 font=('Segoe UI', 8),
                 foreground='#adb5bd',
                 bg='white').pack(side="right")

        self.tree.bind("<Double-1>", lambda _: self.gerenciar_usuarios())

    def _criar_treeview(self, parent):
        tree_frame = tk.Frame(parent, bg='white')
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(15, 0))

        # Style minimalista
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Empresas.Treeview",
                       background="white",
                       foreground='#212529',
                       rowheight=32,
                       fieldbackground="white",
                       borderwidth=0,
                       font=('Segoe UI', 9))
        style.configure("Empresas.Treeview.Heading",
                       background='#f8f9fa',
                       foreground='#495057',
                       font=('Segoe UI', 9, 'bold'),
                       borderwidth=0,
                       relief='flat')
        style.map("Empresas.Treeview",
                 background=[("selected", CORES['primary'])],
                 foreground=[("selected", "white")])

        scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("id", "nome", "usuarios", "banco", "status"),
            show="headings",
            style="Empresas.Treeview",
            selectmode="browse",
            yscrollcommand=scroll.set
        )
        scroll.config(command=self.tree.yview)

        self.tree.heading("id",       text="ID",       anchor="center")
        self.tree.heading("nome",     text="Nome da Empresa", anchor="w")
        self.tree.heading("usuarios", text="Usuários", anchor="center")
        self.tree.heading("banco",    text="Banco de Dados", anchor="w")
        self.tree.heading("status",   text="Status",   anchor="center")

        self.tree.column("id",       width=50,  minwidth=40,  stretch=False, anchor="center")
        self.tree.column("nome",     width=280, minwidth=180, stretch=True,  anchor="w")
        self.tree.column("usuarios", width=80,  minwidth=70,  stretch=False, anchor="center")
        self.tree.column("banco",    width=280, minwidth=180, stretch=True,  anchor="w")
        self.tree.column("status",   width=80,  minwidth=70,  stretch=False, anchor="center")

        self.tree.pack(fill="both", expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # CARREGAMENTO
    # ══════════════════════════════════════════════════════════════════════════

    def carregar_empresas(self):
        self._empresas_cache = self.dao.listar_empresas(apenas_ativas=True)
        self._popular_tree()

    def _popular_tree(self):
        selecionado = self._id_selecionado()
        self.tree.delete(*self.tree.get_children())

        for e in self._empresas_cache:
            qtd_usuarios = self.dao.contar_usuarios_empresa(e['id'])
            
            # Nome do arquivo apenas
            banco_nome = os.path.basename(e['caminho_banco']) if e['caminho_banco'] else "—"
            
            status = "✓ Ativa" if e['ativo'] else "✗ Inativa"

            self.tree.insert(
                "", "end",
                iid=str(e['id']),
                values=(
                    e['id'],
                    e['nome_exibicao'],
                    qtd_usuarios,
                    banco_nome,
                    status
                )
            )

        if selecionado and self.tree.exists(selecionado):
            self.tree.selection_set(selecionado)
            self.tree.see(selecionado)

    def _id_selecionado(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _empresa_selecionada(self):
        iid = self._id_selecionado()
        if not iid:
            messagebox.showwarning("Atenção", "Selecione uma empresa na lista.",
                                  parent=self.janela)
            return None
        empresa_id = int(iid)
        return next((e for e in self._empresas_cache if e['id'] == empresa_id), None)

    # ══════════════════════════════════════════════════════════════════════════
    # AÇÕES
    # ══════════════════════════════════════════════════════════════════════════

    def nova_empresa(self):
        """Abre modal para criar nova empresa."""
        ModalNovaEmpresa(self.janela, self.carregar_empresas)

    def renomear_empresa(self):
        """Renomeia empresa selecionada."""
        empresa = self._empresa_selecionada()
        if not empresa:
            return

        novo_nome = simpledialog.askstring(
            "Renomear Empresa",
            f"Novo nome para '{empresa['nome_exibicao']}':",
            initialvalue=empresa['nome_exibicao'],
            parent=self.janela
        )

        if not novo_nome or novo_nome.strip() == "":
            return

        if self.dao.atualizar_empresa(empresa['id'], novo_nome.strip()):
            messagebox.showinfo("Sucesso", "Empresa renomeada com sucesso!",
                               parent=self.janela)
            self.carregar_empresas()
        else:
            messagebox.showerror("Erro", "Erro ao renomear empresa.",
                                parent=self.janela)

    def gerenciar_usuarios(self):
        """Abre tela de gerenciamento de usuários da empresa."""
        empresa = self._empresa_selecionada()
        if not empresa:
            return

        ModalGerenciarUsuarios(self.janela, empresa, self.carregar_empresas)

    def excluir_empresa(self):
        """Exclui empresa selecionada permanentemente."""
        empresa = self._empresa_selecionada()
        if not empresa:
            return

        qtd_usuarios = self.dao.contar_usuarios_empresa(empresa['id'])

        resposta = messagebox.askyesno(
            "⚠️ CONFIRMAR EXCLUSÃO",
            f"EXCLUIR PERMANENTEMENTE:\n\n"
            f"Empresa: {empresa['nome_exibicao']}\n"
            f"ID: {empresa['id']}\n"
            f"Usuários com acesso: {qtd_usuarios}\n\n"
            f"O BANCO DE DADOS SERÁ DELETADO!\n"
            f"Todos os dados (diaristas, serviços, produções, etc.) "
            f"serão PERDIDOS.\n\n"
            f"Esta ação NÃO PODE SER DESFEITA!\n\n"
            f"Tem CERTEZA ABSOLUTA?",
            icon='warning',
            parent=self.janela
        )

        if resposta:
            if self.dao.excluir_empresa(empresa['id']):
                messagebox.showinfo("Sucesso", "Empresa excluída com sucesso!",
                                   parent=self.janela)
                self.carregar_empresas()
            else:
                messagebox.showerror("Erro", "Erro ao excluir empresa.",
                                    parent=self.janela)


# ══════════════════════════════════════════════════════════════════════════════
# MODAL: NOVA EMPRESA
# ══════════════════════════════════════════════════════════════════════════════

class ModalNovaEmpresa:
    def __init__(self, parent, callback=None):
        self.dao = EmpresaCentralDAO()
        self.callback = callback

        self.janela = tk.Toplevel(parent)
        self.janela.title("Nova Empresa")
        self.janela.geometry("420x180")
        self.janela.configure(bg='white')
        self.janela.resizable(False, False)
        self.janela.transient(parent)
        self.janela.grab_set()

        self.centralizar()
        self.criar_interface()

    def centralizar(self):
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() - 420) // 2
        y = (self.janela.winfo_screenheight() - 180) // 2
        self.janela.geometry(f"420x180+{x}+{y}")

    def criar_interface(self):
        container = tk.Frame(self.janela, bg='white')
        container.pack(fill="both", expand=True, padx=30, pady=25)

        tk.Label(container, text="Nome da Empresa",
                 font=('Segoe UI', 11),
                 foreground='#212529',
                 bg='white').pack(anchor="w", pady=(0, 8))

        self.var_nome = tk.StringVar()
        entry = tk.Entry(container, textvariable=self.var_nome,
                        font=('Segoe UI', 11),
                        relief='solid', bd=1)
        entry.pack(fill="x", ipady=8)
        entry.focus_set()

        btn_frame = tk.Frame(container, bg='white')
        btn_frame.pack(fill="x", pady=(20, 0))

        tk.Button(btn_frame, text="Cancelar",
                  font=('Segoe UI', 9),
                  bg='#6c757d', fg='white',
                  relief='flat', cursor='hand2',
                  padx=18, pady=8,
                  command=self.janela.destroy).pack(side="right", padx=(8, 0))

        tk.Button(btn_frame, text="Criar Empresa",
                  font=('Segoe UI', 9, 'bold'),
                  bg=CORES['success'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=18, pady=8,
                  command=self.cadastrar).pack(side="right")

        entry.bind("<Return>", lambda _: self.cadastrar())
        self.janela.bind("<Escape>", lambda _: self.janela.destroy())

    def cadastrar(self):
        nome = self.var_nome.get().strip()

        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome da empresa.",
                                  parent=self.janela)
            return

        try:
            empresa_id = self.dao.cadastrar_empresa(nome)
            messagebox.showinfo(
                "Sucesso",
                f"Empresa '{nome}' criada com sucesso!\n\nID: {empresa_id}",
                parent=self.janela
            )
            if self.callback:
                self.callback()
            self.janela.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar empresa:\n\n{str(e)}",
                                parent=self.janela)


# ══════════════════════════════════════════════════════════════════════════════
# MODAL: GERENCIAR USUÁRIOS
# ══════════════════════════════════════════════════════════════════════════════

class ModalGerenciarUsuarios:
    def __init__(self, parent, empresa, callback=None):
        self.dao = EmpresaCentralDAO()
        self.empresa = empresa
        self.callback = callback

        self.janela = tk.Toplevel(parent)
        self.janela.title(f"Gerenciar Usuários - {empresa['nome_exibicao']}")
        self.janela.geometry("700x500")
        self.janela.configure(bg='#fafbfc')
        self.janela.transient(parent)
        self.janela.grab_set()

        self.centralizar()
        self.criar_interface()
        self.carregar_usuarios()

    def centralizar(self):
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() - 700) // 2
        y = (self.janela.winfo_screenheight() - 500) // 2
        self.janela.geometry(f"700x500+{x}+{y}")

    def criar_interface(self):
        container = tk.Frame(self.janela, bg='#fafbfc')
        container.pack(fill="both", expand=True, padx=30, pady=25)

        # Header
        tk.Label(container, text=f"Gerenciar Acessos",
                 font=('Segoe UI', 14, 'bold'),
                 foreground='#1a1a1a',
                 bg='#fafbfc').pack(anchor="w")

        tk.Label(container, text=self.empresa['nome_exibicao'],
                 font=('Segoe UI', 10),
                 foreground='#6c757d',
                 bg='#fafbfc').pack(anchor="w", pady=(2, 25))

        # Painel duplo
        paineis = tk.Frame(container, bg='#fafbfc')
        paineis.pack(fill="both", expand=True)

        # Painel ESQUERDO - Com acesso
        left = tk.Frame(paineis, bg='white')
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(left, text="✓ Com Acesso",
                 font=('Segoe UI', 10, 'bold'),
                 foreground='#212529',
                 bg='white').pack(anchor="w", padx=15, pady=(12, 8))

        self.list_com_acesso = tk.Listbox(left, font=('Segoe UI', 9),
                                          relief='flat', bd=0,
                                          highlightthickness=0)
        self.list_com_acesso.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        tk.Button(left, text="← Remover Acesso",
                  font=('Segoe UI', 9),
                  bg=CORES['danger'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=12, pady=7,
                  command=self.remover_acesso).pack(padx=15, pady=(0, 12))

        # Painel DIREITO - Sem acesso
        right = tk.Frame(paineis, bg='white')
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(right, text="Sem Acesso",
                 font=('Segoe UI', 10, 'bold'),
                 foreground='#212529',
                 bg='white').pack(anchor="w", padx=15, pady=(12, 8))

        self.list_sem_acesso = tk.Listbox(right, font=('Segoe UI', 9),
                                          relief='flat', bd=0,
                                          highlightthickness=0)
        self.list_sem_acesso.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        tk.Button(right, text="Conceder Acesso →",
                  font=('Segoe UI', 9),
                  bg=CORES['success'], fg='white',
                  relief='flat', cursor='hand2',
                  padx=12, pady=7,
                  command=self.conceder_acesso).pack(padx=15, pady=(0, 12))

    def carregar_usuarios(self):
        # Com acesso
        self.list_com_acesso.delete(0, tk.END)
        usuarios_com = self.dao.listar_usuarios_empresa(self.empresa['id'])
        self.usuarios_com_ids = []
        for user_id, nome, admin in usuarios_com:
            label = f"{nome} {'(Admin)' if admin else ''}"
            self.list_com_acesso.insert(tk.END, label)
            self.usuarios_com_ids.append(user_id)

        # Sem acesso
        self.list_sem_acesso.delete(0, tk.END)
        usuarios_sem = self.dao.listar_usuarios_sem_acesso(self.empresa['id'])
        self.usuarios_sem_ids = []
        for user_id, nome, admin in usuarios_sem:
            label = f"{nome} {'(Admin)' if admin else ''}"
            self.list_sem_acesso.insert(tk.END, label)
            self.usuarios_sem_ids.append(user_id)

    def conceder_acesso(self):
        sel = self.list_sem_acesso.curselection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um usuário.",
                                  parent=self.janela)
            return

        idx = sel[0]
        usuario_id = self.usuarios_sem_ids[idx]

        if self.dao.adicionar_usuario_empresa(self.empresa['id'], usuario_id):
            self.carregar_usuarios()
            if self.callback:
                self.callback()
        else:
            messagebox.showerror("Erro", "Erro ao conceder acesso.",
                                parent=self.janela)

    def remover_acesso(self):
        sel = self.list_com_acesso.curselection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um usuário.",
                                  parent=self.janela)
            return

        idx = sel[0]
        usuario_id = self.usuarios_com_ids[idx]

        if self.dao.remover_usuario_empresa(self.empresa['id'], usuario_id):
            self.carregar_usuarios()
            if self.callback:
                self.callback()
        else:
            messagebox.showerror("Erro", "Erro ao remover acesso.",
                                parent=self.janela)