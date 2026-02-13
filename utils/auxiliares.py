import os
import sys
import re
from tkinter import messagebox, ttk
from dao.usuario_dao import UsuarioDAO
from utils.constantes import CORES, VERSAO_ATUAL


def resource_path(rel_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.abspath("."), rel_path)


def pasta_dados_app(nome_app="MTSistem"):
    base = os.path.join(os.path.expanduser("~"), "Documents", nome_app)
    os.makedirs(base, exist_ok=True)
    return base

def verificar_versao_no_startup():
    dao = UsuarioDAO()

    versao_remota = dao.get_config("versao_atual")

    if not versao_remota:
        messagebox.showerror(
            "Erro crítico",
            "Versão do sistema não configurada no banco de dados.\n\n"
            "O sistema não pode ser iniciado."
        )
        sys.exit()

    return versao_remota


def atualizacao_liberada(dao: UsuarioDAO):
    try:
        return dao.get_config("atualizacao_liberada") == "SIM"
    except Exception:
        return False
    

def sistema_esta_desatualizado(dao):
    versao_banco = dao.get_config("versao_atual")
    return str(versao_banco).strip() != str(VERSAO_ATUAL).strip()



def executar_atualizacao(dao: UsuarioDAO):
    caminho_exe = dao.get_config("exe_atualizacao")

    if not caminho_exe or not os.path.exists(caminho_exe):
        messagebox.showerror(
            "Atualização indisponível",
            "Arquivo de atualização não encontrado.\n\n"
            "Entre em contato com o administrador."
        )
        return

    try:
        messagebox.showinfo(
            "Atualização",
            "O sistema será fechado para aplicar a atualização."
        )

        os.startfile(caminho_exe)
        sys.exit()

    except OSError:
        messagebox.showwarning(
            "Atualização cancelada",
            "A atualização foi cancelada pelo usuário."
        )


# =====================================================
# CONFIGURAÇÕES DE ESTILO
# =====================================================



def configurar_estilo():
    """Configura estilos modernos para os widgets ttk"""
    style = ttk.Style()
    style.theme_use('clam')
    
    # Botões primários
    style.configure(
        'Primary.TButton',
        background=CORES['primary'],
        foreground='white',
        borderwidth=0,
        focuscolor='none',
        font=('Segoe UI', 10),
        padding=(20, 10)
    )
    style.map('Primary.TButton',
        background=[('active', CORES['primary_hover'])]
    )

    # Botões verde (Adicionar)
    style.configure(
        'Add.TButton',
        background=CORES['success'],
        foreground='white',
        borderwidth=0,
        focuscolor='none',
        font=('Segoe UI', 10),
        padding=(20, 10)
    )
    style.map('Add.TButton',
        background=[('active', CORES['success_hover'])]
    )

    # Botões vermelho(excluir)
    style.configure(
        'Danger.TButton',
        background=CORES['danger'],
        foreground='white',
        borderwidth=0,
        focuscolor='none',
        font=('Segoe UI', 10),
        padding=(20, 10)
    )
    style.map('Danger.TButton',
        background=[('active', CORES['danger_hover'])]
    )

    # Botões amarelo(atenção)
    style.configure(
        'Warning.TButton',
        background=CORES['warning'],
        foreground='white',
        borderwidth=0,
        focuscolor='none',
        font=('Segoe UI', 10),
        padding=(20, 10)
    )
    style.map('Warning.TButton',
        background=[('active', CORES['warning_hover'])]
    )
    
    # Botões secundários
    style.configure(
        'Secondary.TButton',
        background=CORES['bg_card'],
        foreground=CORES['text_dark'],
        borderwidth=1,
        relief='solid',
        font=('Segoe UI', 9),
        padding=(15, 8)
    )

    # Botões voltar
    style.configure(
        'Voltar.TButton',
        background=CORES['primary'],
        foreground='white',
        borderwidth=0,
        focuscolor='none',
        font=('Segoe UI', 8),
        padding=(10, 8)
    )
    style.map('Voltar.TButton',
        background=[('active', CORES['primary_hover'])]
    )
    
    # Checkbuttons
    style.configure(
        "Custom.TCheckbutton",
        background=CORES['bg_card'],
        foreground=CORES['text_dark'],
        font=('Segoe UI', 10),
        padding=5
    )
    style.map(
        "Custom.TCheckbutton",
        background=[
            ('active', CORES['bg_card_hover']),
            ('selected', CORES['bg_card'])
        ],
        foreground=[
            ('disabled', CORES['text_light']),
            ('selected', CORES['text_dark'])
        ]
    )

    # Labels
    style.configure(
        'Title.TLabel',
        background=CORES['bg_main'],
        foreground=CORES['text_dark'],
        font=('Segoe UI', 11, 'bold')
    )
    
    style.configure(
        'Subtitle.TLabel',
        background=CORES['bg_card'],
        foreground=CORES['text_light'],
        font=('Segoe UI', 9)
    )
    
    # Frames
    style.configure('Card.TFrame', background=CORES['bg_card'], relief='flat')
    style.configure('Main.TFrame', background=CORES['bg_main'])


def formatar_cpf(valor):
    """
    Recebe qualquer string e retorna CPF formatado.
    Mantém zeros à esquerda.
    """
    numeros = re.sub(r"\D", "", valor)[:11]

    if len(numeros) <= 3:
        return numeros
    elif len(numeros) <= 6:
        return f"{numeros[:3]}.{numeros[3:]}"
    elif len(numeros) <= 9:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:]}"
    else:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"