import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from dao.notas_fiscais_dao import NotasFiscaisDAO
from services.nfse_importer import importar_nfse_xml, formatar_data_br, NFSeImportError
from utils.constantes import CORES
from utils.auxiliares import resource_path


def _fmt_brl(v):
    if v is None:
        return "—"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


_STATUS_INFO = {
    "pronta": ("success", "✅ Pronta para importar"),
    "duplicada": ("warning", "⚠️ Já cadastrada"),
    "incompleta": ("warning", "⚠️ Dados incompletos"),
    "erro": ("danger", "❌ Erro ao ler o arquivo"),
}


class ImportacaoLoteNFDialog:
    """Janela modal para importar várias NFS-e (XML) de uma só vez."""

    def __init__(self, parent, dao: NotasFiscaisDAO, on_concluido=None):
        self.dao = dao
        self.on_concluido = on_concluido
        self._itens = []

        self.janela = tk.Toplevel(parent)
        self.janela.title("Importação em Lote de NFS-e (XML)")
        self.janela.geometry("980x600")
        self.janela.minsize(820, 480)
        self.janela.configure(bg=CORES['bg_main'])
        self.janela.grab_set()

        try:
            self.janela.iconbitmap(resource_path("Icones/logo.ico"))
        except Exception:
            pass

        self._build()

    def _build(self):
        container = ttk.Frame(self.janela, padding=20, style="Main.TFrame")
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Importação em Lote",
                  font=('Segoe UI', 14, 'bold'),
                  background=CORES['bg_main'], foreground=CORES['text_dark']).pack(anchor="w")
        ttk.Label(container,
                  text="Selecione um ou mais arquivos XML de NFS-e — os dados são lidos "
                       "diretamente das tags (mais confiável que o OCR do PDF).",
                  font=('Segoe UI', 9),
                  background=CORES['bg_main'], foreground=CORES['text_light']
                  ).pack(anchor="w", pady=(2, 14))

        top = ttk.Frame(container, style="Main.TFrame")
        top.pack(fill="x", pady=(0, 10))

        ttk.Button(top, text="📂 Selecionar XML(s)", style="Primary.TButton",
                   command=self._selecionar_arquivos).pack(side="left")

        self.resumo_label = ttk.Label(top, text="Nenhum arquivo selecionado.",
                                      background=CORES['bg_main'], foreground=CORES['text_light'])
        self.resumo_label.pack(side="left", padx=16)

        list_card = ttk.Frame(container, style="Card.TFrame", padding=10)
        list_card.pack(fill="both", expand=True, pady=(0, 12))

        header = ttk.Frame(list_card, style="Card.TFrame")
        header.pack(fill="x", pady=(0, 4))
        for label, width in [
            ("Arquivo", 22), ("Número", 10), ("Emitente", 26),
            ("Valor", 14), ("Emissão", 12), ("Situação", 38)
        ]:
            ttk.Label(header, text=label, width=width, anchor="w",
                      font=('Segoe UI', 9, 'bold'),
                      background=CORES['bg_card'], foreground=CORES['text_light']).pack(side="left")

        canvas = tk.Canvas(list_card, bg=CORES['bg_dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_card, orient="vertical", command=canvas.yview)
        self.lista_frame = ttk.Frame(canvas, style="Card.TFrame")

        self.lista_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.lista_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btns = ttk.Frame(container, style="Main.TFrame")
        btns.pack(fill="x")

        self.btn_importar = ttk.Button(btns, text="✅ Importar válidas", style="Add.TButton",
                                       command=self._importar_validas, state="disabled")
        self.btn_importar.pack(side="left")

        ttk.Button(btns, text="Fechar", style="Secondary.TButton",
                   command=self.janela.destroy).pack(side="left", padx=8)

    def _selecionar_arquivos(self):
        paths = filedialog.askopenfilenames(
            title="Selecionar XML(s) de NFS-e",
            filetypes=[("XML", "*.xml"), ("Todos", "*.*")],
            parent=self.janela
        )
        if not paths:
            return
        self._analisar_arquivos(paths)

    def _analisar_arquivos(self, paths):
        self._itens = []
        for path in paths:
            item = {"path": path, "dados": None, "status": "erro", "motivo": ""}
            try:
                dados = importar_nfse_xml(path)
            except NFSeImportError as e:
                item["motivo"] = str(e)
                self._itens.append(item)
                continue
            except Exception as e:
                item["motivo"] = f"Erro inesperado: {e}"
                self._itens.append(item)
                continue

            item["dados"] = dados
            if dados["_problemas"]:
                item["status"] = "incompleta"
                item["motivo"] = "; ".join(dados["_problemas"])
            else:
                dup = self.dao.buscar_nota_duplicada(
                    dados["numero"], dados["emitente"], dados.get("_chave_acesso")
                )
                if dup:
                    item["status"] = "duplicada"
                    item["motivo"] = f"Já existe NF nº {dup['numero']} de {dup['emitente']}"
                else:
                    item["status"] = "pronta"
            self._itens.append(item)

        self._renderizar_itens()

    def _renderizar_itens(self):
        for w in self.lista_frame.winfo_children():
            w.destroy()

        for item in self._itens:
            row = ttk.Frame(self.lista_frame, style="Card.TFrame",
                            relief="solid", borderwidth=1)
            row.pack(fill="x", pady=2)

            dados = item["dados"] or {}
            cor_key, texto_status = _STATUS_INFO[item["status"]]
            cor = CORES[cor_key]

            nome_arquivo = Path(item["path"]).name
            if len(nome_arquivo) > 24:
                nome_arquivo = nome_arquivo[:22] + "…"

            ttk.Label(row, text=nome_arquivo, width=22, anchor="w",
                      font=('Segoe UI', 9),
                      background=CORES['bg_card'], foreground=CORES['text_dark']).pack(side="left", padx=4, pady=6)

            ttk.Label(row, text=dados.get("numero") or "—", width=10, anchor="w",
                      font=('Segoe UI', 9),
                      background=CORES['bg_card'], foreground=CORES['text_dark']).pack(side="left")

            emitente = dados.get("emitente") or "—"
            if len(emitente) > 28:
                emitente = emitente[:26] + "…"
            ttk.Label(row, text=emitente, width=26, anchor="w",
                      font=('Segoe UI', 9),
                      background=CORES['bg_card'], foreground=CORES['text_dark']).pack(side="left")

            ttk.Label(row, text=_fmt_brl(dados.get("valor")), width=14, anchor="w",
                      font=('Segoe UI', 9, 'bold'),
                      background=CORES['bg_card'], foreground=CORES['text_dark']).pack(side="left")

            ttk.Label(row, text=formatar_data_br(dados.get("data_emissao", "")) or "—",
                      width=12, anchor="w", font=('Segoe UI', 9),
                      background=CORES['bg_card'], foreground=CORES['text_light']).pack(side="left")

            status_frame = ttk.Frame(row, style="Card.TFrame")
            status_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))
            ttk.Label(status_frame, text=texto_status, anchor="w",
                      font=('Segoe UI', 9, 'bold'),
                      background=CORES['bg_card'], foreground=cor).pack(anchor="w")
            if item["motivo"] and item["status"] != "pronta":
                ttk.Label(status_frame, text=item["motivo"], anchor="w",
                          font=('Segoe UI', 8), wraplength=280, justify="left",
                          background=CORES['bg_card'], foreground=CORES['text_light']).pack(anchor="w")

        prontas = sum(1 for i in self._itens if i["status"] == "pronta")
        total = len(self._itens)
        if total:
            self.resumo_label.configure(
                text=f"{total} arquivo(s) selecionado(s) — {prontas} pronto(s) para importar."
            )
        self.btn_importar.configure(state="normal" if prontas else "disabled")

    def _importar_validas(self):
        prontos = [i for i in self._itens if i["status"] == "pronta"]
        if not prontos:
            return

        importadas = 0
        for item in prontos:
            dados = item["dados"]
            self.dao.upsert_fornecedor_auto(dados["emitente"], dados["cnpj_cpf"])
            self.dao.inserir_nota({
                "numero": dados["numero"],
                "emitente": dados["emitente"],
                "cnpj_cpf": dados["cnpj_cpf"],
                "descricao_servico": dados["descricao_servico"],
                "valor": dados["valor"],
                "data_emissao": dados["data_emissao"],
                "competencia": dados["competencia"],
                "chave_acesso": dados.get("_chave_acesso") or "",
            })
            importadas += 1

        messagebox.showinfo(
            "Importação concluída",
            f"{importadas} nota(s) fiscal(is) importada(s) com sucesso!",
            parent=self.janela
        )
        if self.on_concluido:
            self.on_concluido()
        self.janela.destroy()
