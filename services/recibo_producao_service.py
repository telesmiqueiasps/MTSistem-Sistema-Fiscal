from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from datetime import datetime, date
from tkinter import filedialog
import tempfile
import os
import sys
import subprocess
from dao.empresa_dao import EmpresaDAO
from utils.auxiliares import resource_path


def formatar_data_br(data):
    if not data:
        return None

    if isinstance(data, (datetime, date)):
        return data.strftime("%d-%m-%Y")

    return datetime.strptime(data, "%Y-%m-%d").strftime("%d-%m-%Y")



def abrir_pdf(caminho):
    if not os.path.exists(caminho):
        return

    try:
        if sys.platform.startswith("win"):
            os.startfile(caminho)
        elif sys.platform.startswith("darwin"):
            subprocess.call(["open", caminho])
        else:
            subprocess.call(["xdg-open", caminho])
    except Exception as e:
        print(f"Erro ao abrir PDF: {e}")


class ReciboProducaoService:
    def __init__(self, dao):
        self.dao = dao

    def gerar_recibo_individual(
        self,
        producao_id: int,
        diarista_id: int,
        salvar: bool = False,
        abrir: bool = True
    ) -> str:

        producao = self.dao.get_producao(producao_id)
        if not producao:
            raise ValueError("Produção não encontrada")

        totais = self.dao.get_totais_diaristas(producao_id)
        diarista = next((t for t in totais if t['id'] == diarista_id), None)

        if not diarista:
            raise ValueError("Diarista não encontrado nesta produção")

        # =========================
        # Caminho do arquivo
        # =========================
        if salvar:
            caminho = filedialog.asksaveasfilename(
                title="Salvar recibo de produção",
                defaultextension=".pdf",
                filetypes=[("Arquivo PDF", "*.pdf")],
                initialfile=f"recibo_{diarista['nome']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            if not caminho:
                return None
        else:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            caminho = tmp.name
            tmp.close()

        # =========================
        # Criar PDF
        # =========================
        c = canvas.Canvas(caminho, pagesize=A4)
        largura, altura = A4

        y_topo = altura - 3 * cm

        # =========================
        # Título
        # =========================
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(largura / 2, y_topo, "RECIBO DE PAGAMENTO DE PRODUÇÃO")

        y = y_topo - 40

        # Valor em destaque
        c.setFont("Helvetica-Bold", 13)
        c.drawRightString(
            largura - 3 * cm,
            y,
            f"R$ {diarista['valor_total']:.2f}"
        )

        y -= 50

        # =========================
        # Texto corrido (justificado)
        # =========================
        styles = getSampleStyleSheet()
        style = ParagraphStyle(
            "Justificado",
            parent=styles["Normal"],
            alignment=TA_JUSTIFY,
            fontName="Helvetica",
            fontSize=11,
            leading=16
        )

        texto = f"""
        Recebi a importância de <b>R$ {diarista['valor_total']:.2f}</b> referente
        à minha participação na produção <b>{producao['nome']}</b>,
        realizada no período de <b>{producao['data_inicio']}</b> até
        <b>{producao['data_fim'] or 'a presente data'}</b>, dando plena,
        geral e irrevogável quitação do valor acima descrito.
        """

        frame = Frame(
            2 * cm,
            7 * cm,
            largura - 4 * cm,
            altura - 14 * cm,
            showBoundary=0
        )

        frame.addFromList([Paragraph(texto, style)], c)

        # =========================
        # Assinatura
        # =========================
        y_ass = 5 * cm
        c.line(5 * cm, y_ass, largura - 5 * cm, y_ass)

        c.setFont("Helvetica", 11)
        c.drawCentredString(
            largura / 2,
            y_ass - 15,
            f"{diarista['nome']} – CPF: {diarista['cpf']}"
        )

        # =========================
        # Rodapé
        # =========================
        c.setFont("Helvetica", 9)
        c.drawString(
            2 * cm,
            2 * cm,
            f"Emitido em {datetime.now().strftime('%d/%m/%Y')}"
        )

        c.showPage()
        c.save()

        if abrir:
            abrir_pdf(caminho)

        return caminho

    def gerar_recibo_geral(
        self,
        producao_id: int,
        salvar: bool = False,
        abrir: bool = True
    ) -> str:

        producao = self.dao.get_producao(producao_id)
        if not producao:
            raise ValueError("Produção não encontrada")

        totais = self.dao.get_totais_diaristas(producao_id)
        if not totais:
            raise ValueError("Nenhum diarista encontrado")
        
        data_inicio = formatar_data_br(producao["data_inicio"])
        data_fim = formatar_data_br(producao["data_fim"]) if producao["data_fim"] else "a presente data"


        # =========================
        # Caminho do arquivo
        # =========================
        if salvar:
            caminho = filedialog.asksaveasfilename(
                title="Salvar recibo geral",
                defaultextension=".pdf",
                filetypes=[("Arquivo PDF", "*.pdf")],
                initialfile=f"recibo_geral_{producao['nome']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            if not caminho:
                return None
        else:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            caminho = tmp.name
            tmp.close()

        # =========================
        # Buscar empresa
        # =========================
        empresa = EmpresaDAO().buscar_empresa()
        if not empresa:
            raise Exception("Empresa não cadastrada.")
        
        # =========================
        # Criar PDF
        # =========================
        c = canvas.Canvas(caminho, pagesize=A4)
        largura, altura = A4

        y_topo = altura - 80

        # =========================
        # Logo
        # =========================
        try:
            logo = resource_path("Icones/logo_empresa.png")
            c.drawImage(
                logo,
                (largura - 80) / 2,
                y_topo - 10,
                width=80,
                height=80,
                preserveAspectRatio=True,
                mask="auto"
            )
        except Exception:
            pass

        # =========================
        # Cabeçalho Empresa
        # =========================
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(largura / 2, y_topo - 10, empresa["razao_social"])

        c.setFont("Helvetica", 10)
        c.drawCentredString(
            largura / 2,
            y_topo - 28,
            f"CNPJ: {empresa['cnpj']} | IE: {empresa['inscricao_estadual']}"
        )

        c.drawCentredString(
            largura / 2,
            y_topo - 44,
            f"{empresa['endereco']} - {empresa['cidade']}/{empresa['uf']}"
        )

        c.line(2 * cm, y_topo - 60, largura - 2 * cm, y_topo - 60)

        # =========================
        # Título
        # =========================
        y = y_topo - 120

        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(largura / 2, y, "RECIBO GERAL DE PRODUÇÃO")

        y -= 25
        c.setFont("Helvetica", 10)
        c.drawCentredString(
            largura / 2,
            y,
            f"{producao['nome']} • {data_inicio} até {data_fim}"
        )

        # =========================
        # Total geral (destaque)
        # =========================
        valor_total_geral = sum(t["valor_total"] for t in totais)
        total_sacos_geral = sum(t["total_sacos"] for t in totais)


        y -= 40
        c.setFont("Helvetica-Bold", 13)
        c.drawRightString(
            largura - 3 * cm,
            y,
            f"TOTAL: {total_sacos_geral} SACOS  |  R$ {valor_total_geral:.2f}"
        )


        # =========================
        # Texto Justificado
        # =========================
        styles = getSampleStyleSheet()
        style = ParagraphStyle(
            "Justificado",
            parent=styles["Normal"],
            alignment=TA_JUSTIFY,
            fontName="Helvetica",
            fontSize=11,
            leading=16
        )

        texto = f"""
        Recebemos de <b>{empresa['razao_social']}</b>, a importância total de
        <b>R$ {valor_total_geral:.2f}</b> referente aos pagamentos da produção de
        <b>{producao['nome']}</b>, ocorrida no período de
        <b>{data_inicio}</b> até <b>{data_fim}</b>, onde ASSINAMOS e CONFIRMAMOS
        como verdadeiras as informações aqui prestadas, comprometendo-nos a não
        reclamar nenhum outro valor a respeito da mesma, no qual damos plena,
        geral e irrevogável quitação dos pagamentos aqui relacionados.
        """


        frame = Frame(
            2 * cm,
            altura - 18 * cm,
            largura - 4 * cm,
            4 * cm,
            showBoundary=0
        )

        frame.addFromList([Paragraph(texto, style)], c)

        y = altura - 20 * cm
 

        # =========================
        # Assinatura
        # =========================
        
        c.setFont("Helvetica", 10)

        for t in totais:
            if y < 4 * cm:
                c.showPage()
                y = altura - 4 * cm
                c.setFont("Helvetica", 10)

            # Linha de assinatura
            c.line(4 * cm, y, largura - 4 * cm, y)
            y -= 14

            c.drawCentredString(
                largura / 2,
                y,
                f"{t['nome']} – CPF: {t['cpf']} | Valor: R$ {t['valor_total']:.2f}"
            )

            y -= 30


        # =========================
        # Rodapé
        # =========================
        c.setFont("Helvetica", 9)
        c.drawString(
            2 * cm,
            2 * cm,
            f"Emitido em {empresa['cidade']}/{empresa['uf']} - {datetime.now().strftime('%d/%m/%Y')}"
        )

        c.showPage()
        c.save()

        if abrir:
            abrir_pdf(caminho)

        return caminho

