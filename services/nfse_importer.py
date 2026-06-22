"""
Importador de NFS-e (DANFSe v1.0) via OCR (PDF) ou via XML estruturado.
"""
import re
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime


class NFSeImportError(Exception):
    pass


def _encontrar_tesseract() -> str:
    """
    Localiza o executável do Tesseract.
    Tenta: PATH do sistema e depois caminhos padrão do Windows.
    """
    import shutil, sys

    if shutil.which("tesseract"):
        return "tesseract"

    if sys.platform == "win32":
        candidatos = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
            os.path.join(os.environ.get("APPDATA", ""), "Tesseract-OCR", "tesseract.exe"),
        ]
        for c in candidatos:
            if os.path.isfile(c):
                return c

        raise NFSeImportError(
            "Tesseract OCR não encontrado!\n\n"
            "Para usar a importação de NFS-e por PDF:\n\n"
            "1. Baixe e instale em:\n"
            "   https://github.com/UB-Mannheim/tesseract/wiki\n\n"
            "2. Durante a instalação, em 'Additional language data',\n"
            "   marque 'Portuguese' para suporte ao idioma.\n\n"
            "3. Reinicie o aplicativo após instalar."
        )

    raise NFSeImportError(
        "Tesseract OCR não encontrado!\n\n"
        "Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-por\n"
        "Mac: brew install tesseract tesseract-lang"
    )


def tesseract_disponivel() -> bool:
    """Verifica se o Tesseract está instalável sem lançar exceção."""
    import shutil, sys
    if shutil.which("tesseract"):
        return True
    if sys.platform == "win32":
        candidatos = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
        ]
        return any(os.path.isfile(c) for c in candidatos)
    return False


def _extrair_texto_ocr(pdf_path: str) -> str:
    """Converte PDF para imagem em alta resolução e aplica OCR com Tesseract."""
    try:
        import fitz
    except ImportError:
        raise NFSeImportError(
            "PyMuPDF não instalado.\n"
            "Execute: pip install pymupdf"
        )

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise NFSeImportError(f"Não foi possível abrir o PDF:\n{e}")

    if len(doc) == 0:
        raise NFSeImportError("PDF vazio ou corrompido.")

    tesseract_cmd = _encontrar_tesseract()

    page = doc[0]
    mat = fitz.Matrix(3, 3)  # 3x resolução para OCR de qualidade
    pix = page.get_pixmap(matrix=mat)

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, "nfse.png")
        txt_path = os.path.join(tmpdir, "nfse")
        pix.save(img_path)

        ultimo_erro = ""
        for lang in ["por", "por+eng", "eng"]:
            try:
                result = subprocess.run(
                    [tesseract_cmd, img_path, txt_path, "-l", lang],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    break
                ultimo_erro = result.stderr
            except FileNotFoundError:
                raise NFSeImportError(
                    f"Tesseract não encontrado em:\n{tesseract_cmd}\n\n"
                    "Reinstale e reinicie o aplicativo."
                )
        else:
            raise NFSeImportError(
                f"Tesseract falhou ao processar o PDF.\n{ultimo_erro}\n\n"
                "Verifique se o pacote de idioma Português está instalado."
            )

        output_file = txt_path + ".txt"
        if not os.path.isfile(output_file):
            raise NFSeImportError("Tesseract não gerou saída. Tente reinstalar.")

        with open(output_file, "r", encoding="utf-8") as f:
            return f.read()


def _limpar(s: str) -> str:
    return " ".join(s.split()).strip()


def _linha_apos(lines: list, label: str, inicio: int = 0, fim: int = None, saltar: int = 1) -> str:
    """Retorna o conteúdo da `saltar`-ésima linha não-vazia após a linha que contém `label`."""
    fim = fim or len(lines)
    for i in range(inicio, fim):
        if label.lower() in lines[i].lower():
            count = 0
            for j in range(i + 1, min(i + 15, fim)):
                if lines[j].strip():
                    count += 1
                    if count == saltar:
                        return lines[j].strip()
    return ""


def _idx_linha(lines: list, label: str, inicio: int = 0) -> int:
    """Retorna o índice da primeira linha que contém o label."""
    for i in range(inicio, len(lines)):
        if label.lower() in lines[i].lower():
            return i
    return -1


def _parse_valor(s: str):
    """R$ 9.726,00  →  9726.0"""
    if not s:
        return None
    nums = re.sub(r"[^\d,]", "", s)
    if not nums:
        return None
    nums = nums.replace(",", ".")
    try:
        return float(nums)
    except ValueError:
        return None


def _parse_data_iso(s: str) -> str:
    """DD/MM/YYYY ... → YYYY-MM-DD"""
    if not s:
        return ""
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return ""


def _parse_competencia(s: str) -> str:
    """Extrai MM/AAAA de uma string qualquer."""
    if not s:
        return ""
    m = re.search(r"\b(\d{2}/\d{4})\b", s)
    if m:
        return m.group(1)
    m = re.search(r"\d{2}/(\d{2}/\d{4})", s)
    if m:
        return m.group(1)
    return ""


def _competencia_da_descricao(desc: str) -> str:
    """Busca padrão 'MÊS DE MM/AAAA' ou 'COMPETÊNCIA MM/AAAA' na descrição."""
    m = re.search(
        r"(?:m[eê]s\s+de|competên[ck]ia|referente\s+ao\s+m[eê]s\s+de)\s*:?\s*(\d{2}/\d{4})",
        desc, re.IGNORECASE
    )
    return m.group(1) if m else ""


def importar_nfse(pdf_path: str) -> dict:
    """Lê um DANFSe v1.0 (via OCR) e retorna dict com campos para o banco."""
    texto = _extrair_texto_ocr(pdf_path)
    lines = texto.split("\n")

    chave = ""
    idx = _idx_linha(lines, "Chave de Acesso")
    if idx >= 0:
        chave = _linha_apos(lines, "Chave de Acesso", idx, idx + 5)
    if not chave:
        m = re.search(r"\b(\d{44})\b", texto)
        chave = m.group(1) if m else ""

    numero = ""
    idx = _idx_linha(lines, "Número da NFS-e")
    if idx >= 0:
        numero = _linha_apos(lines, "Número da NFS-e", idx, idx + 5)
    numero = _limpar(numero)

    data_emissao = ""
    idx = _idx_linha(lines, "Data e Hora da emissão da NFS-e")
    if idx >= 0:
        raw = _linha_apos(lines, "Data e Hora da emissão da NFS-e", idx, idx + 5)
        data_emissao = _parse_data_iso(raw)

    competencia = ""
    idx = _idx_linha(lines, "Competência da NFS-e")
    if idx >= 0:
        raw = _linha_apos(lines, "Competência da NFS-e", idx, idx + 5)
        competencia = _parse_competencia(raw)

    emitente = ""
    cnpj_cpf = ""

    idx_emit = _idx_linha(lines, "EMITENTE DA NFS-e")
    idx_tomad = _idx_linha(lines, "TOMADOR DO SERVIÇO")

    if idx_emit >= 0:
        bloco_emit = lines[idx_emit: idx_tomad if idx_tomad > idx_emit else idx_emit + 30]

        for l in bloco_emit:
            m = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", l)
            if m:
                cnpj_cpf = m.group(0)
                break

        encontrou_cnpj = False
        for l in bloco_emit:
            if cnpj_cpf and cnpj_cpf in l:
                encontrou_cnpj = True
                continue
            if encontrou_cnpj and l.strip():
                if not re.match(
                    r"^(Endere[çc]|Inscri[çc]|Simples|Optante|Regime|Munic[ií]|Telefone|CEP|E-mail)",
                    l.strip(), re.IGNORECASE
                ):
                    emitente = _limpar(l)
                    break

    if not cnpj_cpf:
        m = re.search(r"\b(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\b", texto)
        cnpj_cpf = m.group(1) if m else ""

    descricao = ""
    idx_desc = _idx_linha(lines, "Descrição do Serviço")
    idx_trib_mun = -1
    for _i, _l in enumerate(lines):
        if re.match(r"^TRIBUTA[CÇ][AÃ]O\s+MUNICIPAL\s*$", _l.strip(), re.IGNORECASE):
            idx_trib_mun = _i
            break

    if idx_desc >= 0 and idx_trib_mun > idx_desc:
        labels_colunas = {
            "código de tributação municipal",
            "código de tributação nacional",
            "local da prestação",
            "país da prestação",
        }
        inicio_desc = idx_desc + 1
        for i in range(idx_desc + 1, idx_trib_mun):
            l = lines[i].strip()
            if l and any(lab in l.lower() for lab in labels_colunas):
                inicio_desc = i + 1

        partes = []
        for l in lines[inicio_desc: idx_trib_mun]:
            linha = l.strip()
            if not linha:
                continue
            if re.match(r"^[A-Z\s]+ - [A-Z]{2}$", linha):
                continue
            if linha == "-":
                continue
            partes.append(linha)

        descricao = _limpar(" ".join(partes))

    valor = None

    idx_vl = _idx_linha(lines, "Valor Líquido da NFS-e")
    if idx_vl < 0:
        idx_vl = _idx_linha(lines, "Valor Liquido da NFS-e")
    if idx_vl >= 0:
        raw = _linha_apos(lines, lines[idx_vl], idx_vl, idx_vl + 5)
        valor = _parse_valor(raw)

    if valor is None:
        m = re.search(
            r"Valor\s+L[ií]quido\s+da\s+NFS-?e\s*\n+\s*(R\$\s*[\d.,]+)",
            texto, re.IGNORECASE
        )
        if m:
            valor = _parse_valor(m.group(1))

    if valor is None:
        m = re.search(
            r"VALOR\s+TOTAL\s+DA\s+NFS-?E.*?R\$\s*([\d.,]+)",
            texto, re.IGNORECASE | re.DOTALL
        )
        if m:
            valor = _parse_valor(m.group(1))

    if descricao:
        comp_desc = _competencia_da_descricao(descricao)
        if comp_desc:
            competencia = comp_desc

    resultado = {
        "numero": numero,
        "emitente": emitente,
        "cnpj_cpf": cnpj_cpf,
        "descricao_servico": descricao,
        "valor": valor,
        "data_emissao": data_emissao,
        "competencia": competencia,
        "_chave_acesso": chave,
        "_texto_ocr": texto,
    }

    problemas = []
    if not resultado["numero"]:
        problemas.append("Número da NFS-e não encontrado")
    if not resultado["emitente"]:
        problemas.append("Emitente não encontrado")
    if resultado["valor"] is None:
        problemas.append("Valor líquido não encontrado")
    if not resultado["data_emissao"]:
        problemas.append("Data de emissão não encontrada")

    resultado["_problemas"] = problemas
    resultado["_sucesso"] = len(problemas) == 0

    return resultado


def formatar_data_br(data_iso: str) -> str:
    """YYYY-MM-DD → DD/MM/YYYY"""
    if not data_iso:
        return ""
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return data_iso


# ── IMPORTAÇÃO VIA XML (NFS-e nacional) ──────────────────────────────────────
# Muito mais confiável que o OCR do PDF: os dados vêm em tags estruturadas,
# sem depender de Tesseract nem de heurísticas de layout.

def _xml_local_tag(tag: str) -> str:
    """Remove o namespace ("{http://...}tag" → "tag")."""
    return tag.split("}")[-1] if "}" in tag else tag


def _xml_find(elem, tagname: str):
    """Primeiro elemento (entre `elem` e seus descendentes) cujo nome local
    é `tagname`, ignorando namespace."""
    if elem is None:
        return None
    for node in elem.iter():
        if _xml_local_tag(node.tag) == tagname:
            return node
    return None


def _xml_text(elem, tagname: str, default: str = "") -> str:
    node = _xml_find(elem, tagname)
    if node is not None and node.text:
        return node.text.strip()
    return default


def _formatar_cnpj_cpf(digits: str) -> str:
    digits = re.sub(r"\D", "", digits or "")
    if len(digits) == 14:
        return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"
    if len(digits) == 11:
        return f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"
    return digits


def importar_nfse_xml(xml_path: str) -> dict:
    """
    Lê o XML estruturado de uma NFS-e (padrão nacional) e retorna dict com
    os mesmos campos que `importar_nfse` (vindo do OCR).
    """
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as e:
        raise NFSeImportError(f"Arquivo XML inválido ou corrompido:\n{e}")
    except Exception as e:
        raise NFSeImportError(f"Não foi possível abrir o XML:\n{e}")

    numero = _xml_text(root, "nNFSe")

    emit = _xml_find(root, "emit")
    emitente = _xml_text(emit, "xNome")
    cnpj_cpf = _xml_text(emit, "CNPJ") or _xml_text(emit, "CPF")
    cnpj_cpf = _formatar_cnpj_cpf(cnpj_cpf)

    valores = _xml_find(root, "valores")
    valor_txt = _xml_text(valores, "vLiq") if valores is not None else _xml_text(root, "vLiq")
    valor = None
    if valor_txt:
        try:
            valor = float(valor_txt.replace(",", "."))
        except ValueError:
            valor = None

    dh_emi = _xml_text(root, "dhEmi")
    data_emissao = dh_emi[:10] if len(dh_emi) >= 10 else ""

    d_compet = _xml_text(root, "dCompet")
    competencia = ""
    if d_compet:
        try:
            competencia = datetime.strptime(d_compet[:10], "%Y-%m-%d").strftime("%m/%Y")
        except ValueError:
            pass

    descricao = _limpar(_xml_text(root, "xDescServ"))

    chave = ""
    inf_nfse = _xml_find(root, "infNFSe")
    if inf_nfse is not None:
        chave = (inf_nfse.get("Id") or "").strip()

    resultado = {
        "numero": numero,
        "emitente": emitente,
        "cnpj_cpf": cnpj_cpf,
        "descricao_servico": descricao,
        "valor": valor,
        "data_emissao": data_emissao,
        "competencia": competencia,
        "_chave_acesso": chave,
    }

    problemas = []
    if not resultado["numero"]:
        problemas.append("Número da NFS-e (nNFSe) não encontrado")
    if not resultado["emitente"]:
        problemas.append("Emitente (xNome) não encontrado")
    if resultado["valor"] is None:
        problemas.append("Valor líquido (vLiq) não encontrado")
    if not resultado["data_emissao"]:
        problemas.append("Data de emissão (dhEmi) não encontrada")
    if not resultado["competencia"]:
        problemas.append("Competência (dCompet) não encontrada")

    resultado["_problemas"] = problemas
    resultado["_sucesso"] = len(problemas) == 0
    return resultado


def importar_nfse_arquivo(path: str) -> dict:
    """Detecta a extensão e despacha para o importador adequado (XML ou PDF)."""
    if path.lower().endswith(".xml"):
        return importar_nfse_xml(path)
    return importar_nfse(path)
