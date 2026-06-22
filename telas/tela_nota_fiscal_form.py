import shutil
import sys
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import ttk, messagebox, filedialog

from dao.notas_fiscais_dao import NotasFiscaisDAO
from services.nfse_importer import (importar_nfse, importar_nfse_xml,
                                     formatar_data_br, tesseract_disponivel,
                                     NFSeImportError)
from utils.constantes import CORES
from utils.auxiliares import resource_path


class NotaFiscalFormDialog:
    """Janela modal para criar/editar uma nota fiscal, com importação de
    NFS-e via XML (recomendado) ou PDF (OCR)."""

    def __init__(self, parent, dao: NotasFiscaisDAO, nota_id=None, on_save=None):
        self.dao = dao
        self.nota_id = nota_id
        self.on_save = on_save
        self.nota = dao.get_nota(nota_id) if nota_id else None
        self._chave_acesso_importada = None
        self.fields = {}

        self.janela = tk.Toplevel(parent)
        titulo = "Editar Nota Fiscal" if nota_id else "Nova Nota Fiscal"
        self.janela.title(titulo)
        self.janela.geometry("760x780")
        self.janela.configure(bg=CORES['bg_main'])
        self.janela.resizable(False, False)
        self.janela.grab_set()

        try:
            self.janela.iconbitmap(resource_path("Icones/logo.ico"))
        except Exception:
            pass

        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() - 760) // 2
        y = (self.janela.winfo_screenheight() - 780) // 2
        self.janela.geometry(f"760x780+{x}+{y}")

        self._build()
        if self.nota:
            self._populate()

    # ─────────────────────────────────────────────────────────────────────────
    # INTERFACE
    # ─────────────────────────────────────────────────────────────────────────

    def _build(self):
        outer = ttk.Frame(self.janela, style="Main.TFrame")
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=CORES['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        container = ttk.Frame(canvas, style="Main.TFrame", padding=22)

        container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=container, anchor="nw", width=740)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        outer.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        outer.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        titulo = "Editar Nota Fiscal" if self.nota_id else "Nova Nota Fiscal"
        ttk.Label(container, text=titulo,
                  font=('Segoe UI', 16, 'bold'),
                  background=CORES['bg_main'],
                  foreground=CORES['text_dark']).pack(anchor="w")

        self.chave_frame = ttk.Frame(container, style="Main.TFrame")
        self.chave_frame.pack(anchor="w", pady=(6, 0))
        self._render_chave_acesso()

        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=16)

        self._build_import_card(container)

        form = ttk.Frame(container, style="Card.TFrame", padding=18)
        form.pack(fill="x", pady=(0, 16))

        col_esq = ttk.Frame(form, style="Card.TFrame")
        col_esq.pack(side="left", fill="both", expand=True, padx=(0, 14))
        col_dir = ttk.Frame(form, style="Card.TFrame")
        col_dir.pack(side="right", fill="both", expand=True)

        self._campo(col_esq, "numero", "Número da NF *")
        self._campo(col_esq, "emitente", "Emitente *")
        self._campo(col_esq, "cnpj_cpf", "CNPJ / CPF")
        self._campo(col_esq, "descricao_servico", "Descrição do Serviço", multiline=True, height=4)

        self._campo(col_dir, "valor", "Valor (R$) *", placeholder="0,00")
        self._campo(col_dir, "data_emissao", "Data de Emissão * (DD/MM/AAAA)")
        self._campo(col_dir, "competencia", "Competência * (MM/AAAA)")
        self._campo(col_dir, "data_vencimento", "Data de Vencimento (DD/MM/AAAA)")

        self._campo(form, "observacoes", "Observações", multiline=True, height=3, full=True)

        pag_card = ttk.Frame(container, style="Card.TFrame", padding=16)
        pag_card.pack(fill="x", pady=(0, 16))

        ttk.Label(pag_card, text="Status de Pagamento",
                  font=('Segoe UI', 11, 'bold'),
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(anchor="w", pady=(0, 10))

        row_pago = ttk.Frame(pag_card, style="Card.TFrame")
        row_pago.pack(fill="x")

        self.pago_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row_pago, text="Nota fiscal já foi paga",
                        variable=self.pago_var, style="Custom.TCheckbutton",
                        command=self._toggle_pago).pack(side="left")

        self.dp_frame = ttk.Frame(row_pago, style="Card.TFrame")
        ttk.Label(self.dp_frame, text="Data do Pagamento (DD/MM/AAAA):",
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(side="left", padx=(20, 6))
        self.fields["data_pagamento"] = ttk.Entry(self.dp_frame, width=14)
        self.fields["data_pagamento"].pack(side="left")

        btns = ttk.Frame(container, style="Main.TFrame")
        btns.pack(fill="x", pady=(4, 10))

        ttk.Button(btns, text="💾 Salvar Nota Fiscal", style="Primary.TButton",
                   command=self._save).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton",
                   command=self.janela.destroy).pack(side="left")

        self.janela.bind("<Escape>", lambda _e: self.janela.destroy())

    def _build_import_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=16)
        card.pack(fill="x", pady=(0, 16))

        ttk.Label(card, text="📄 Importar NFS-e",
                  font=('Segoe UI', 11, 'bold'),
                  background=CORES['bg_card'],
                  foreground=CORES['text_dark']).pack(anchor="w")
        ttk.Label(card,
                  text="Pelo XML (recomendado — dados lidos direto das tags, sem OCR) "
                       "ou pelo PDF da DANFSe.",
                  font=('Segoe UI', 9),
                  background=CORES['bg_card'],
                  foreground=CORES['text_light']).pack(anchor="w", pady=(2, 10))

        xml_row = ttk.Frame(card, style="Card.TFrame")
        xml_row.pack(fill="x", pady=(0, 8))

        ttk.Button(xml_row, text="📋 Selecionar XML", style="Primary.TButton",
                   command=self._importar_xml).pack(side="left", padx=(0, 10))

        self.import_status = ttk.Label(xml_row, text="",
                                       background=CORES['bg_card'],
                                       foreground=CORES['text_light'])
        self.import_status.pack(side="left")

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=8)

        if tesseract_disponivel():
            ttk.Button(card, text="📂 Selecionar PDF", style="Add.TButton",
                       command=self._importar_pdf).pack(anchor="w")
        else:
            aviso = ttk.Frame(card, style="Card.TFrame", relief="solid", borderwidth=1)
            aviso.pack(fill="x")
            av_inner = ttk.Frame(aviso, style="Card.TFrame", padding=10)
            av_inner.pack(fill="x")

            ttk.Label(av_inner, text="⚠️ Tesseract OCR não encontrado",
                      font=('Segoe UI', 10, 'bold'),
                      background=CORES['bg_card'],
                      foreground=CORES['warning']).pack(anchor="w")

            if sys.platform == "win32":
                instrucoes = (
                    "Para habilitar a importação de NFS-e por PDF, instale o Tesseract OCR:\n"
                    "1. Baixe em: github.com/UB-Mannheim/tesseract/wiki\n"
                    "2. Durante a instalação, selecione o pacote de idioma 'Portuguese'\n"
                    "3. Reinicie o aplicativo após instalar"
                )
            else:
                instrucoes = (
                    "Instale com:\n"
                    "Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-por\n"
                    "Mac: brew install tesseract tesseract-lang"
                )
            ttk.Label(av_inner, text=instrucoes,
                      font=('Segoe UI', 9),
                      background=CORES['bg_card'],
                      foreground=CORES['text_light'],
                      justify="left").pack(anchor="w", pady=(6, 8))

            btn_row = ttk.Frame(av_inner, style="Card.TFrame")
            btn_row.pack(anchor="w")
            if sys.platform == "win32":
                ttk.Button(btn_row, text="🌐 Abrir página de download",
                           style="Secondary.TButton",
                           command=lambda: webbrowser.open(
                               "https://github.com/UB-Mannheim/tesseract/wiki"
                           )).pack(side="left", padx=(0, 8))
            ttk.Button(btn_row, text="📂 Tentar mesmo assim",
                       style="Secondary.TButton",
                       command=self._importar_pdf).pack(side="left")

    # ── LÓGICA DE IMPORTAÇÃO ──────────────────────────────────────────────────

    def _importar_xml(self):
        path = filedialog.askopenfilename(
            title="Selecionar NFS-e em XML",
            filetypes=[("XML", "*.xml"), ("Todos", "*.*")]
        )
        if not path:
            return
        try:
            dados = importar_nfse_xml(path)
        except NFSeImportError as e:
            messagebox.showerror("Erro ao importar XML", str(e), parent=self.janela)
            return
        except Exception as e:
            messagebox.showerror("Erro inesperado", f"Erro ao importar XML:\n\n{e}", parent=self.janela)
            return
        self._aplicar_dados_importados(dados)

    def _importar_pdf(self):
        path = filedialog.askopenfilename(
            title="Selecionar NFS-e em PDF",
            filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")]
        )
        if not path:
            return
        try:
            dados = importar_nfse(path)
        except NFSeImportError as e:
            messagebox.showerror("Erro na importação de NFS-e", str(e), parent=self.janela)
            return
        except Exception as e:
            messagebox.showerror("Erro inesperado", f"Erro ao importar PDF:\n\n{e}", parent=self.janela)
            return
        self._aplicar_dados_importados(dados)

    def _aplicar_dados_importados(self, dados: dict):
        if dados["_problemas"]:
            avisos = "\n• ".join(dados["_problemas"])
            messagebox.showwarning(
                "Importação parcial",
                f"Alguns campos não foram encontrados:\n\n• {avisos}\n\n"
                "Verifique e preencha manualmente os campos faltantes.",
                parent=self.janela
            )

        self._chave_acesso_importada = dados.get("_chave_acesso") or None
        self._render_chave_acesso()

        mapa = {
            "numero": dados.get("numero", ""),
            "emitente": dados.get("emitente", ""),
            "cnpj_cpf": dados.get("cnpj_cpf", ""),
            "descricao_servico": dados.get("descricao_servico", ""),
            "competencia": dados.get("competencia", ""),
            "data_emissao": formatar_data_br(dados.get("data_emissao", "")),
        }
        if dados.get("valor") is not None:
            v = dados["valor"]
            mapa["valor"] = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        for key, val in mapa.items():
            w = self.fields.get(key)
            if not w or not val:
                continue
            if isinstance(w, tk.Text):
                w.delete("1.0", "end")
                w.insert("1.0", val)
            else:
                w.delete(0, "end")
                w.insert(0, val)

        nome_emit = dados.get("emitente", "")
        cnpj_emit = dados.get("cnpj_cpf", "")
        sufixo = ""
        if nome_emit:
            forn_id = self.dao.upsert_fornecedor_auto(nome_emit, cnpj_emit)
            sufixo = " (fornecedor cadastrado)" if forn_id else ""

        self.import_status.configure(
            text=f"✅ Dados importados com sucesso!{sufixo}",
            foreground=CORES['success']
        )

    # ── CHAVE DE ACESSO ────────────────────────────────────────────────────────

    def _render_chave_acesso(self):
        for w in self.chave_frame.winfo_children():
            w.destroy()

        chave = (self.nota.get("chave_acesso") if self.nota else None) \
            or self._chave_acesso_importada
        if not chave:
            return

        ttk.Label(self.chave_frame, text="🔑 Chave de Acesso:",
                  font=('Segoe UI', 9, 'bold'),
                  background=CORES['bg_main'],
                  foreground=CORES['text_light']).pack(side="left", padx=(0, 8))

        entry = ttk.Entry(self.chave_frame, width=46, font=('Consolas', 9))
        entry.pack(side="left", padx=(0, 8))
        entry.insert(0, chave)
        entry.configure(state="readonly")

        ttk.Button(self.chave_frame, text="📋 Copiar", style="Secondary.TButton",
                   command=lambda: self._copiar_chave(chave)).pack(side="left")

    def _copiar_chave(self, chave):
        self.janela.clipboard_clear()
        self.janela.clipboard_append(chave)

    # ── HELPERS DO FORMULÁRIO ─────────────────────────────────────────────────

    def _campo(self, parent, key, label, multiline=False, height=3, full=False, placeholder=""):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(fill="x", pady=(0, 12))
        ttk.Label(frame, text=label,
                  font=('Segoe UI', 9, 'bold'),
                  background=CORES['bg_card'],
                  foreground=CORES['text_light']).pack(anchor="w", pady=(0, 4))
        if multiline:
            widget = tk.Text(frame, height=height, font=('Segoe UI', 10))
        else:
            widget = ttk.Entry(frame)
        widget.pack(fill="x")
        self.fields[key] = widget

    def _toggle_pago(self):
        if self.pago_var.get():
            self.dp_frame.pack(side="left")
        else:
            self.dp_frame.pack_forget()

    def _get_val(self, key):
        w = self.fields.get(key)
        if not w:
            return ""
        if isinstance(w, tk.Text):
            return w.get("1.0", "end").strip()
        return w.get().strip()

    def _set_val(self, key, val):
        w = self.fields.get(key)
        if not w or not val:
            return
        if isinstance(w, tk.Text):
            w.insert("1.0", val)
        else:
            w.insert(0, val)

    def _parse_date(self, s):
        s = s.strip()
        if not s:
            return ""
        for fmt_in in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(s, fmt_in).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return s

    def _parse_valor(self, s):
        s = s.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None

    def _populate(self):
        n = self.nota
        self._set_val("numero", n.get("numero", ""))
        self._set_val("emitente", n.get("emitente", ""))
        self._set_val("cnpj_cpf", n.get("cnpj_cpf", "") or "")
        self._set_val("descricao_servico", n.get("descricao_servico", "") or "")
        self._set_val("valor", str(n.get("valor", "")).replace(".", ","))
        self._set_val("competencia", n.get("competencia", ""))
        self._set_val("observacoes", n.get("observacoes", "") or "")

        for campo in ["data_emissao", "data_vencimento"]:
            raw = n.get(campo) or ""
            if raw:
                try:
                    dt = datetime.strptime(raw, "%Y-%m-%d")
                    self._set_val(campo, dt.strftime("%d/%m/%Y"))
                except ValueError:
                    self._set_val(campo, raw)

        if n.get("pago"):
            self.pago_var.set(True)
            self._toggle_pago()
            raw_dp = n.get("data_pagamento") or ""
            if raw_dp:
                try:
                    dt = datetime.strptime(raw_dp, "%Y-%m-%d")
                    self._set_val("data_pagamento", dt.strftime("%d/%m/%Y"))
                except ValueError:
                    self._set_val("data_pagamento", raw_dp)

    def _save(self):
        numero = self._get_val("numero")
        emitente = self._get_val("emitente")
        valor_str = self._get_val("valor")
        data_emissao_str = self._get_val("data_emissao")
        competencia = self._get_val("competencia")

        if not numero:
            messagebox.showerror("Campo obrigatório", "Informe o número da nota fiscal.", parent=self.janela)
            return
        if not emitente:
            messagebox.showerror("Campo obrigatório", "Informe o emitente.", parent=self.janela)
            return
        valor = self._parse_valor(valor_str)
        if valor is None:
            messagebox.showerror("Valor inválido", "Informe um valor numérico válido.", parent=self.janela)
            return
        data_emissao = self._parse_date(data_emissao_str)
        if not data_emissao:
            messagebox.showerror("Data inválida",
                                 "Informe a data de emissão no formato DD/MM/AAAA.", parent=self.janela)
            return
        if not competencia:
            messagebox.showerror("Campo obrigatório",
                                 "Informe a competência (ex.: 06/2025).", parent=self.janela)
            return

        pago = 1 if self.pago_var.get() else 0
        data_pagamento = self._parse_date(self._get_val("data_pagamento")) if pago else ""

        dados = {
            "numero": numero,
            "emitente": emitente,
            "cnpj_cpf": self._get_val("cnpj_cpf"),
            "descricao_servico": self._get_val("descricao_servico"),
            "valor": valor,
            "data_emissao": data_emissao,
            "competencia": competencia,
            "data_vencimento": self._parse_date(self._get_val("data_vencimento")),
            "pago": pago,
            "data_pagamento": data_pagamento,
            "observacoes": self._get_val("observacoes"),
        }
        if self._chave_acesso_importada:
            dados["chave_acesso"] = self._chave_acesso_importada

        if self.nota_id:
            self.dao.atualizar_nota(self.nota_id, dados)
            messagebox.showinfo("Sucesso", "Nota fiscal atualizada com sucesso!", parent=self.janela)
        else:
            self.dao.inserir_nota(dados)
            messagebox.showinfo("Sucesso", "Nota fiscal cadastrada com sucesso!", parent=self.janela)

        self.dao.upsert_fornecedor_auto(emitente, dados["cnpj_cpf"])

        if self.on_save:
            self.on_save()
        self.janela.destroy()
