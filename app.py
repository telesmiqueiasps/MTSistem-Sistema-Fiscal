import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from database.sessao import sessao
from services.licenca_online_service import verificar_licenca_online
from telas.tela_login import TelaLogin
from utils.constantes import CORES


def abrir_login():
    root = tk.Tk()
    root.withdraw()

    splash = tk.Toplevel(root)
    splash.title("MTSistem")
    splash.geometry("320x110")
    splash.resizable(False, False)
    splash.configure(bg=CORES['bg_main'])
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() - 320) // 2
    y = (splash.winfo_screenheight() - 110) // 2
    splash.geometry(f"320x110+{x}+{y}")

    ttk.Label(
        splash, text="Verificando licença e atualizações...",
        font=('Segoe UI', 10), background=CORES['bg_main'],
        foreground=CORES['text_dark']
    ).pack(expand=True)

    fila = queue.Queue()
    threading.Thread(target=lambda: fila.put(verificar_licenca_online()), daemon=True).start()

    def _aguardar_resultado():
        try:
            info = fila.get_nowait()
        except queue.Empty:
            root.after(150, _aguardar_resultado)
            return

        splash.destroy()

        if info and info["status"] != "ok":
            messagebox.showerror("Acesso bloqueado", info["mensagem_bloqueio"], parent=root)
            root.destroy()
            return

        if info:
            sessao.versao_remota = info.get("versao_atual")
            sessao.exe_url_remoto = info.get("exe_url")
            sessao.mensagem_update_remoto = info.get("mensagem_update")

        root.deiconify()
        TelaLogin(root)

    root.after(150, _aguardar_resultado)
    root.mainloop()


if __name__ == "__main__":
    abrir_login()
