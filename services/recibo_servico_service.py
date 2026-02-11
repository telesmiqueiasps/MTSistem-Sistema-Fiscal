import tempfile
import os
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from dao.empresa_dao import EmpresaDAO
from utils.auxiliares import resource_path

def formatar_data_br(data):
    if not data:
        return None

    if isinstance(data, (datetime, date)):
        return data.strftime("%d-%m-%Y")

    return datetime.strptime(data, "%Y-%m-%d").strftime("%d-%m-%Y")

def abrir_pdf(caminho):
    """Abre o PDF no visualizador padrão"""
    try:
        os.startfile(caminho)
    except AttributeError:
        # Linux/Mac
        import subprocess
        subprocess.call(["xdg-open", caminho])

class ReciboServicoService:
    
    @staticmethod
    def gerar_recibo_temporario(servico_dados) -> str:
        
        # Cria arquivo temporário
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        caminho = tmp.name
        tmp.close()
        
        # Busca dados da empresa
        try:
            empresa = EmpresaDAO().buscar_empresa()
        except:
            empresa = None
        
        # Cria o PDF
        c = canvas.Canvas(caminho, pagesize=A4)
        largura, altura = A4
        
        y_topo = altura - 80
        
        # =========================
        # Logo (se existir)
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
        data_servico_formatada = formatar_data_br(servico_dados[1])
        y = y_topo - 120
        
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(largura / 2, y, "RECIBO DE SERVIÇO PRESTADO")
        
        y -= 25
        c.setFont("Helvetica", 10)
        c.drawCentredString(
            largura / 2,
            y,
            f"Recibo Nº {servico_dados[0]:06d} - Data do Serviço: {data_servico_formatada}"
        )
        
        # =========================
        # Total do Serviço
        # =========================
        valor_formatado = f"R$ {servico_dados[5]:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        y -= 40
        c.setFont("Helvetica-Bold", 13)
        c.drawRightString(
            largura - 3 * cm,
            y,
            f"Total do Serviço: {valor_formatado}"
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
        Recebi de <b>{empresa['razao_social']}</b>, a importância total de
        <b> {valor_formatado}</b>, referente ao pagamento do serviço abaixo descrito,
        onde ASSINO e CONFIRMO como verdadeiras as informações aqui prestadas, comprometendo-me a não
        reclamar nenhum outro valor a respeito do mesmo, no qual dou plena,
        geral e irrevogável quitação do pagamento aqui relacionado.
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

        # Descrição (pode ser longa, usar Paragraph)
        y -= 15
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2.5 * cm, y, "DESCRIÇÃO DO SERVIÇO PRESTADO:")
        
        y -= 5
        styles = getSampleStyleSheet()
        style_desc = ParagraphStyle(
            "Descricao",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14
        )
        
        frame_desc = Frame(
            2.5 * cm,
            y - 3 * cm,
            largura - 5 * cm,
            3 * cm,
            showBoundary=0
        )
        
        desc_para = Paragraph(servico_dados[6], style_desc)
        frame_desc.addFromList([desc_para], c)
        
        y -= 3.5 * cm
        
    
        
        
        
        # =========================
        # Assinatura
        # =========================
    
        # Linha de assinatura
        c.line(4 * cm, y, largura - 4 * cm, y)
        
        y -= 15
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(largura / 2, y, servico_dados[2])
        
        y -= 14
        c.setFont("Helvetica", 9)
        c.drawCentredString(largura / 2, y, f"CPF: {servico_dados[3]}")
        
        # =========================
        # Rodapé
        # =========================
        c.setFont("Helvetica", 8)
        rodape_texto = f"Documento gerado e assinado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        if empresa:
            rodape_texto += f" - {empresa['cidade']}/{empresa['uf']}"
        
        c.drawCentredString(largura / 2, 2 * cm, rodape_texto)
        
        # Finaliza
        c.save()
        
        # Abre automaticamente
        abrir_pdf(caminho)
        
        return caminho
    
    @staticmethod
    def _numero_por_extenso(valor: float) -> str:
        """Converte número para extenso simplificado"""
        partes = f"{valor:.2f}".split('.')
        reais = int(partes[0])
        centavos = int(partes[1]) if len(partes) > 1 else 0
        
        if centavos > 0:
            return f"{reais} reais e {centavos:02d} centavos"
        else:
            return f"{reais} reais"