import os
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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
        except:
            pass


def _fmt(valor) -> str:
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


class RelatorioServicoPDF:

    @staticmethod
    def gerar(parent, dao, agrupamento: str, data_ini: str, data_fim: str):
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
            leftMargin=1.8*cm,
            rightMargin=1.8*cm,
            topMargin=1.5*cm,
            bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()

        # Cores consistentes com o outro relatório
        cor_titulo     = colors.HexColor('#1a2533')
        cor_header     = colors.HexColor('#2c3e50')
        cor_header_txt = colors.white
        cor_total      = colors.HexColor('#27ae60')
        cor_zebra      = colors.HexColor('#f9fbfc')
        cor_borda      = colors.HexColor('#dfe6e9')
        cor_texto_cinza= colors.HexColor('#7f8c8d')

        elementos = []

        # ── Cabeçalho com logo + empresa ─────────────────────────────
        header_data = []

        try:
            from reportlab.platypus import Image as RLImage
            logo_path = resource_path("Icones/logo_empresa.png")
            logo = RLImage(logo_path, width=1.8*cm, height=1.8*cm)
            logo.hAlign = 'LEFT'
            header_data.append([logo, ""])
        except:
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
            name='EmpresaHeader',
            fontSize=11,
            fontName='Helvetica',
            textColor=cor_titulo,
            alignment=TA_LEFT,
            leading=13,
            spaceAfter=2
        )
        header_data[0][1] = Paragraph(empresa_txt, empresa_style)

        header_table = Table(header_data, colWidths=[2.2*cm, None])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (1,0), (1,0), 12),
            ('BACKGROUND', (0,0), (-1,-1), colors.transparent),
        ]))

        elementos.extend([
            header_table,
            Spacer(1, 0.4*cm),
            HRFlowable(width="100%", thickness=1, color=cor_titulo, spaceBefore=2, spaceAfter=10),
        ])

        # ── Título ────────────────────────────────────────────────────
        titulo_style = ParagraphStyle(
            name='TituloRel',
            parent=styles['Heading1'],
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=cor_titulo,
            alignment=TA_CENTER,
            spaceAfter=6
        )

        label_agrup = "CENTRO DE CUSTO" if agrupamento == "centro_custo" else "DIARISTA"
        elementos.append(Paragraph(
            f"RELATÓRIO DE SERVIÇOS — POR {label_agrup}",
            titulo_style
        ))

        periodo = (
            f"Período: {datetime.strptime(data_ini, '%Y-%m-%d').strftime('%d/%m/%Y')} "
            f"até {datetime.strptime(data_fim, '%Y-%m-%d').strftime('%d/%m/%Y')}   |   "
            f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )

        elementos.append(Paragraph(
            periodo,
            ParagraphStyle(
                name='Periodo',
                fontSize=10,
                textColor=cor_texto_cinza,
                alignment=TA_CENTER,
                spaceAfter=18
            )
        ))

        # ── Preparar dados da tabela ──────────────────────────────────
        if agrupamento == "centro_custo":
            dados = dao.relatorio_por_centro_custo(data_ini, data_fim)
            cabecalho = ["Centro de Custo", "Qtd. Serviços", "Valor Total"]
            col_widths = [14*cm, 5*cm, 6*cm]

            linhas = []
            total_qtd = 0.0
            total_val = 0.0

            for row in dados:
                if len(row) != 3:
                    print(f"[DEBUG] Linha inválida em centro_custo (esperado 3 colunas): {row}")
                    continue
                centro, qtd_servicos, valor = row
                linhas.append([centro or "—", f"{qtd_servicos:g}", _fmt(valor or 0)])
                total_qtd += float(qtd_servicos or 0)
                total_val += float(valor or 0)

            linha_total = ["TOTAL GERAL", f"{total_qtd:g}", _fmt(total_val)]

        else:  # diarista
            dados = dao.relatorio_por_diarista(data_ini, data_fim)
            cabecalho = ["Diarista", "CPF", "Qtd. Serviços", "Valor Total"]
            col_widths = [9.5*cm, 5*cm, 4.2*cm, 6*cm]

            linhas = []
            total_qtd = 0.0
            total_val = 0.0

            for row in dados:
                if len(row) != 4:
                    print(f"[DEBUG] Linha inválida em diarista (esperado 4 colunas): {row}")
                    continue
                nome, cpf, qtd_servicos, valor = row
                linhas.append([nome or "—", cpf or "—", f"{qtd_servicos:g}", _fmt(valor or 0)])
                total_qtd += float(qtd_servicos or 0)
                total_val += float(valor or 0)

            linha_total = ["TOTAL GERAL", "—", f"{total_qtd:g}", _fmt(total_val)]

        if not dados:
            elementos.append(Paragraph(
                "Nenhum serviço registrado no período informado.",
                ParagraphStyle(name='Aviso', fontSize=11, textColor=colors.darkred, alignment=TA_CENTER)
            ))
        else:
            linhas.append(linha_total)

            tabela_dados = [cabecalho] + linhas
            tabela = Table(tabela_dados, colWidths=col_widths, repeatRows=1)

            table_style = TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), cor_header),
                ('TEXTCOLOR',  (0, 0), (-1, 0), cor_header_txt),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, 0), 11),
                ('ALIGN',      (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING',(0,0), (-1,-1), 6),
                ('BOTTOMPADDING',(0,0), (-1,0), 8),
                ('TOPPADDING',  (0,0), (-1,0), 8),

                # Bordas
                ('GRID', (0,0), (-1,-1), 0.4, cor_borda),

                # Zebra nas linhas de dados (exclui total)
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('BACKGROUND', (0, 2), (-1, -2), cor_zebra),  # alterna a partir da 2ª linha de dados

                # Total
                ('BACKGROUND', (0, -1), (-1, -1), cor_total),
                ('TEXTCOLOR',  (0, -1), (-1, -1), colors.white),
                ('FONTNAME',   (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, -1), (-1, -1), 11.5),
                ('ALIGN',      (-2, -1), (-1, -1), 'RIGHT'),
                ('ALIGN',      (0, -1), (0, -1), 'LEFT'),

                # Alinhamentos por coluna
                ('ALIGN',      (1 if agrupamento == "diarista" else 0, 1), (-2, -2), 'LEFT'),
                ('ALIGN',      (-2, 1), (-2, -2), 'CENTER'),   # qtd serviços
                ('ALIGN',      (-1, 1), (-1, -2), 'RIGHT'),    # valor
            ])

            tabela.setStyle(table_style)
            elementos.append(KeepTogether(tabela))


        # ── Rodapé ────────────────────────────────────────────────────
        cidade_uf = f"{empresa.get('cidade', '')}/{empresa.get('uf', '')}" if empresa else ""

        def rodape(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(cor_texto_cinza)
            canvas.drawString(1.8*cm, 1.2*cm, f"Emitido em {cidade_uf} — {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
            canvas.drawRightString(landscape(A4)[0] - 1.8*cm, 1.2*cm, f"Página {doc.page}")
            canvas.restoreState()

        doc.build(elementos, onFirstPage=rodape, onLaterPages=rodape)
        _abrir_pdf(caminho)
        return caminho