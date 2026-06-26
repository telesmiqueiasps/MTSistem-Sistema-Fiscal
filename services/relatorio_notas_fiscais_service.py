import os
import tempfile
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable, KeepTogether
)

from dao.empresa_dao import EmpresaDAO
from utils.auxiliares import resource_path


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


def _fmt_data_br(iso):
    if not iso:
        return "—"
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return iso


def _status_nota(nota: dict):
    if nota.get("pago"):
        return "pago", "Pago"
    if nota.get("qtd_recibos"):
        return "ok", "Com recibo"
    return "pendente", "Pendente"


class RelatorioNotasFiscaisPDF:

    @staticmethod
    def gerar(notas: list, filtros_desc: str, abrir: bool = True) -> str:
        """Gera o PDF do relatório de notas fiscais já filtradas e retorna
        o caminho do arquivo temporário criado."""
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        caminho = tmp.name
        tmp.close()

        try:
            empresa = EmpresaDAO().buscar_empresa()
        except Exception:
            empresa = None

        doc = SimpleDocTemplate(
            caminho,
            pagesize=landscape(A4),
            leftMargin=1.8 * cm,
            rightMargin=1.8 * cm,
            topMargin=1.5 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()

        cor_titulo = colors.HexColor('#1a2533')
        cor_header = colors.HexColor('#2c3e50')
        cor_header_txt = colors.white
        cor_total = colors.HexColor('#27ae60')
        cor_zebra = colors.HexColor('#f9fbfc')
        cor_borda = colors.HexColor('#dfe6e9')
        cor_texto_cinza = colors.HexColor('#7f8c8d')
        cor_pago = colors.HexColor('#27ae60')
        cor_ok = colors.HexColor('#2563eb')
        cor_pendente = colors.HexColor('#d97706')

        elementos = []

        # ── Cabeçalho com logo + empresa ─────────────────────────────────────
        header_data = []
        try:
            from reportlab.platypus import Image as RLImage
            logo_path = resource_path("Icones/logo_empresa.png")
            logo = RLImage(logo_path, width=1.8 * cm, height=1.8 * cm)
            logo.hAlign = 'LEFT'
            header_data.append([logo, ""])
        except Exception:
            header_data.append(["", ""])

        if empresa:
            empresa_txt = (
                f"<b>{empresa.get('razao_social', 'EMPRESA NÃO IDENTIFICADA')}</b><br/>"
                f"CNPJ/CPF: {empresa.get('cnpj', '')}  IE: {empresa.get('inscricao_estadual', '')}<br/>"
                f"{empresa.get('endereco', '')}, {empresa.get('cidade', '')}/{empresa.get('uf', '')}"
            )
        else:
            empresa_txt = "<i>Empresa não identificada</i>"

        empresa_style = ParagraphStyle(
            name='EmpresaHeader', fontSize=9.5, fontName='Helvetica',
            textColor=cor_titulo, alignment=TA_LEFT, leading=11, spaceAfter=2
        )
        header_data[0][1] = Paragraph(empresa_txt, empresa_style)

        header_table = Table(header_data, colWidths=[2.2 * cm, None])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (1, 0), (1, 0), 12),
            ('BACKGROUND', (0, 0), (-1, -1), colors.transparent),
        ]))

        elementos.extend([
            header_table,
            Spacer(1, 0.4 * cm),
            HRFlowable(width="100%", thickness=1, color=cor_titulo, spaceBefore=2, spaceAfter=10),
        ])

        # ── Título ────────────────────────────────────────────────────────────
        titulo_style = ParagraphStyle(
            name='TituloRel', parent=styles['Heading1'], fontSize=13,
            fontName='Helvetica-Bold', textColor=cor_titulo,
            alignment=TA_CENTER, spaceAfter=4
        )
        elementos.append(Paragraph("RELATÓRIO DE NOTAS FISCAIS DE SERVIÇO", titulo_style))

        info_linha = (
            f"{filtros_desc}   |   Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        elementos.append(Paragraph(
            info_linha,
            ParagraphStyle(name='Periodo', fontSize=8.5, textColor=cor_texto_cinza,
                          alignment=TA_CENTER, spaceAfter=12)
        ))

        # ── Resumo ────────────────────────────────────────────────────────────
        total_qtd = len(notas)
        total_pendentes = sum(1 for n in notas if _status_nota(n)[0] == "pendente")
        total_ok = sum(1 for n in notas if _status_nota(n)[0] == "ok")
        total_pagos = sum(1 for n in notas if _status_nota(n)[0] == "pago")
        valor_total = sum(n["valor"] for n in notas)

        resumo_txt = (
            f"Total de notas: <b>{total_qtd}</b>  |  "
            f"Pendentes: <b>{total_pendentes}</b>  |  "
            f"Com recibo: <b>{total_ok}</b>  |  "
            f"Pagas: <b>{total_pagos}</b>  |  "
            f"Valor total: <b>{_fmt_brl(valor_total)}</b>"
        )
        elementos.append(Paragraph(
            resumo_txt,
            ParagraphStyle(name='Resumo', fontSize=9, textColor=cor_titulo,
                          alignment=TA_CENTER, spaceAfter=10)
        ))

        # ── Tabela de notas ───────────────────────────────────────────────────
        if not notas:
            elementos.append(Paragraph(
                "Nenhuma nota fiscal encontrada com os filtros informados.",
                ParagraphStyle(name='Aviso', fontSize=11, textColor=colors.darkred, alignment=TA_CENTER)
            ))
        else:
            cabecalho = ["Nº NF", "Emitente", "CNPJ/CPF", "Competência",
                        "Emissão", "Valor", "Status"]
            col_widths = [2.2*cm, 6.5*cm, 4*cm, 3*cm, 3*cm, 3.5*cm, 3.5*cm]

            linhas = []
            cores_status = []
            for n in notas:
                status_key, status_txt = _status_nota(n)
                linhas.append([
                    n["numero"], n["emitente"] or "—", n.get("cnpj_cpf") or "—",
                    n["competencia"], _fmt_data_br(n["data_emissao"]),
                    _fmt_brl(n["valor"]), status_txt
                ])
                cores_status.append({"pago": cor_pago, "ok": cor_ok, "pendente": cor_pendente}[status_key])

            linha_total = ["TOTAL GERAL", "", "", "", "", _fmt_brl(valor_total), f"{total_qtd} nota(s)"]
            linhas.append(linha_total)

            tabela = Table([cabecalho] + linhas, colWidths=col_widths, repeatRows=1)

            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), cor_header),
                ('TEXTCOLOR', (0, 0), (-1, 0), cor_header_txt),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8.5),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                ('TOPPADDING', (0, 0), (-1, 0), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
                ('TOPPADDING', (0, 1), (-1, -1), 2),
                ('GRID', (0, 0), (-1, -1), 0.4, cor_borda),
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('FONTSIZE', (0, 1), (-1, -2), 7.5),
                ('ALIGN', (0, 1), (0, -2), 'CENTER'),
                ('ALIGN', (-2, 1), (-2, -2), 'RIGHT'),
                ('ALIGN', (-1, 1), (-1, -2), 'CENTER'),
                ('BACKGROUND', (0, -1), (-1, -1), cor_total),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 9),
                ('ALIGN', (-2, -1), (-1, -1), 'CENTER'),
                ('SPAN', (1, -1), (4, -1)),
            ]
            for i in range(1, len(linhas)):
                if i % 2 == 0:
                    table_style.append(('BACKGROUND', (0, i), (-1, i), cor_zebra))
            for i, cor in enumerate(cores_status, start=1):
                table_style.append(('TEXTCOLOR', (-1, i), (-1, i), cor))
                table_style.append(('FONTNAME', (-1, i), (-1, i), 'Helvetica-Bold'))

            tabela.setStyle(TableStyle(table_style))
            elementos.append(KeepTogether(tabela))

        # ── Rodapé ────────────────────────────────────────────────────────────
        cidade_uf = f"{empresa.get('cidade', '')}/{empresa.get('uf', '')}" if empresa else ""

        def rodape(canvas, doc_):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(cor_texto_cinza)
            canvas.drawString(1.8*cm, 1.2*cm,
                              f"Emitido em {cidade_uf} — {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
            canvas.drawRightString(landscape(A4)[0] - 1.8*cm, 1.2*cm, f"Página {doc_.page}")
            canvas.restoreState()

        doc.build(elementos, onFirstPage=rodape, onLaterPages=rodape)

        if abrir:
            _abrir_pdf(caminho)
        return caminho
