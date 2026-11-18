"""Testes dos requisitos do trabalho (rodar com: python -m pytest)."""
import re
from datetime import date

import pytest

from helpdesk import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / "teste.sqlite")
    app.config["TESTING"] = True
    return app.test_client()


def csrf(client, url="/login"):
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="_csrf" value="([^"]+)"', html).group(1)


def entrar(client, login, senha):
    return client.post("/login", data={"login": login, "senha": senha, "_csrf": csrf(client)})


def abrir(client, **extra):
    dados = {"data": "2026-11-10", "setor": "Financeiro", "item": "Impressora",
             "descricao": "Papel enroscando", "etiqueta": "pat-001", "_csrf": csrf(client, "/chamados/novo")}
    dados.update(extra)
    return client.post("/chamados/novo", data=dados)


def test_login_exige_credenciais(client):
    assert client.get("/chamados").status_code == 302
    assert entrar(client, "admin", "errada").status_code == 401
    assert entrar(client, "admin", "admin123").status_code == 302
    assert client.get("/chamados").status_code == 200


def test_logout(client):
    entrar(client, "usuario", "usuario123")
    client.post("/logout", data={"_csrf": csrf(client, "/chamados")})
    assert client.get("/chamados").status_code == 302


def test_abertura_comeca_em_aberto_e_ordena_por_data(client):
    entrar(client, "usuario", "usuario123")
    abrir(client, data="2026-11-01", item="Monitor antigo")
    abrir(client, data="2026-11-15", item="Notebook novo")
    html = client.get("/chamados").get_data(as_text=True)
    assert html.index("Notebook novo") < html.index("Monitor antigo")
    assert "PAT-001" in html and "Em aberto" in html


def test_validacao(client):
    entrar(client, "usuario", "usuario123")
    r = abrir(client, item="", setor="Inexistente")
    assert r.status_code == 422
    assert "Informe qual equipamento" in r.get_data(as_text=True)


def test_cancelamento_so_quando_aberto(client):
    entrar(client, "usuario", "usuario123")
    abrir(client)
    client.post("/logout", data={"_csrf": csrf(client, "/chamados")})
    entrar(client, "admin", "admin123")
    client.post("/chamados/1/status", data={"status": "andamento", "_csrf": csrf(client, "/chamados")})
    client.post("/logout", data={"_csrf": csrf(client, "/chamados")})
    entrar(client, "usuario", "usuario123")
    r = client.post("/chamados/1/cancelar", data={"_csrf": csrf(client, "/chamados")}, follow_redirects=True)
    assert "não pode mais ser cancelado" in r.get_data(as_text=True)
    abrir(client, item="Teclado")
    client.post("/chamados/2/cancelar", data={"_csrf": csrf(client, "/chamados")})
    assert "Teclado" not in client.get("/chamados").get_data(as_text=True)


def test_usuario_comum_nao_altera_status(client):
    entrar(client, "usuario", "usuario123")
    abrir(client)
    client.post("/chamados/1/status", data={"status": "finalizado", "_csrf": csrf(client, "/chamados")})
    assert "Em aberto" in client.get("/chamados").get_data(as_text=True)


def test_admin_altera_status_e_consulta(client):
    entrar(client, "admin", "admin123")
    abrir(client, setor="TI", data="2026-11-02", item="Roteador")
    abrir(client, setor="Comercial", data="2026-11-03", item="Telefone IP")
    client.post("/chamados/1/status", data={"status": "finalizado", "_csrf": csrf(client, "/chamados")})
    client.post("/chamados/1/status", data={"status": "aberto", "_csrf": csrf(client, "/chamados")})
    html = client.get("/chamados?status=finalizado").get_data(as_text=True)
    assert "Roteador" in html and "Telefone IP" not in html
    html = client.get("/chamados?setor=Comercial").get_data(as_text=True)
    assert "Telefone IP" in html and "Roteador" not in html
    html = client.get("/chamados?data=2026-11-02").get_data(as_text=True)
    assert "Roteador" in html and "Telefone IP" not in html


def test_csrf(client):
    entrar(client, "admin", "admin123")
    assert client.post("/chamados/novo", data={"item": "x"}).status_code == 400
