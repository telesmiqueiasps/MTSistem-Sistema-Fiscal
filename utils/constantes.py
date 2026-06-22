import os

VERSAO_ATUAL = "1.2.0"
CAMINHO_EXE_ATUALIZADO = r"T:\MTSistem\app\MTSistem.exe"

# ── Licenciamento / Verificação Online ──────────────────────────────────────
# CLIENTE_ID: identificador único desta instalação. Defina um valor diferente
# para cada cliente ANTES de gerar o executável (.exe) dele — precisa bater
# exatamente com o "id" cadastrado na lista de clientes do site de status.
CLIENTE_ID = "CLIENTE001TORTAFREIDAMIAO"

# URL do JSON estático (ex.: hospedado na Netlify) com a lista de clientes,
# versão atual e link de download da atualização. Mesma URL para todos os
# clientes — substitua pela URL real do seu site antes de distribuir.
URL_VERIFICACAO_LICENCA = "https://mtsistemvalidador.netlify.app/clientes.json"


MODULOS = {
    "abrir_extrator": "Extrator TXT → Excel",
    "abrir_comparador": "Comparador SEFAZ x Sistema",
    "abrir_triagem": "Triagem SPED → PDFs",
    "abrir_extrator_pdf": "Extrator PDF → Excel",
    "abrir_diaristas": "Cadastro de Diaristas",
    "abrir_centros_custo": "Centros de Custo",
    "abrir_diarias": "Emissor de Diárias",
    "abrir_servicos": "Emissor de Serviços",
    'abrir_producao': "Controle de Produção",
    "abrir_notas_fiscais": "Notas Fiscais",
}

CORES = {
    'bg_card_hover': '#F5F7FA',
    'bg_hover': '#F5F7FA',
    'primary': '#2563eb',
    'primary_hover': '#1d4ed8',
    'secondary': '#64748b',
    'success': '#10b981',
    'success_hover': "#057e56",
    'danger': '#ef4444',
    'warning': '#f59e0b',
    'warning_hover': '#e69000',
    'danger_hover': '#dc2626',
    'bg_main': '#f8fafc',
    'bg_card': '#ffffff',
    'text_dark': '#1e293b',
    'text_light': '#64748b',
    'border': '#e2e8f0'
}