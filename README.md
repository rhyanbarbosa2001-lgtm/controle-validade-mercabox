# Controle de Validade — Mercabox Araújo

Projeto acadêmico desenvolvido para apoiar o controle de validade de produtos no contexto do supermercado Mercabox Araújo, em Minaçu–GO.

O sistema permite cadastrar produtos e lotes, consultar suas datas de validade e identificar os que precisam de atenção.

## Funcionalidades

- Cadastro de produtos com nome e código interno único.
- Registro de lotes com produto, quantidade, localização e validade.
- Listagem dos lotes pela validade mais próxima.
- Identificação de lotes vencidos, com vencimento hoje ou nos próximos 30 dias.
- Destaques em cores acompanhados de textos explicativos.
- Validação dos dados e proteção dos formulários com token CSRF.

## Tecnologias

- Python
- Flask
- SQLite
- HTML e CSS
- pytest e pytest-cov

## Como executar no Windows

É necessário ter o Python instalado.

No terminal, dentro da pasta do projeto, execute:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Abra no navegador:

http://127.0.0.1:5000

O banco de dados é criado automaticamente na primeira execução. Os produtos e lotes devem ser cadastrados pela interface.

Para encerrar o servidor, pressione Ctrl + C no terminal.

## Páginas

- `/produtos`: cadastro de produtos.
- `/lotes`: registro de lotes.
- `/vencimentos`: consulta das validades.

## Testes automatizados

Com o ambiente virtual ativado, execute:

```bat
python -m pytest -v --cov=app --cov=banco --cov-report=term-missing
```

Os testes de integração verificam a abertura das páginas, o cadastro de produtos, a rejeição de códigos duplicados, campos obrigatórios, proteção CSRF e situações de validade dos lotes.

Na execução registrada durante o desenvolvimento, os 13 testes passaram, com cobertura total de linhas de 87%.

## Organização do projeto

- `app.py`: aplicação Flask, rotas e regras de validação.
- `banco.py`: conexão com SQLite e criação das tabelas.
- `templates/`: páginas HTML.
- `test_sistema.py`: testes automatizados.
- `requirements.txt`: dependências do projeto.
- `.gitignore`: arquivos que não devem ser versionados.

## Limitações atuais

Esta versão é um MVP para demonstração e avaliação acadêmica. Ainda não possui autenticação de usuários, edição ou exclusão pela interface e exportação de relatórios.

O servidor iniciado com `python app.py` é destinado ao desenvolvimento local.

## Autor

Rhyan Paula Barbosa — estudante de Ciência da Computação.