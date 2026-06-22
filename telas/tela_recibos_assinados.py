import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox

from dao.notas_fiscais_dao import NotasFiscaisDAO
from utils.constantes import CORES


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


class RecibosAssinadosEmbed:
    """Sub-aba que lista todos os recibos assinados anexados, agrupados por NF."""

    def __init__(self, parent_frame, recibos_dir):
        self.parent_frame = parent_frame
        self.dao = NotasFiscaisDAO()
        self.recibos_dir = Path(recibos_dir)
        self.criar_interface()
        self.carregar()

    def criar_interface(self):
        main_frame = ttk.Frame(self.parent_frame, style='Main.TFrame')
        main_frame.pack(fill="both", expand=True)

        header = ttk.Frame(main_frame, style='Main.TFrame')
        header.pack(fill="x", pady=(0, 4))

        ttk.Label(header, text="Recibos Assinados",
                  font=('Segoe UI', 13, 'bold'),
                  background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(side="left")

        ttk.Button(header, text="📁 Abrir Pasta",
                   style="Secondary.TButton",
                   command=self._abrir_pasta).pack(side="right")

        ttk.Label(main_frame, text=f"Pasta: {self.recibos_dir}",
                  font=('Segoe UI', 8),
                  background=CORES['bg_main'],
                  foreground=CORES['text_light']).pack(anchor="w", pady=(0, 10))

        self.lista_container = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
        self.lista_container.pack(fill="both", expand=True)

        canvas_frame = ttk.Frame(self.lista_container, style="Card.TFrame")
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = ttk_canvas = tk.Canvas(
            canvas_frame, bg=CORES['bg_card'], highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=ttk_canvas.yview)
        self.scroll_frame = ttk.Frame(ttk_canvas, style="Card.TFrame")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: ttk_canvas.configure(scrollregion=ttk_canvas.bbox("all"))
        )
        ttk_canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        ttk_canvas.configure(yscrollcommand=scrollbar.set)

        ttk_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            ttk_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas_frame.bind("<Enter>", lambda e: ttk_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas_frame.bind("<Leave>", lambda e: ttk_canvas.unbind_all("<MouseWheel>"))

    def carregar(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        recibos = self.dao.listar_recibos()
        if not recibos:
            ttk.Label(
                self.scroll_frame,
                text="Nenhum recibo assinado encontrado.\n"
                     "Anexe recibos assinados na aba de Notas Fiscais.",
                font=('Segoe UI', 11),
                background=CORES['bg_card'],
                foreground=CORES['text_light'],
                justify="center"
            ).pack(pady=60)
            return

        notas_map = {}
        for r in recibos:
            nid = r["nota_id"]
            if nid not in notas_map:
                notas_map[nid] = {"nota": r, "recibos": []}
            notas_map[nid]["recibos"].append(r)

        for grupo in notas_map.values():
            self._build_card(grupo)

    def _build_card(self, grupo):
        nota = grupo["nota"]
        card = ttk.Frame(self.scroll_frame, style="Card.TFrame",
                         relief="solid", borderwidth=1)
        card.pack(fill="x", pady=6, padx=2)

        nf_header = ttk.Frame(card, style="Card.TFrame")
        nf_header.pack(fill="x", padx=12, pady=(8, 4))

        ttk.Label(
            nf_header,
            text=f"📋 NF nº {nota['numero']}   |   {nota['emitente']}   |   {_fmt_brl(nota['valor'])}",
            font=('Segoe UI', 10, 'bold'),
            background=CORES['bg_card'],
            foreground=CORES['text_dark']
        ).pack(side="left")

        ttk.Label(
            nf_header, text=f"{len(grupo['recibos'])} recibo(s)",
            font=('Segoe UI', 9),
            background=CORES['bg_card'],
            foreground=CORES['primary']
        ).pack(side="right")

        ttk.Separator(card, orient="horizontal").pack(fill="x", padx=12)

        for r in grupo["recibos"]:
            row = ttk.Frame(card, style="Card.TFrame")
            row.pack(fill="x", padx=12, pady=6)

            arquivo = Path(r["arquivo"])
            existe = arquivo.exists()

            info = ttk.Frame(row, style="Card.TFrame")
            info.pack(side="left", fill="x", expand=True)

            ttk.Label(
                info, text=("📎 " if existe else "⚠️ ") + r["nome_arquivo"],
                font=('Segoe UI', 9, 'bold'),
                background=CORES['bg_card'],
                foreground=CORES['text_dark'] if existe else CORES['warning']
            ).pack(anchor="w")

            try:
                dt = datetime.strptime(r["criado_em"], "%Y-%m-%d %H:%M:%S")
                data_fmt = dt.strftime("Anexado em %d/%m/%Y às %H:%M")
            except Exception:
                data_fmt = r["criado_em"]
            if not existe:
                data_fmt += "  ·  ⚠️ Arquivo não encontrado no disco"

            ttk.Label(
                info, text=data_fmt,
                font=('Segoe UI', 8),
                background=CORES['bg_card'],
                foreground=CORES['text_light']
            ).pack(anchor="w")

            if existe:
                ttk.Button(row, text="👁️ Abrir", style="Secondary.TButton",
                          command=lambda p=str(arquivo): _abrir_arquivo(p)).pack(side="right", padx=2)

            ttk.Button(row, text="🗑️", style="Danger.TButton",
                      command=lambda rid=r["id"]: self._excluir(rid)).pack(side="right", padx=2)

    def _excluir(self, recibo_id):
        if messagebox.askyesno("Confirmar",
                               "Remover este recibo do sistema?\n(O arquivo na pasta será mantido)"):
            self.dao.excluir_recibo(recibo_id)
            self.carregar()

    def _abrir_pasta(self):
        try:
            self.recibos_dir.mkdir(parents=True, exist_ok=True)
            _abrir_arquivo(str(self.recibos_dir))
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")
