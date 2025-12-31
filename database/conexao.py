import os
import sqlite3

#DB_DIR = r"T:\MTSistem\db"
DB_DIR = r"C:\Users\Mateus\Documents\Miquéias\MTSistem-Sistema-Fiscal\db"

DB_PATH = os.path.join(DB_DIR, "sistemafiscal.db")


def garantir_banco():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    return conn