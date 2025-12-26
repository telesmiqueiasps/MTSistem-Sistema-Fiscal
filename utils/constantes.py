import os

VERSAO_ATUAL = "1.0"
CAMINHO_EXE_ATUALIZADO = r"T:\MTSistem\app\MTSistem.exe"

DB_DIR = r"T:\MTSistem\db"
DB_PATH = os.path.join(DB_DIR, "sistemafiscal.db")


MODULOS = {
    "abrir_extrator": "Extrator TXT → Excel",
    "abrir_comparador": "Comparador SEFAZ x Sistema",
    "abrir_triagem": "Triagem SPED → PDFs",
    "abrir_extrator_pdf": "Extrator PDF → Excel"
}

CORES = {
    'bg_card_hover': '#F5F7FA',
    'primary': '#2563eb',
    'primary_hover': '#1d4ed8',
    'secondary': '#64748b',
    'success': '#10b981',
    'success_hover': "#057e56",
    'danger': '#ef4444',
    'danger_hover': '#dc2626',
    'bg_main': '#f8fafc',
    'bg_card': '#ffffff',
    'text_dark': '#1e293b',
    'text_light': '#64748b',
    'border': '#e2e8f0'
}