import os
import secrets
import sqlite3

from flask import (
    Flask, abort, redirect, render_template,
    request, session, url_for
)

from banco import conectar, criar_tabelas

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

criar_tabelas()


@app.route("/")
def inicio():
    return redirect(url_for("produtos"))


@app.route("/produtos", methods=["GET", "POST"])
def produtos():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    mensagem = session.pop("mensagem", "")
    nome = ""
    codigo = ""

    if request.method == "POST":
        token = request.form.get("csrf_token", "")

        if not secrets.compare_digest(
            token.encode(), session["csrf_token"].encode()
        ):
            abort(403)

        nome = request.form.get("nome", "").strip()
        codigo = request.form.get("codigo_interno", "").strip()

        if not nome or not codigo:
            mensagem = "Preencha o nome e o código interno."
        elif len(nome) > 120 or len(codigo) > 40:
            mensagem = "Use até 120 caracteres no nome e 40 no código."
        else:
            conexao = conectar()

            try:
                conexao.execute(
                    "INSERT INTO produtos (nome, codigo_interno) VALUES (?, ?)",
                    (nome, codigo)
                )
                conexao.commit()
            except sqlite3.IntegrityError:
                conexao.rollback()
                mensagem = "Esse código interno já está cadastrado."
            else:
                session["mensagem"] = "Produto cadastrado com sucesso."
                return redirect(url_for("produtos"))
            finally:
                conexao.close()

    conexao = conectar()

    try:
        lista = conexao.execute(
            "SELECT * FROM produtos ORDER BY nome"
        ).fetchall()
    finally:
        conexao.close()

    return render_template(
        "produtos.html",
        produtos=lista,
        mensagem=mensagem,
        nome=nome,
        codigo=codigo,
        csrf_token=session["csrf_token"]
    )

@app.route("/lotes", methods=["GET", "POST"])
def lotes():
    from datetime import date

    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    mensagem = session.pop("mensagem_lote", "")
    dados = {}
    conexao = conectar()

    try:
        if request.method == "POST":
            token = request.form.get("csrf_token", "")

            if not secrets.compare_digest(
                token.encode(), session["csrf_token"].encode()
            ):
                abort(403)

            campos = [
                "produto_id", "codigo_lote", "quantidade",
                "localizacao", "data_validade"
            ]
            dados = {
                campo: request.form.get(campo, "").strip()
                for campo in campos
            }

            try:
                if not all(dados.values()):
                    raise ValueError("Preencha todos os campos.")

                if len(dados["codigo_lote"]) > 60:
                    raise ValueError("Use até 60 caracteres no lote.")

                if len(dados["localizacao"]) > 120:
                    raise ValueError("Use até 120 caracteres na localização.")

                if (
                    not dados["quantidade"].isascii()
                    or not dados["quantidade"].isdigit()
                    or len(dados["quantidade"]) > 10
                ):
                    raise ValueError("Informe uma quantidade inteira positiva ou zero.")

                quantidade = int(dados["quantidade"])

                if quantidade > 2147483647:
                    raise ValueError("A quantidade informada é muito grande.")

                try:
                    validade = date.fromisoformat(dados["data_validade"])
                except ValueError:
                    raise ValueError("Informe uma data de validade válida.")

                produto = conexao.execute(
                    "SELECT id FROM produtos WHERE id = ?",
                    (dados["produto_id"],)
                ).fetchone()

                if produto is None:
                    raise ValueError("Selecione um produto cadastrado.")

                conexao.execute(
                    """
                    INSERT INTO lotes (
                        produto_id, codigo_lote, quantidade,
                        localizacao, data_validade
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        produto["id"], dados["codigo_lote"], quantidade,
                        dados["localizacao"], validade.isoformat()
                    )
                )
                conexao.commit()

            except ValueError as erro:
                mensagem = str(erro)
            except sqlite3.IntegrityError:
                conexao.rollback()
                mensagem = "Esse lote já está cadastrado com essa validade."
            else:
                session["mensagem_lote"] = "Lote cadastrado com sucesso."
                return redirect(url_for("lotes"))

        lista = conexao.execute(
            "SELECT * FROM produtos ORDER BY nome"
        ).fetchall()
    finally:
        conexao.close()

    return render_template(
        "lotes.html",
        produtos=lista,
        dados=dados,
        mensagem=mensagem,
        csrf_token=session["csrf_token"]
    )

@app.route("/vencimentos")
def vencimentos():
    from datetime import date

    hoje = date.today()
    conexao = conectar()

    try:
        registros = conexao.execute("""
            SELECT produtos.nome, lotes.codigo_lote,
                   lotes.quantidade, lotes.localizacao,
                   lotes.data_validade
            FROM lotes
            JOIN produtos ON produtos.id = lotes.produto_id
            ORDER BY lotes.data_validade, produtos.nome, lotes.id
        """).fetchall()
    finally:
        conexao.close()

    lista = []

    for registro in registros:
        lote = dict(registro)
        validade = date.fromisoformat(lote["data_validade"])
        dias = (validade - hoje).days

        if dias < 0:
            lote["situacao"] = "Vencido"
            lote["classe"] = "vencido"
        elif dias == 0:
            lote["situacao"] = "Vence hoje"
            lote["classe"] = "proximo"
        elif dias <= 30:
            lote["situacao"] = f"Vence em {dias} dia(s)"
            lote["classe"] = "proximo"
        else:
            lote["situacao"] = "Validade acima de 30 dias"
            lote["classe"] = ""

        lote["validade_formatada"] = validade.strftime("%d/%m/%Y")
        lista.append(lote)

    return render_template(
        "vencimentos.html",
        lotes=lista,
        hoje=hoje.strftime("%d/%m/%Y")
    )
if __name__ == "__main__":
    app.run()
