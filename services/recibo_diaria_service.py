import tempfile
import os
import sys
import subprocess
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from tkinter import filedialog

def abrir_pdf(caminho):
    if not os.path.exists(caminho):
        return

    try:
        if sys.platform.startswith("win"):
            os.startfile(caminho)  # Windows
        elif sys.platform.startswith("darwin"):
            subprocess.call(["open", caminho])  # macOS
        else:
            subprocess.call(["xdg-open", caminho])  # Linux
    except Exception as e:
        print(f"Erro ao abrir PDF: {e}")

def gerar_pdf_recibo_diaria(dados, salvar=False, abrir=True):
    # =========================
    # Definir caminho do arquivo
    # =========================
    if salvar:
        caminho = filedialog.asksaveasfilename(
            title="Salvar recibo de diária",
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialfile=f"recibo_diaria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        if not caminho:  # usuário cancelou
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

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, altura - 60, "RECIBO DE DIÁRIA")

    c.setFont("Helvetica", 11)
    y = altura - 120

    def linha(label, valor):
        nonlocal y
        c.drawString(50, y, f"{label}: {valor}")
        y -= 22

    linha("Diarista", dados["nome"])
    linha("CPF", dados["cpf"])
    linha("Centro de custo", dados["centro"])
    linha("Quantidade de diárias", dados["qtd_diarias"])
    linha("Valor diárias", f"R$ {dados['vlr_diaria_hora']:.2f}")
    linha("Valor horas extras", f"R$ {dados['vlr_horas_extras']:.2f}")
    linha("Valor total", f"R$ {dados['valor_total']:.2f}")

    if dados.get("descricao"):
        y -= 10
        c.drawString(50, y, "Descrição:")
        y -= 18
        text = c.beginText(70, y)
        for l in dados["descricao"].split("\n"):
            text.textLine(l)
        c.drawText(text)

    c.drawString(
        50,
        100,
        f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    c.showPage()
    c.save()

    # =========================
    # Abrir PDF
    # =========================
    if abrir:
        abrir_pdf(caminho)

    return caminho
