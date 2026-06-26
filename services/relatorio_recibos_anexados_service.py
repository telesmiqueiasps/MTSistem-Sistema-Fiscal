"""
Gera um único PDF mesclando os arquivos de recibo assinados realmente
anexados às notas fiscais filtradas em um relatório (services.
relatorio_notas_fiscais_service). Cada nota com recibo recebe uma página
separadora de identificação, seguida dos arquivos anexados (PDFs mesclados
diretamente, imagens convertidas em página).
"""
import os
import tempfile
from pathlib import Path

from PIL import Image
from PyPDF2 import PdfMerger
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas

EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif"}


def _abrir_pdf(caminho: str):
    try:
        os.startfile(caminho)
    except AttributeError:
        import subprocess
        try:
            subprocess.call(["xdg-open", caminho])
        except Exception:
            pass


def _fmt_brl(valor) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _gerar_pagina_separadora(nota: dict) -> str:
    """Página de identificação (NF, emitente, valor) inserida antes dos
    recibos daquela nota, para dar contexto na mesclagem."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    caminho = tmp.name
    tmp.close()

    c = rl_canvas.Canvas(caminho, pagesize=A4)
    largura, altura = A4

    c.setFillColor(colors.HexColor("#2c3e50"))
    c.rect(0, altura - 4 * cm, largura, 4 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, altura - 1.8 * cm, f"NOTA FISCAL Nº {nota['numero']}")
    c.setFont("Helvetica", 12)
    c.drawCentredString(largura / 2, altura - 2.6 * cm, nota.get("emitente") or "")
    c.drawCentredString(
        largura / 2, altura - 3.2 * cm,
        f"Competência: {nota.get('competencia') or '—'}   |   Valor: {_fmt_brl(nota['valor'])}"
    )

    c.setFillColor(colors.HexColor("#7f8c8d"))
    c.setFont("Helvetica", 9)
    c.drawCentredString(largura / 2, 1.5 * cm, "Recibo(s) assinado(s) anexado(s) a seguir")
    c.save()
    return caminho


def _converter_imagem_para_pdf(caminho_imagem: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    caminho_pdf = tmp.name
    tmp.close()
    with Image.open(caminho_imagem) as img:
        img.convert("RGB").save(caminho_pdf, "PDF")
    return caminho_pdf


class RelatorioRecibosAnexadosPDF:

    @staticmethod
    def gerar(dao, notas: list, abrir: bool = True):
        """Mescla os recibos anexados das notas informadas em um único PDF.

        Retorna (caminho, problemas): `caminho` é None se nada pôde ser
        incluído; `problemas` é a lista de avisos (arquivo não encontrado,
        formato não suportado, erro ao mesclar) para exibir ao usuário.
        """
        notas_com_recibo = [n for n in notas if n.get("qtd_recibos")]
        if not notas_com_recibo:
            return None, ["Nenhuma das notas filtradas possui recibo anexado."]

        merger = PdfMerger()
        arquivos_temporarios = []
        problemas = []
        algo_incluido = False

        for nota in notas_com_recibo:
            recibos = dao.listar_recibos(nota["id"])
            if not recibos:
                continue

            separador = _gerar_pagina_separadora(nota)
            arquivos_temporarios.append(separador)
            pagina_separadora_inserida = False

            for r in recibos:
                caminho = r["arquivo"]
                if not os.path.exists(caminho):
                    problemas.append(f"NF {nota['numero']}: arquivo não encontrado ({r['nome_arquivo']})")
                    continue

                ext = Path(caminho).suffix.lower()
                if ext == ".pdf":
                    origem = caminho
                elif ext in EXTENSOES_IMAGEM:
                    try:
                        origem = _converter_imagem_para_pdf(caminho)
                        arquivos_temporarios.append(origem)
                    except Exception as e:
                        problemas.append(
                            f"NF {nota['numero']}: erro ao converter imagem {r['nome_arquivo']} ({e})"
                        )
                        continue
                else:
                    problemas.append(
                        f"NF {nota['numero']}: formato não suportado para mesclagem ({r['nome_arquivo']})"
                    )
                    continue

                try:
                    if not pagina_separadora_inserida:
                        merger.append(separador)
                        pagina_separadora_inserida = True
                    merger.append(origem)
                    algo_incluido = True
                except Exception as e:
                    problemas.append(f"NF {nota['numero']}: erro ao mesclar {r['nome_arquivo']} ({e})")

        if not algo_incluido:
            merger.close()
            for f in arquivos_temporarios:
                try:
                    os.remove(f)
                except OSError:
                    pass
            return None, problemas or ["Nenhum recibo pôde ser incluído no PDF."]

        tmp_final = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        caminho_final = tmp_final.name
        tmp_final.close()
        with open(caminho_final, "wb") as f:
            merger.write(f)
        merger.close()

        for f in arquivos_temporarios:
            try:
                os.remove(f)
            except OSError:
                pass

        if abrir:
            _abrir_pdf(caminho_final)

        return caminho_final, problemas
