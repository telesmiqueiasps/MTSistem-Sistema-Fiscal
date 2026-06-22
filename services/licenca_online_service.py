"""
Verificação online de licença/versão a partir de um site estático (ex.: Netlify)
que publica um JSON no formato:

{
  "versao_atual": "1.2.0",
  "exe_url": "https://SEU-SITE.netlify.app/downloads/MTSistem_Update.exe",
  "mensagem_update": "Nova versão disponível com melhorias e correções.",
  "clientes": [
    { "id": "CLIENTE001", "status": "ok" },
    { "id": "CLIENTE002", "status": "bloqueado", "mensagem_bloqueio": "..." },

    // Qualquer cliente pode opcionalmente sobrescrever os campos globais
    // acima (versao_atual / exe_url / mensagem_update) — útil para liberar
    // uma versão diferente, um instalador específico ou testar com um
    // cliente antes do rollout geral. Quem não definir esses campos
    // simplesmente herda os valores globais.
    { "id": "CLIENTE003", "status": "ok",
      "versao_atual": "1.1.5",
      "exe_url": "https://SEU-SITE.netlify.app/downloads/Cliente003_Update.exe" }
  ]
}

A consulta nunca lança exceção para o chamador: se a internet estiver fora,
o site indisponível, o JSON inválido ou o CLIENTE_ID não estiver na lista,
retorna None — o chamador deve então tratar isso como "sem informação
remota" (fail-open) e seguir com a verificação local de versão.
"""
import json
import os
import tempfile
import urllib.error
import urllib.request

from utils.constantes import CLIENTE_ID, URL_VERIFICACAO_LICENCA

MENSAGEM_BLOQUEIO_PADRAO = "Este cliente não possui acesso liberado. Contate o suporte."


def verificar_licenca_online(timeout: int = 4) -> dict | None:
    """Consulta o status deste cliente no site de licenciamento.

    Retorna um dict {status, mensagem_bloqueio, versao_atual,
    mensagem_update, exe_url} em caso de sucesso, ou None se não foi
    possível obter uma resposta confiável.
    """
    try:
        with urllib.request.urlopen(URL_VERIFICACAO_LICENCA, timeout=timeout) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    clientes = dados.get("clientes", [])
    registro = next((c for c in clientes if c.get("id") == CLIENTE_ID), None)
    if not registro:
        return None

    return {
        "status": (registro.get("status") or "ok").strip().lower(),
        "mensagem_bloqueio": registro.get("mensagem_bloqueio") or MENSAGEM_BLOQUEIO_PADRAO,
        # Campos do próprio cliente sobrescrevem os globais quando presentes.
        "versao_atual": registro.get("versao_atual") or dados.get("versao_atual"),
        "mensagem_update": registro.get("mensagem_update") or dados.get("mensagem_update"),
        "exe_url": registro.get("exe_url") or dados.get("exe_url"),
    }


def baixar_atualizacao(exe_url: str) -> str:
    """Baixa o instalador/executável de atualização para a pasta temporária
    do sistema e retorna o caminho local do arquivo baixado."""
    nome_arquivo = os.path.basename(exe_url.split("?")[0]) or "MTSistem_Update.exe"
    destino = os.path.join(tempfile.gettempdir(), nome_arquivo)
    urllib.request.urlretrieve(exe_url, destino)
    return destino
