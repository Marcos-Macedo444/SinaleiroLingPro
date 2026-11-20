"""Insere chamados de exemplo para demonstração (python popular_demo.py)."""
from helpdesk import HelpdeskApp
from helpdesk.demo import popular
from helpdesk.repositories import ChamadoRepository

app = HelpdeskApp()
with app.flask.app_context():
    print(f"{popular(ChamadoRepository(app.db))} chamados de exemplo inseridos.")
