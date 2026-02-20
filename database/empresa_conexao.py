import sqlite3
import os

_conn_empresa = None

def conectar_empresa(db_path):
    global _conn_empresa

    if _conn_empresa:
        _conn_empresa.close()

    _conn_empresa = sqlite3.connect(db_path)

def get_conn_empresa():
    return _conn_empresa

