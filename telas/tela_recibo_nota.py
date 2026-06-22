import os
import shutil
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

from dao.notas_fiscais_dao import NotasFiscaisDAO
from services.recibo_nf_service import ReciboNFService
from utils.constantes import CORES
from utils.auxiliares import resource_path


def _fmt_brl(valor):
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _abrir_arquivo(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o arquivo:\n{e}")


class ReciboNotaDialog:
    """Janela modal: gera o recibo em PDF, permite anexar o recibo assinado
    pelo emitente e marcar a nota como paga."""

    def __init__(self, parent, dao: NotasFiscaisDAO, nota_id, recibos_dir, on_close=None):
        self.dao = dao
        self.nota_id = nota_id
        self.nota = dao.get_nota(nota_id)
        self.recibos_dir = Path(recibos_dir)
        self.on_close = on_close

        self.janela = tk.Toplevel(parent)
        self.janela.title(f"Recibo — NF nº {self.nota['numero']}")
        self.janela.geometry("700x680")
        self.janela.configure(bg=CORES['bg_main'])
        self.janela.resizable(False, False)
        self.janela.grab_set()

        try:
            self.janela.iconbitmap(resource_path("Icones/logo.ico"))
        except Exception:
            pass

        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() - 700) // 2
        y = (self.janela.winfo_screenheight() - 680) // 2
        self.janela.geometry(f"700x680+{x}+{y}")
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)

        self._build()
        self._load_recibos()

    def _build(self):
        container = ttk.Frame(self.janela, padding=20, style="Main.TFrame")
        container.pack(fill="both", expand=True)

        ttk.Label(container, text=f"Recibo — NF nº {self.nota['numero']}",
                  font=('Segoe UI', 15, 'bold'),
                  background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(anchor="w")

        nf_card = ttk.Frame(container, style="Card.TFrame", padding=14)
        nf_card.pack(fill="x", pady=(14, 14))

        infos = [
            ("Emitente", self.nota["emitente"]),
            ("CNPJ/CPF", self.nota.get("cnpj_cpf") or "—"),
            ("Competência", self.nota.get("competencia") or "—"),
            ("Valor", _fmt_brl(self.nota["valor"])),
        ]
        for label, val in infos:
            col = ttk.Frame(nf_card, style="Card.TFrame")
            col.pack(side="left", padx=(0, 22))
            ttk.Label(col, text=label, font=('Segoe UI', 8),
                      background=CORES['bg_card'], foreground=CORES['text_light']).pack(anchor="w")
            ttk.Label(col, text=val, font=('Segoe UI', 11, 'bold'),
                      background=CORES['bg_card'], foreground=CORES['text_dark']).pack(anchor="w")

        gen_card = ttk.Frame(container, style="Card.TFrame", padding=16)
        gen_card.pack(fill="x", pady=(0, 12))

        ttk.Label(gen_card, text="📄 Gerar Recibo para Assinatura",
                  font=('Segoe UI', 11, 'bold'),
                  background=CORES['bg_card'], foreground=CORES['text_dark']).pack(anchor="w")
        ttk.Label(gen_card,
                  text="Gere o PDF do recibo com os dados desta nota fiscal para enviar ao emitente assinar.",
                  font=('Segoe UI', 9),
                  background=CORES['bg_card'], foreground=CORES['text_light']).pack(anchor="w", pady=(2, 10))

        row_gen = ttk.Frame(gen_card, style="Card.TFrame")
        row_gen.pack(fill="x")
        ttk.Button(row_gen, text="📄 Gerar PDF do Recibo", style="Primary.TButton",
                   command=self._gerar_recibo).pack(side="left", padx=(0, 10))
        self.status_label = ttk.Label(row_gen, text="", background=CORES['bg_card'],
                                      foreground=CORES['success'])
        self.status_label.pack(side="left")

        att_card = ttk.Frame(container, style="Card.TFrame", padding=16)
        att_card.pack(fill="x", pady=(0, 12))

        ttk.Label(att_card, text="📎 Anexar Recibo Assinado",
                  font=('Segoe UI', 11, 'bold'),
                  background=CORES['bg_card'], foreground=CORES['text_dark']).pack(anchor="w")
        ttk.Label(att_card,
                  text="Após receber o recibo assinado pelo emitente, anexe o arquivo aqui.",
                  font=('Segoe UI', 9),
                  background=CORES['bg_card'], foreground=CORES['text_light']).pack(anchor="w", pady=(2, 10))

        row_att = ttk.Frame(att_card, style="Card.TFrame")
        row_att.pack(fill="x")
        ttk.Button(row_att, text="📎 Selecionar Arquivo", style="Add.TButton",
                   command=self._anexar_recibo).pack(side="left", padx=(0, 10))
        self.attach_status = ttk.Label(row_att, text="", background=CORES['bg_card'],
                                       foreground=CORES['success'])
        self.attach_status.pack(side="left")

        pago_card = ttk.Frame(container, style="Card.TFrame", padding=16)
        pago_card.pack(fill="x", pady=(0, 12))

        pago_left = ttk.Frame(pago_card, style="Card.TFrame")
        pago_left.pack(side="left", fill="x", expand=True)
        ttk.Label(pago_left, text="✅ Registrar Pagamento",
                  font=('Segoe UI', 11, 'bold'),
                  background=CORES['bg_card'], foreground=CORES['text_dark']).pack(anchor="w")
        ttk.Label(pago_left, text="Confirme o pagamento desta nota fiscal para atualizar o status.",
                  font=('Segoe UI', 9),
                  background=CORES['bg_card'], foreground=CORES['text_light']).pack(anchor="w")

        ttk.Button(pago_card, text="✅ Marcar como Pago", style="Add.TButton",
                   command=self._marcar_pago).pack(side="right")

        ttk.Label(container, text="Recibos Assinados Anexados",
                  font=('Segoe UI', 11, 'bold'),
                  background=CORES['bg_main'], foreground=CORES['text_dark']).pack(anchor="w", pady=(4, 8))

        list_outer = ttk.Frame(container, style="Card.TFrame")
        list_outer.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(list_outer, bg=CORES['bg_card'], highlightthickness=0, height=160)
        scrollbar = ttk.Scrollbar(list_outer, orient="vertical", command=self.canvas.yview)
        self.recibos_frame = ttk.Frame(self.canvas, style="Card.TFrame")

        self.recibos_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.recibos_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _load_recibos(self):
        for w in self.recibos_frame.winfo_children():
            w.destroy()

        recibos = self.dao.listar_recibos(self.nota_id)
        if not recibos:
            ttk.Label(self.recibos_frame, text="Nenhum recibo assinado anexado ainda.",
                      font=('Segoe UI', 9),
                      background=CORES['bg_card'], foreground=CORES['text_light']).pack(pady=20)
            return

        for r in recibos:
            row = ttk.Frame(self.recibos_frame, style="Card.TFrame",
                            relief="solid", borderwidth=1)
            row.pack(fill="x", pady=3, padx=2)

            inner = ttk.Frame(row, style="Card.TFrame")
            inner.pack(fill="x", padx=10, pady=6)

            info = ttk.Frame(inner, style="Card.TFrame")
            info.pack(side="left", fill="x", expand=True)

            ttk.Label(info, text="📎 " + r["nome_arquivo"],
                      font=('Segoe UI', 9, 'bold'),
                      background=CORES['bg_card'], foreground=CORES['text_dark']).pack(anchor="w")

            try:
                dt = datetime.strptime(r["criado_em"], "%Y-%m-%d %H:%M:%S")
                data_fmt = dt.strftime("Anexado em %d/%m/%Y às %H:%M")
            except Exception:
                data_fmt = r["criado_em"]
            ttk.Label(info, text=data_fmt, font=('Segoe UI', 8),
                      background=CORES['bg_card'], foreground=CORES['text_light']).pack(anchor="w")

            arquivo = Path(r["arquivo"])
            if arquivo.exists():
                ttk.Button(inner, text="👁️ Abrir", style="Secondary.TButton",
                          command=lambda p=str(arquivo): _abrir_arquivo(p)).pack(side="right", padx=2)
            else:
                ttk.Label(inner, text="⚠️ Arquivo não encontrado",
                          font=('Segoe UI', 8),
                          background=CORES['bg_card'], foreground=CORES['warning']).pack(side="right", padx=4)

            ttk.Button(inner, text="🗑️", style="Danger.TButton",
                      command=lambda rid=r["id"]: self._excluir_recibo(rid)).pack(side="right", padx=2)

    def _gerar_recibo(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = f"recibo_NF{self.nota['numero']}_{ts}.pdf"
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=nome,
            title="Salvar recibo como",
            parent=self.janela
        )
        if not path:
            return
        try:
            ReciboNFService.gerar_pdf_recibo(self.nota, path)
            self.status_label.configure(text=f"✅ Salvo: {Path(path).name}")
            if messagebox.askyesno("Recibo gerado", f"Recibo salvo em:\n{path}\n\nDeseja abrir o arquivo?",
                                   parent=self.janela):
                _abrir_arquivo(path)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF:\n{e}", parent=self.janela)

    def _anexar_recibo(self):
        path = filedialog.askopenfilename(
            title="Selecionar Recibo Assinado",
            filetypes=[
                ("Documentos", "*.pdf *.png *.jpg *.jpeg *.tiff *.bmp"),
                ("PDF", "*.pdf"),
                ("Imagens", "*.png *.jpg *.jpeg"),
                ("Todos", "*.*"),
            ],
            parent=self.janela
        )
        if not path:
            return

        src = Path(path)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_dest = f"NF{self.nota['numero']}_{ts}{src.suffix}"
        self.recibos_dir.mkdir(parents=True, exist_ok=True)
        dest = self.recibos_dir / nome_dest

        try:
            shutil.copy2(src, dest)
            self.dao.inserir_recibo(self.nota_id, str(dest), src.name)
            self.attach_status.configure(text=f"✅ Anexado: {src.name}")
            self._load_recibos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao anexar arquivo:\n{e}", parent=self.janela)

    def _marcar_pago(self):
        if self.nota.get("pago"):
            messagebox.showinfo("Aviso", "Esta nota já está marcada como paga.", parent=self.janela)
            return
        if messagebox.askyesno("Confirmar", f"Marcar a NF nº {self.nota['numero']} como PAGA?",
                               parent=self.janela):
            self.dao.marcar_pago(self.nota_id)
            messagebox.showinfo("Sucesso", "Nota marcada como paga!", parent=self.janela)
            self._fechar()

    def _excluir_recibo(self, recibo_id):
        if messagebox.askyesno("Confirmar",
                               "Remover este recibo do sistema?\n(O arquivo na pasta será mantido)",
                               parent=self.janela):
            self.dao.excluir_recibo(recibo_id)
            self._load_recibos()

    def _fechar(self):
        self.janela.destroy()
        if self.on_close:
            self.on_close()
