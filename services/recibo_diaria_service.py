from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime
from tkinter import filedialog
import tempfile
import os
import sys
import subprocess
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY


from dao.empresa_dao import EmpresaDAO
from utils.auxiliares import resource_path


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


def gerar_pdf_recibo_diaria(dados, salvar=False, abrir=True):
    # =========================
    # Caminho do arquivo
    # =========================
    if salvar:
        caminho = filedialog.asksaveasfilename(
            title="Salvar recibo de diária",
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialfile=f"recibo_diaria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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

    y = altura - 80

    # =========================
    # Logo
    # =========================
    logo_largura = 80
    logo_altura = 80

    try:
        caminho_logo = resource_path("Icones/logo_empresa.png")
        c.drawImage(
            caminho_logo,
            (largura - logo_largura) / 2,  # 👈 correção
            y - 10,
            width=logo_largura,
            height=logo_altura,
            preserveAspectRatio=True,
            mask="auto"
        )
    except Exception:
        pass

    # =========================
    # Cabeçalho Empresa
    # =========================
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(largura / 2, y - 10, empresa["razao_social"])

    c.setFont("Helvetica", 10)
    c.drawCentredString(
        largura / 2,
        y - 28,
        f"CNPJ/CPF: {empresa['cnpj']}  |  IE: {empresa['inscricao_estadual']}"
    )

    endereco = (
        f"{empresa['endereco']} - CEP: {empresa['cep']} "
        f"- {empresa['cidade']}/{empresa['uf']}"
    )
    c.drawCentredString(largura / 2, y - 44, endereco)

    c.line(2 * cm, y - 60, largura - 2 * cm, y - 60)

    # =========================
    # Título
    # =========================
    if dados["tipo_diaria"] == "com_hora":
        titulo = (
            f"RECIBO DE DIÁRIA E HORA EXTRA"
        )
    else:
        titulo = "RECIBO DE DIÁRIA"

    y_atual = y - 120

    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(largura / 2, y_atual, titulo)

    y_atual -= 60

    valor_total = f"R$ {dados['valor_total']:.2f}"
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(largura - 4 * cm, y_atual, valor_total)

    # =========================
    # Texto corrido (JUSTIFICADO)
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

    valor_total = f"R$ {dados['valor_total']:.2f}"
    qtd_diarias = dados["qtd_diarias"]

    if dados["tipo_diaria"] == "com_hora":
        complemento = (
            f"e {dados['qtd_horas']} hora(s) extra(s) "
            f"na produção de {dados['centro']}"
        )
    else:
        complemento = "pela prestação do serviço abaixo descrito"

    texto = f"""
    Recebi de(a) <b>{empresa['razao_social']}</b>, inscrito(a) sob CNPJ/CPF nº
    <b>{empresa['cnpj']}</b>, a importância de <b>{valor_total}</b> referente ao
    pagamento de <b>{qtd_diarias}</b> diária(s) {complemento}, onde ASSINO E
    CONFIRMO como verdadeiras as informações aqui prestadas, comprometendo-me
    dessa forma a não reclamar outro valor a respeito da mesma, do qual dou
    plena, geral e irrevogável quitação de pago do exposto acima.
    """

    frame = Frame(
        2 * cm,
        7 * cm,
        largura - 4 * cm,
        altura - 17 * cm,
        showBoundary=0
    )

    frame.addFromList([Paragraph(texto, style)], c)

    # =========================
    # Detalhamento financeiro
    # =========================
    y_atual = altura - 17 * cm
    y_atual -= 40
    y = y_atual
    c.setFont("Helvetica", 10)

    if dados["tipo_diaria"] == "com_hora":
        c.drawString(
            2 * cm,
            y,
            f"Valor referente às diárias: R$ {dados['vlr_diaria_hora']:.2f}"
        )
        y -= 14
        c.drawString(
            2 * cm,
            y,
            f"Valor referente às horas extras: R$ {dados['vlr_horas_extras']:.2f}"
        )
    else:
        c.drawString(
            2 * cm,
            y,
            f"Serviço prestado: {dados.get('descricao', '')}"
        )

    # =========================
    # Assinatura
    # =========================
    y_atual -= 80
    y = y_atual
    c.line(4 * cm, y, largura - 4 * cm, y)

    c.drawCentredString(
        largura / 2,
        y - 15,
        f"{dados['nome']} – CPF: {dados['cpf']}"
    )

    # =========================
    # Rodapé
    # =========================
    c.drawString(
        2 * cm,
        2 * cm,
        f"Emitido e assinado em: {empresa['cidade']}/{empresa['uf']} - {dados['data_emissao']}"
    )

    c.showPage()
    c.save()

    if abrir:
        abrir_pdf(caminho)

    return caminho

