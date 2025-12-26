import tkinter as tk
from utils.auxiliares import  verificar_versao_no_startup
from telas.tela_login import TelaLogin
from telas.tela_inicial import SistemaFiscal


def abrir_login():
    root = tk.Tk()
    TelaLogin(root, abrir_sistema)
    root.mainloop()


def abrir_sistema(usuario_id, usuario_nome):
    root = tk.Tk()
    versao_remota = verificar_versao_no_startup()
    SistemaFiscal(
        root,
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        versao_remota=versao_remota,
        voltar_login=abrir_login
    )
    root.mainloop()


if __name__ == "__main__":
    abrir_login()

