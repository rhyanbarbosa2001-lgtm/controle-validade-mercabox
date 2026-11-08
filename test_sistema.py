import importlib
from datetime import date, timedelta

import pytest

import banco


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(
        banco, "CAMINHO_BANCO", tmp_path / "teste.db"
    )
    banco.criar_tabelas()

    modulo = importlib.import_module("app")
    monkeypatch.setitem(modulo.app.config, "TESTING", True)
    monkeypatch.setitem(
        modulo.app.config, "SECRET_KEY", "chave-apenas-para-testes"
    )

    with modulo.app.test_client() as cliente:
        yield cliente


def enviar(cliente, caminho, dados):
    cliente.get(caminho)

    with cliente.session_transaction() as sessao:
        token = sessao["csrf_token"]

    return cliente.post(
        caminho,
        data={**dados, "csrf_token": token},
        follow_redirects=True
    )


def cadastrar_produto(cliente):
    enviar(cliente, "/produtos", {
        "nome": "Leite de teste",
        "codigo_interno": "TESTE001"
    })


def test_inicio_redireciona(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/produtos")


@pytest.mark.parametrize(
    "pagina", ["/produtos", "/lotes", "/vencimentos"]
)
def test_paginas_abrem(cliente, pagina):
    assert cliente.get(pagina).status_code == 200


def test_cadastra_produto(cliente):
    cadastrar_produto(cliente)
    conexao = banco.conectar()

    try:
        produto = conexao.execute(
            "SELECT * FROM produtos"
        ).fetchone()

        assert produto["nome"] == "Leite de teste"
        assert produto["codigo_interno"] == "TESTE001"
    finally:
        conexao.close()


def test_rejeita_codigo_duplicado(cliente):
    cadastrar_produto(cliente)

    resposta = enviar(cliente, "/produtos", {
        "nome": "Outro produto",
        "codigo_interno": "TESTE001"
    })

    assert "já está cadastrado" in resposta.get_data(as_text=True)

    conexao = banco.conectar()
    try:
        total = conexao.execute(
            "SELECT COUNT(*) FROM produtos"
        ).fetchone()[0]

        assert total == 1
    finally:
        conexao.close()


def test_rejeita_produto_sem_nome(cliente):
    resposta = enviar(cliente, "/produtos", {
        "nome": " ",
        "codigo_interno": "TESTE002"
    })

    assert "Preencha o nome" in resposta.get_data(as_text=True)

    conexao = banco.conectar()
    try:
        assert conexao.execute(
            "SELECT COUNT(*) FROM produtos"
        ).fetchone()[0] == 0
    finally:
        conexao.close()


def test_bloqueia_envio_sem_token(cliente):
    resposta = cliente.post("/produtos", data={
        "nome": "Produto",
        "codigo_interno": "SEM-TOKEN"
    })

    assert resposta.status_code == 403


@pytest.mark.parametrize("dias", [-1, 0, 7, 30, 31])
def test_lote_e_situacao_da_validade(cliente, dias):
    cadastrar_produto(cliente)
    validade = date.today() + timedelta(days=dias)

    resposta = enviar(cliente, "/lotes", {
        "produto_id": "1",
        "codigo_lote": "LOTE-TESTE",
        "quantidade": "12",
        "localizacao": "Prateleira de teste",
        "data_validade": validade.isoformat()
    })

    assert "Lote cadastrado com sucesso" in resposta.get_data(
        as_text=True
    )

    pagina = cliente.get("/vencimentos").get_data(as_text=True)

    assert "LOTE-TESTE" in pagina
    assert validade.strftime("%d/%m/%Y") in pagina

    if dias < 0:
        assert "Vencido" in pagina
    elif dias == 0:
        assert "Vence hoje" in pagina
    elif dias <= 30:
        assert f"Vence em {dias} dia(s)" in pagina
    else:
        assert "Validade acima de 30 dias" in pagina