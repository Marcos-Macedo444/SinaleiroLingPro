"""Testes dos requisitos do trabalho.

Rodam no SQLite sempre e também no Postgres se TEST_DATABASE_URL estiver definida:
    python -m pytest
    TEST_DATABASE_URL=postgresql://... python -m pytest
"""
import os
import re
from datetime import timedelta

import pytest

from helpdesk import create_app
from helpdesk.database import PostgresDatabase, SqliteDatabase
from helpdesk.services import hoje

BANCOS = ["sqlite"] + (["postgres"] if os.environ.get("TEST_DATABASE_URL") else [])


@pytest.fixture(params=BANCOS)
def app(request, tmp_path):
    if request.param == "postgres":
        import psycopg
        url = os.environ["TEST_DATABASE_URL"]
        with psycopg.connect(url, autocommit=True) as con:
            con.execute("DROP TABLE IF EXISTS chamados, setores, usuarios CASCADE")
        db = PostgresDatabase(url)
    else:
        db = SqliteDatabase(tmp_path / "teste.sqlite")
    app = create_app(db=db)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def csrf(client, url="/login"):
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="_csrf" value="([^"]+)"', html).group(1)


def entrar(client, login, senha):
    return client.post("/login", data={"login": login, "senha": senha, "_csrf": csrf(client)})


def sair(client):
    client.post("/logout", data={"_csrf": csrf(client, "/chamados")})


def abrir(client, **extra):
    dados = {"data": (hoje() - timedelta(days=1)).isoformat(), "setor": "Financeiro", "item": "Impressora",
             "descricao": "Papel enroscando", "etiqueta": "pat-001", "_csrf": csrf(client, "/chamados/novo")}
    dados.update(extra)
    return client.post("/chamados/novo", data=dados)


def lista(client, query=""):
    """Só a parte da tabela (ignora avisos no topo da página)."""
    html = client.get("/chamados" + query).get_data(as_text=True)
    return html[html.find("<tbody>"):] if "<tbody>" in html else html[html.find('class="vazio"'):]


def post(client, url, **dados):
    dados["_csrf"] = csrf(client, "/chamados")
    return client.post(url, data=dados, follow_redirects=True)


# ---- login, logout e permissões -------------------------------------------
def test_login_exige_credenciais(client):
    assert client.get("/chamados").status_code == 302
    assert entrar(client, "admin", "errada").status_code == 401
    assert entrar(client, "ADMIN", "admin123").status_code == 302   # login sem diferenciar maiúsculas
    assert client.get("/chamados").status_code == 200


def test_logout_so_por_post(client):
    entrar(client, "usuario", "usuario123")
    assert client.get("/logout").status_code == 405
    sair(client)
    assert client.get("/chamados").status_code == 302


def test_redirecionamento_pos_login_so_interno(client):
    for destino in ("//site-malicioso.com", "/\\site-malicioso.com", "https://site-malicioso.com"):
        r = client.post(f"/login?proximo={destino}",
                        data={"login": "admin", "senha": "admin123", "_csrf": csrf(client)})
        assert r.headers["Location"].endswith("/chamados"), destino
        sair(client)
    r = client.post("/login?proximo=/chamados/novo",
                    data={"login": "admin", "senha": "admin123", "_csrf": csrf(client)})
    assert r.headers["Location"].endswith("/chamados/novo")


def test_banco_comeca_sem_chamados(client):
    """Nada de chamados de exemplo inseridos sozinhos."""
    entrar(client, "admin", "admin123")
    assert 'class="linha ' not in lista(client)


def test_csrf_obrigatorio(client):
    entrar(client, "admin", "admin123")
    assert client.post("/chamados/novo", data={"item": "x"}).status_code == 400


# ---- abertura e relatório --------------------------------------------------
def test_abertura_comeca_em_aberto_e_ordena_por_data(client):
    entrar(client, "usuario", "usuario123")
    abrir(client, data=(hoje() - timedelta(days=9)).isoformat(), item="Monitor antigo")
    abrir(client, data=hoje().isoformat(), item="Notebook novo")
    abrir(client, data=(hoje() - timedelta(days=9)).isoformat(), item="Teclado mesmo dia")
    html = lista(client)
    assert html.index("Notebook novo") < html.index("Teclado mesmo dia") < html.index("Monitor antigo")
    assert "PAT-001" in html and "Em aberto" in html


def test_validacao(client):
    entrar(client, "usuario", "usuario123")
    r = abrir(client, item="", setor="Inexistente", data=(hoje() + timedelta(days=1)).isoformat())
    html = r.get_data(as_text=True)
    assert r.status_code == 422
    assert "Informe qual equipamento" in html and "não pode ser no futuro" in html


def test_usuario_comum_ve_so_os_seus(client):
    entrar(client, "admin", "admin123")
    abrir(client, item="Chamado do admin")
    sair(client)
    entrar(client, "usuario", "usuario123")
    abrir(client, item="Chamado do usuario")
    html = lista(client)
    assert "Chamado do usuario" in html and "Chamado do admin" not in html
    assert 'role="search"' not in html   # busca por data/setor é do administrador


# ---- cancelamento ----------------------------------------------------------
def test_cancelamento_so_quando_aberto(client):
    entrar(client, "usuario", "usuario123")
    abrir(client, item="Roteador")
    sair(client)
    entrar(client, "admin", "admin123")
    post(client, "/chamados/1/status", status="andamento")
    sair(client)
    entrar(client, "usuario", "usuario123")
    r = post(client, "/chamados/1/cancelar")
    assert "não pode mais ser cancelado" in r.get_data(as_text=True)
    assert "Roteador" in lista(client)


def test_admin_cancela_e_chamado_nao_volta(client):
    entrar(client, "usuario", "usuario123")
    abrir(client, item="Scanner")
    abrir(client, item="Mouse")
    sair(client)
    entrar(client, "admin", "admin123")
    r = post(client, "/chamados/1/cancelar")
    assert "cancelado e removido" in r.get_data(as_text=True)
    for _ in range(3):   # recarregar a página não traz o chamado de volta
        html = lista(client)
        assert "Scanner" not in html and "Mouse" in html
    r = post(client, "/chamados/1/cancelar")   # cancelar de novo: já não existe
    assert "não encontrado" in r.get_data(as_text=True)


def test_usuario_nao_cancela_chamado_de_outro(client):
    entrar(client, "admin", "admin123")
    abrir(client, item="Do admin")
    sair(client)
    entrar(client, "usuario", "usuario123")
    r = post(client, "/chamados/1/cancelar")
    assert "só pode cancelar" in r.get_data(as_text=True)
    sair(client)
    entrar(client, "admin", "admin123")
    assert "Do admin" in lista(client)


# ---- status e consulta (administrador) ------------------------------------
def test_usuario_comum_nao_altera_status(client):
    entrar(client, "usuario", "usuario123")
    abrir(client)
    post(client, "/chamados/1/status", status="finalizado")
    assert "Em aberto" in lista(client)


def test_admin_altera_status_e_consulta(client):
    entrar(client, "admin", "admin123")
    d1, d2 = (hoje() - timedelta(days=3)).isoformat(), (hoje() - timedelta(days=2)).isoformat()
    abrir(client, setor="TI", data=d1, item="Roteador")
    abrir(client, setor="Comercial", data=d2, item="Telefone IP")
    post(client, "/chamados/1/status", status="finalizado")
    assert "já está finalizado" in post(client, "/chamados/1/status", status="finalizado").get_data(as_text=True)
    html = lista(client, "?status=finalizado")
    assert "Roteador" in html and "Telefone IP" not in html
    html = lista(client, "?setor=Comercial")
    assert "Telefone IP" in html and "Roteador" not in html
    html = lista(client, f"?data={d1}")
    assert "Roteador" in html and "Telefone IP" not in html


def test_status_aberto_nao_e_escolha_do_admin(client):
    entrar(client, "admin", "admin123")
    abrir(client)
    post(client, "/chamados/1/status", status="andamento")
    r = post(client, "/chamados/1/status", status="aberto")
    assert "Em andamento ou Finalizado" in r.get_data(as_text=True)


def test_carro_so_no_login(client):
    assert "carro.js" in client.get("/login").get_data(as_text=True)
    entrar(client, "admin", "admin123")
    assert "carro.js" not in lista(client)


def test_saude(client):
    r = client.get("/saude")
    assert r.status_code == 200 and r.get_json()["status"] == "ok"
