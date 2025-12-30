from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime
from tkinter import filedialog
import tempfile
import os
import sys
import subprocess

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
    # Buscar dados da empresa
    # =========================
    empresa = EmpresaDAO().buscar_empresa()
    if not empresa:
        raise Exception("Empresa não cadastrada.")

    # =========================
    # Criar PDF
    # =========================
    c = canvas.Canvas(caminho, pagesize=A4)
    largura, altura = A4

    y = altura - 40

    # =========================
    # Logo
    # =========================
    try:
        caminho_logo = resource_path("Icones/logo_empresa.png")
        c.drawImage(
            caminho_logo,
            2 * cm,
            y - 60,
            width=60,
            height=60,
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
        f"CNPJ: {empresa['cnpj']}  |  IE: {empresa['inscricao_estadual']}"
    )

    endereco_completo = (
        f"{empresa['endereco']} - CEP: {empresa['cep']} "
        f"- {empresa['cidade']}/{empresa['uf']}"
    )

    c.drawCentredString(largura / 2, y - 44, endereco_completo)

    # Linha separadora
    c.line(2 * cm, y - 60, largura - 2 * cm, y - 60)

    # =========================
    # Título Recibo
    # =========================
    y = y - 90
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(largura / 2, y, "RECIBO DE DIÁRIA")

    y -= 40
    c.setFont("Helvetica", 11)

    def linha(label, valor):
        nonlocal y
        c.drawString(2 * cm, y, f"{label}: {valor}")
        y -= 20

    # =========================
    # Dados da Diária
    # =========================
    linha("Diarista", dados["nome"])
    linha("CPF", dados["cpf"])
    linha("Centro de custo", dados["centro"])
    linha("Quantidade de diárias", dados["qtd_diarias"])
    linha("Valor das diárias", f"R$ {dados['vlr_diaria_hora']:.2f}")
    linha("Valor horas extras", f"R$ {dados['vlr_horas_extras']:.2f}")
    linha("Valor total", f"R$ {dados['valor_total']:.2f}")

    # =========================
    # Descrição
    # =========================
    if dados.get("descricao"):
        y -= 10
        c.drawString(2 * cm, y, "Descrição:")
        y -= 15
        text = c.beginText(2.5 * cm, y)
        for linha_desc in dados["descricao"].split("\n"):
            text.textLine(linha_desc)
        c.drawText(text)
        y = text.getY() - 20

    # =========================
    # Assinatura
    # =========================
    y -= 40
    c.line(4 * cm, y, largura - 4 * cm, y)

    c.setFont("Helvetica", 10)
    c.drawCentredString(
        largura / 2,
        y - 15,
        f"{dados['nome']} - CPF: {dados['cpf']}"
    )

    # =========================
    # Rodapé
    # =========================
    c.drawString(
        2 * cm,
        2 * cm,
        f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    c.showPage()
    c.save()

    if abrir:
        abrir_pdf(caminho)

    return caminho
