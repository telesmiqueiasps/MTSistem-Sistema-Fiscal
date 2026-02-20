import tempfile
import os
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from dao.empresa_dao import EmpresaDAO
from utils.auxiliares import resource_path


def _fmt_data(data):
    if not data:
        return "—"
    if isinstance(data, (datetime, date)):
        return data.strftime("%d/%m/%Y")
    return datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")


def _fmt_valor(valor: float) -> str:
    return (
        f"R$ {valor:,.2f}"
        .replace(',', 'X').replace('.', ',').replace('X', '.')
    )


def _abrir_pdf(caminho: str):
    try:
        os.startfile(caminho)
    except AttributeError:
        import subprocess
        subprocess.call(["xdg-open", caminho])


class ReciboServicoService:

    @staticmethod
    def gerar_recibo_temporario(servico_dados: dict) -> str:
        """
        Gera recibo de serviço com rateio entre diaristas.

        servico_dados esperado:
        {
            'id':             int,
            'data_servico':   str  (YYYY-MM-DD),
            'centro_custo':   str,
            'valor':          float,
            'descricao':      str,
            'observacoes':    str | None,
            'centro_custo_id':int,
            'diaristas': [
                {'id': int, 'nome': str, 'cpf': str, 'valor_rateio': float},
                ...
            ]
        }
        """
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        caminho = tmp.name
        tmp.close()

        try:
            empresa = EmpresaDAO().buscar_empresa()
        except Exception:
            empresa = None

        c = canvas.Canvas(caminho, pagesize=A4)
        largura, altura = A4

        diaristas   = servico_dados.get('diaristas', [])
        valor_total = servico_dados.get('valor', 0.0)
        multi       = len(diaristas) > 1

        y = altura - 2.5 * cm

        # ── Logo ──────────────────────────────────────────────────────────────
        try:
            logo = resource_path("Icones/logo_empresa.png")
            c.drawImage(logo,
                        (largura - 80) / 2, y - 10,
                        width=80, height=80,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

        # ── Cabeçalho empresa ─────────────────────────────────────────────────
        if empresa:
            c.setFont("Helvetica-Bold", 13)
            c.drawCentredString(largura / 2, y - 10,
                                empresa.get("razao_social", ""))

            c.setFont("Helvetica", 9)
            c.drawCentredString(
                largura / 2, y - 26,
                f"CNPJ/CPF: {empresa.get('cnpj', '')}  |  "
                f"IE: {empresa.get('inscricao_estadual', '')}"
            )
            c.drawCentredString(
                largura / 2, y - 40,
                f"{empresa.get('endereco', '')} — "
                f"{empresa.get('cidade', '')}/{empresa.get('uf', '')}"
            )

        c.setStrokeColor(colors.HexColor('#2c3e50'))
        c.setLineWidth(1)
        c.line(2 * cm, y - 55, largura - 2 * cm, y - 55)

        y -= 80

        # ── Título ────────────────────────────────────────────────────────────
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(largura / 2, y, "RECIBO DE SERVIÇO PRESTADO")

        y -= 18
        c.setFont("Helvetica", 9)
        c.drawCentredString(
            largura / 2, y,
            f"Recibo Nº {servico_dados['id']:06d}  —  "
            f"Data do Serviço: {_fmt_data(servico_dados['data_servico'])}  —  "
            f"Centro de Custo: {servico_dados.get('centro_custo', '')}"
        )

        y -= 28

        # ── Valor total em destaque ───────────────────────────────────────────
        c.setFillColor(colors.HexColor('#2c3e50'))
        c.roundRect(2 * cm, y - 8, largura - 4 * cm, 26, 4, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(largura / 2, y + 4,
                            f"Valor Total do Serviço: {_fmt_valor(valor_total)}")
        c.setFillColor(colors.black)

        y -= 30

        # ── Texto de quitação ─────────────────────────────────────────────────
        styles    = getSampleStyleSheet()
        st_just   = ParagraphStyle(
            "Just", parent=styles["Normal"],
            alignment=TA_JUSTIFY, fontName="Helvetica",
            fontSize=10, leading=15
        )

        if multi:
            nomes_str = ", ".join(
                f"<b>{p['nome']}</b>" for p in diaristas
            )
            texto_quitacao = (
                f"Recebemos de <b>{empresa.get('razao_social', '') if empresa else ''}</b> "
                f"a importância total de <b>{_fmt_valor(valor_total)}</b>, "
                f"rateada igualmente entre os abaixo assinados,"
                f"referente ao pagamento do serviço descrito. "
                f"Declaramos que nada mais há a reclamar, dando plena, geral e irrevogável quitação."
            )
        else:
            p0 = diaristas[0] if diaristas else {}
            texto_quitacao = (
                f"Recebi de <b>{empresa.get('razao_social', '') if empresa else ''}</b> "
                f"a importância de <b>{_fmt_valor(valor_total)}</b>, "
                f"referente ao pagamento do serviço abaixo descrito. "
                f"Declaro que nada mais há a reclamar, dando plena, geral e irrevogável quitação."
            )

        frame_quit = Frame(2 * cm, y - 3.2 * cm, largura - 4 * cm, 3.2 * cm,
                           showBoundary=0)
        frame_quit.addFromList([Paragraph(texto_quitacao, st_just)], c)
        y -= 2.7 * cm

        # ── Descrição do serviço ──────────────────────────────────────────────
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2.5 * cm, y, "DESCRIÇÃO DO SERVIÇO PRESTADO:")

        y -= 4
        st_desc = ParagraphStyle(
            "Desc", parent=styles["Normal"],
            fontName="Helvetica", fontSize=10, leading=14
        )
        frame_desc = Frame(2.5 * cm, y - 2.8 * cm, largura - 5 * cm, 2.8 * cm,
                           showBoundary=0)
        frame_desc.addFromList(
            [Paragraph(servico_dados.get('descricao', ''), st_desc)], c)
        

                # ── ASSINATURAS ───────────────────────────────────────────────────────
        y -= 2.5 * cm

        c.setFont("Helvetica-Bold", 10)
        c.drawString(2.5 * cm, y, "ASSINATURAS:")
        y -= 18

        # Assinaturas sempre uma abaixo da outra
        for p in diaristas:
            c.setStrokeColor(colors.HexColor('#2c3e50'))

            # linha assinatura
            c.line(3 * cm, y, largura - 3 * cm, y)

            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(largura / 2, y - 13, p['nome'])

            c.setFont("Helvetica", 9)
            c.drawCentredString(
                largura / 2,
                y - 25,
                f"CPF: {p['cpf']}   |   Rateio: {_fmt_valor(p['valor_rateio'])}"
            )

            y -= 45  # espaço entre assinaturas

        # ── TESTEMUNHAS (fixas) ───────────────────────────────────────────────
        y -= 10

        c.setFont("Helvetica-Bold", 10)
        c.drawString(2.5 * cm, y, "TESTEMUNHAS:")
        y -= 18

        # Testemunha 1
        c.line(3 * cm, y, largura - 3 * cm, y)
        c.setFont("Helvetica", 9)
        c.drawCentredString(largura / 2, y - 13, "Testemunha 1")
        y -= 35

        # Testemunha 2
        c.line(3 * cm, y, largura - 3 * cm, y)
        c.drawCentredString(largura / 2, y - 13, "Testemunha 2")
        y -= 35


        # ── Rodapé ────────────────────────────────────────────────────────────
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor('#7f8c8d'))
        rodape = (
            f"Documento gerado em "
            f"{datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        )
        if empresa:
            rodape += f" — {empresa.get('cidade', '')}/{empresa.get('uf', '')}"

        c.drawCentredString(largura / 2, 1.5 * cm, rodape)

        c.save()
        _abrir_pdf(caminho)
        return caminho

    @staticmethod
    def _numero_por_extenso(valor: float) -> str:
        partes    = f"{valor:.2f}".split('.')
        reais     = int(partes[0])
        centavos  = int(partes[1]) if len(partes) > 1 else 0
        if centavos > 0:
            return f"{reais} reais e {centavos:02d} centavos"
        return f"{reais} reais"