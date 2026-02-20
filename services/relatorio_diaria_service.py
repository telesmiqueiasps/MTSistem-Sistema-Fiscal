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
            pass  # silencioso se falhar


def _fmt(valor) -> str:
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


class RelatorioDiariaPDF:

    @staticmethod
    def gerar(parent, dao, agrupamento: str, data_ini: str, data_fim: str):

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        caminho = tmp.name
        tmp.close()

        try:
            empresa = EmpresaDAO().buscar_empresa()
        except Exception:
            empresa = None

        # Configuração do documento
        doc = SimpleDocTemplate(
            caminho,
            pagesize=landscape(A4),
            leftMargin=1.8*cm,
            rightMargin=1.8*cm,
            topMargin=1.5*cm,
            bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()

        # Cores
        cor_titulo     = colors.HexColor('#1a2533')
        cor_header     = colors.HexColor('#2c3e50')
        cor_header_txt = colors.white
        cor_total      = colors.HexColor('#27ae60')
        cor_zebra      = colors.HexColor('#f9fbfc')
        cor_borda      = colors.HexColor('#dfe6e9')
        cor_texto_cinza= colors.HexColor('#7f8c8d')

        elementos = []

        # ── Logo + Nome Empresa ─────────────────────────────────────
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
            empresa_txt = f"<b>{empresa.get('razao_social', 'EMPRESA NÃO IDENTIFICADA')}</b><br/>CNPJ/CPF: {empresa.get('cnpj', '')}   IE: {empresa.get('inscricao_estadual', '')}<br/>{empresa.get('endereco', '')}, {empresa.get('cidade', '')} - {empresa.get('uf', '')}"
        else:
            empresa_txt = "<i>Empresa não identificada</i>"

        empresa_style = ParagraphStyle(
            name='EmpresaHeader',
            fontSize=11,
            fontName='Helvetica',
            textColor=cor_titulo,
            alignment=TA_LEFT,
            leading=13,
            spaceAfter=4
        )
        header_data[0][1] = Paragraph(empresa_txt, empresa_style)

        header_table = Table(header_data, colWidths=[2.2*cm, None])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (1,0), (1,0), 12),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BACKGROUND', (0,0), (-1,-1), colors.transparent),
        ]))

        elementos.extend([
            header_table,
            Spacer(1, 0.4*cm),
            HRFlowable(width="100%", thickness=1, color=cor_titulo, spaceBefore=2, spaceAfter=10),
        ])

        # ── Título ──────────────────────────────────────────────────
        titulo_style = ParagraphStyle(
            name='TituloRel',
            parent=styles['Heading1'],
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=cor_titulo,
            alignment=TA_CENTER,
            spaceAfter=6
        )

        label_map = {
            "diarista": "DIARISTA",
            "centro_custo": "CENTRO DE CUSTO",
            "mes": "MÊS"
        }
        agrup_label = label_map.get(agrupamento, agrupamento.upper())

        elementos.append(Paragraph(
            f"RELATÓRIO DE DIÁRIAS — POR {agrup_label}",
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
                textColor=colors.gray,
                alignment=TA_CENTER,
                spaceAfter=18
            )
        ))

        # ── Preparar dados da tabela ────────────────────────────────
        if agrupamento == "diarista":
            dados = dao.relatorio_por_diarista(data_ini, data_fim)
            cabecalho = ["Diarista", "CPF", "Qtde Diárias", "Valor Total"]
            col_widths = [9.5*cm, 5*cm, 4.2*cm, 6*cm]

            linhas = [
                [nome or "", cpf or "", f"{qtd_diarias:g}", _fmt(valor)]
                for nome, cpf, _, qtd_diarias, valor in dados
            ]

            total_qtd = sum(qtd_diarias for _, _, _, qtd_diarias, _ in dados)
            total_val = sum(valor for _, _, _, _, valor in dados)

            linha_total = ["TOTAL GERAL", "", f"{total_qtd:g}", _fmt(total_val)]

        elif agrupamento == "centro_custo":
            dados = dao.relatorio_por_centro_custo(data_ini, data_fim)
            cabecalho = ["Centro de Custo", "Qtde Diárias", "Valor Total"]
            col_widths = [14*cm, 5*cm, 6*cm]

            linhas = [
                [centro or "", f"{qtd_diarias:g}", _fmt(valor)]
                for centro, _, qtd_diarias, valor in dados
            ]

            total_qtd = sum(qtd_diarias for _, _, qtd_diarias, _ in dados)
            total_val = sum(valor for _, _, _, valor in dados)

            linha_total = ["TOTAL GERAL", f"{total_qtd:g}", _fmt(total_val)]

        else:  # mês
            dados = dao.relatorio_por_mes(data_ini, data_fim)
            cabecalho = ["Mês/Ano", "Qtde Diárias", "Valor Total"]
            col_widths = [14*cm, 5*cm, 6*cm]

            linhas = [
                [mes or "", f"{qtd_diarias:g}", _fmt(valor)]
                for mes, qtd_diarias, valor in dados
            ]

            total_qtd = sum(qtd_diarias for _, qtd_diarias, _ in dados)
            total_val = sum(valor for _, _, valor in dados)

            linha_total = ["TOTAL GERAL", f"{total_qtd:g}", _fmt(total_val)]

        if not dados:
            elementos.append(Paragraph(
                "Nenhuma diária registrada no período informado.",
                ParagraphStyle(name='Aviso', fontSize=11, textColor=colors.darkred, alignment=TA_CENTER)
            ))
        else:
            linhas.append(linha_total)


            # Criar tabela
            tabela_dados = [cabecalho] + linhas
            tabela = Table(tabela_dados, colWidths=col_widths, repeatRows=1)

            # Estilo da tabela
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

                # Linhas de dados - zebra
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('BACKGROUND', (0, 2), (-1, -2), cor_zebra),  # começa na linha 2 (índice 1 é primeira linha de dados)

                # Total
                ('BACKGROUND', (0, -1), (-1, -1), cor_total),
                ('TEXTCOLOR',  (0, -1), (-1, -1), colors.white),
                ('FONTNAME',   (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, -1), (-1, -1), 11.5),
                ('ALIGN',      (-2, -1), (-1, -1), 'RIGHT'),   # valores à direita
                ('ALIGN',      (0, -1), (0, -1), 'LEFT'),

                # Alinhamentos específicos
                ('ALIGN',      (1 if agrupamento == "diarista" else 0, 1), (-2, -2), 'LEFT'),
                ('ALIGN',      (-2, 1), (-2, -2), 'CENTER'),   # qtd diárias
                ('ALIGN',      (-1, 1), (-1, -2), 'RIGHT'),    # valores
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