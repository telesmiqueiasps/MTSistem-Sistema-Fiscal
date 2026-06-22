import os
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, Image as RLImage)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from dao.empresa_dao import EmpresaDAO
from utils.auxiliares import resource_path


def _fmt_brl(valor):
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_data(s):
    if not s:
        return "—"
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return s


def _valor_por_extenso(valor):
    """Converte valor numérico para texto por extenso (simplificado)."""
    if valor is None:
        return "zero reais"

    inteiro = int(valor)
    centavos = round((valor - inteiro) * 100)

    unidades = ["", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove",
                "dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis",
                "dezessete", "dezoito", "dezenove"]
    dezenas = ["", "", "vinte", "trinta", "quarenta", "cinquenta",
               "sessenta", "setenta", "oitenta", "noventa"]
    centenas = ["", "cento", "duzentos", "trezentos", "quatrocentos",
                "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"]

    def _conv(n):
        if n == 0:
            return ""
        if n == 100:
            return "cem"
        if n < 20:
            return unidades[n]
        if n < 100:
            d, u = divmod(n, 10)
            return dezenas[d] + (" e " + unidades[u] if u else "")
        c, resto = divmod(n, 100)
        return centenas[c] + (" e " + _conv(resto) if resto else "")

    def _milhar(n):
        if n == 0:
            return ""
        if n <= 1000:
            return _conv(n)
        milhar, resto = divmod(n, 1000)
        p = "um mil" if milhar == 1 else _conv(milhar) + " mil"
        return p + (" e " + _conv(resto) if resto else "")

    reais = _milhar(inteiro) or "zero"
    reais_txt = reais + (" real" if inteiro == 1 else " reais")
    if centavos:
        centavos_txt = _conv(centavos) + (" centavo" if centavos == 1 else " centavos")
        return reais_txt + " e " + centavos_txt
    return reais_txt


class ReciboNFService:

    @staticmethod
    def gerar_pdf_recibo(nota: dict, output_path: str):
        """Gera o PDF do recibo de pagamento de uma nota fiscal, usando os
        dados da empresa já cadastrados em 'Cadastro da Empresa'."""
        try:
            empresa = EmpresaDAO().buscar_empresa() or {}
        except Exception:
            empresa = {}

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2.3 * cm,
            leftMargin=2.3 * cm,
            topMargin=1.8 * cm,
            bottomMargin=1.8 * cm,
        )

        azul = colors.HexColor("#1E3A8A")
        azul_claro = colors.HexColor("#DBEAFE")
        cinza = colors.HexColor("#64748B")
        cinza_claro = colors.HexColor("#F8FAFC")
        cinza_borda = colors.HexColor("#E2E8F0")
        preto = colors.HexColor("#0F172A")

        styles = getSampleStyleSheet()
        story = []

        empresa_nome = empresa.get("razao_social") or "EMPRESA"
        empresa_cnpj = empresa.get("cnpj", "")
        empresa_ie = empresa.get("inscricao_estadual", "")
        empresa_end = empresa.get("endereco", "")
        data_nf = _fmt_data(nota.get("data_emissao"))

        logo_flowable = None
        try:
            logo_path = resource_path("Icones/logo_empresa.png")
            if os.path.exists(logo_path):
                logo_flowable = RLImage(logo_path, width=2.1 * cm, height=2.1 * cm,
                                         kind="proportional")
        except Exception:
            logo_flowable = None

        header_text = Paragraph(
            f'<font color="#1E3A8A"><b>{empresa_nome}</b></font><br/>'
            f'<font size="9" color="#64748B">{empresa_cnpj}</font><br/>'
            f'<font size="9" color="#64748B">{empresa_ie}</font><br/>'
            f'<font size="9" color="#64748B">{empresa_end}</font>',
            ParagraphStyle("h", parent=styles["Normal"], fontSize=9, leading=11, alignment=TA_LEFT)
        )
        header_right = Paragraph(
            '<font color="#1E3A8A"><b>RECIBO DE PAGAMENTO</b></font><br/>'
            f'<font size="9" color="#64748B">Nº da Nota Fiscal</font><br/>'
            f'<font size="12" color="#1E3A8A"><b>{nota.get("numero", "—")}</b></font>',
            ParagraphStyle("n", parent=styles["Normal"], fontSize=9, leading=12, alignment=TA_RIGHT)
        )

        if logo_flowable is not None:
            logo_block = Table(
                [[logo_flowable], [header_text]],
                colWidths=["100%"],
                style=TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ])
            )
            header_table = Table([[logo_block, header_right]], colWidths=["62%", "38%"])
        else:
            header_table = Table([[header_text, header_right]], colWidths=["62%", "38%"])

        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=2, color=azul, spaceAfter=14))

        valor_txt = _fmt_brl(nota["valor"])
        extenso = _valor_por_extenso(nota["valor"]).capitalize()

        valor_table = Table([[
            Paragraph(
                f'<font size="10" color="#64748B">VALOR LÍQUIDO</font><br/>'
                f'<font size="14" color="#1E3A8A"><b>{valor_txt}</b></font><br/>'
                f'<font size="9" color="#475569">({extenso})</font>',
                ParagraphStyle("v", parent=styles["Normal"], fontSize=10, leading=14, alignment=TA_CENTER)
            )
        ]], colWidths=["100%"])
        valor_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), azul_claro),
            ("ROUNDEDCORNERS", (0, 0), (-1, -1), [7, 7, 7, 7]),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#BFDBFE")),
        ]))
        story.append(valor_table)
        story.append(Spacer(1, 0.35 * cm))

        data_table = Table([[
            Paragraph(
                f'<font size="11" color="#0F172A"><b>Data do recebimento:</b> {data_nf}</font>',
                ParagraphStyle("data_nf", parent=styles["Normal"], fontSize=10, leading=12, alignment=TA_CENTER)
            )
        ]], colWidths=["100%"])
        data_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), cinza_claro),
            ("BOX", (0, 0), (-1, -1), 1, cinza_borda),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(data_table)
        story.append(Spacer(1, 0.35 * cm))

        label_style = ParagraphStyle("lbl", parent=styles["Normal"], fontSize=7.5, textColor=cinza, spaceAfter=1)
        value_style = ParagraphStyle("val", parent=styles["Normal"], fontSize=9.5, textColor=preto,
                                      spaceAfter=0, fontName="Helvetica-Bold")

        def cell(label, value):
            return [Paragraph(label.upper(), label_style),
                    Paragraph(str(value) if value else "—", value_style)]

        linha1 = cell("Recebedor", nota.get("emitente") or "—") + cell("CNPJ / CPF", nota.get("cnpj_cpf") or "—")
        linha2 = cell("Competência", nota.get("competencia") or "—") + cell("Data da NF", data_nf)

        dados_table = Table([linha1, linha2], colWidths=["18%", "32%", "18%", "32%"])
        dados_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), cinza_claro),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, cinza_borda),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(dados_table)
        story.append(Spacer(1, 1.0 * cm))

        desc_text = nota.get("descricao_servico") or "Serviços prestados conforme nota fiscal"
        story.append(Paragraph(
            f'<font size="9"><b>Descrição do serviço:</b> {desc_text}</font>',
            ParagraphStyle("desc", parent=styles["Normal"], fontSize=9, leading=11,
                           textColor=preto, alignment=TA_JUSTIFY)
        ))
        story.append(Spacer(1, 2.0 * cm))

        if nota.get("observacoes"):
            obs_table = Table([[
                Paragraph("<b>Observações:</b> " + nota["observacoes"],
                          ParagraphStyle("obs", parent=styles["Normal"], fontSize=8.5,
                                        textColor=cinza, leading=11))
            ]], colWidths=["100%"])
            obs_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FDE68A")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(obs_table)
            story.append(Spacer(1, 1.0 * cm))

        decl = (
            f"Declaro que recebi de <b>{empresa_nome}</b>, a importância de <b>{valor_txt}</b> "
            f"({extenso}), referente aos serviços prestados conforme Nota Fiscal nº <b>{nota.get('numero', '—')}</b>, "
            f"competência <b>{nota.get('competencia', '—')}</b>, "
            f"emitida por <b>{nota.get('emitente', '—')}</b>, onde ASSINA e CONFIRMA "
            f"como verdadeira as informações aqui prestadas, comprometendo-me dessa forma a não reclamar "
            f"nenhum outro valor a respeito do mesmo, do qual dou plena, geral e irrevogável quitação do "
            f"exposto acima, declarando de direito a quem possa interessar e fazendo provas de direito do "
            f"acerto estabelecido."
        )
        story.append(Paragraph(
            decl,
            ParagraphStyle("decl", parent=styles["Normal"], fontSize=9.5, leading=14,
                           textColor=preto, alignment=TA_JUSTIFY, borderPad=10,
                           borderColor=cinza_borda, borderWidth=1, backColor=cinza_claro)
        ))
        story.append(Spacer(1, 2.0 * cm))

        assin_table = Table([[
            Paragraph(
                "__________________________________________<br/>"
                f'<font size="9" color="#64748B"><br/>{nota.get("emitente", "")}<br/>{nota.get("cnpj_cpf") or "—"}</font>',
                ParagraphStyle("a1", parent=styles["Normal"], fontSize=9.5, leading=14, alignment=TA_CENTER)
            )
        ]], colWidths=["100%"])
        assin_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(assin_table)
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph(
            '<font size="8" color="#94A3B8">Documento gerado pelo MTSistem - Sistema Fiscal</font>',
            ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, alignment=TA_CENTER)
        ))

        doc.build(story)
        return output_path

    @staticmethod
    def abrir_pdf(caminho: str):
        try:
            os.startfile(caminho)
        except AttributeError:
            import subprocess
            subprocess.call(["xdg-open", caminho])
