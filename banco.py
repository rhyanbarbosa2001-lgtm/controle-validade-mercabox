import sqlite3
from pathlib import Path

CAMINHO_BANCO = Path(__file__).parent / "estoque.db"


def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    conexao = conectar()

    try:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                codigo_interno TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS lotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                codigo_lote TEXT NOT NULL,
                quantidade INTEGER NOT NULL CHECK (quantidade >= 0),
                localizacao TEXT NOT NULL,
                data_validade TEXT NOT NULL,
                FOREIGN KEY (produto_id) REFERENCES produtos(id),
                UNIQUE (produto_id, codigo_lote, data_validade)
            );
        """)
        conexao.commit()
    finally:
        conexao.close()


if __name__ == "__main__":
    criar_tabelas()
    print("Banco de dados criado com sucesso.")