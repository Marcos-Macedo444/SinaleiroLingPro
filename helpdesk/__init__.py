"""Sinaleiro — helpdesk web para abertura e acompanhamento de chamados."""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, render_template

from .controllers import AuthController, ChamadoController
from .database import Database
from .models import StatusChamado
from .repositories import ChamadoRepository, SetorRepository, UsuarioRepository
from .security import Csrf, SessaoUsuario
from .services import AuthService, ChamadoService

RAIZ = Path(__file__).resolve().parent.parent

# Na Vercel o código roda em funções serverless: só /tmp aceita escrita.
NA_VERCEL = bool(os.environ.get("VERCEL"))


class HelpdeskApp:
    """Monta a aplicação: banco, repositórios, serviços e controllers."""

    def __init__(self, caminho_banco: Path | None = None):
        self.flask = Flask(__name__)
        self.flask.config.update(
            SECRET_KEY=os.environ.get("SECRET_KEY") or self._chave_local(),
            PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE="Lax",
        )

        padrao = Path("/tmp/helpdesk.sqlite") if NA_VERCEL else RAIZ / "data" / "helpdesk.sqlite"
        self.db = Database(caminho_banco or padrao)
        self.db.init_app(self.flask)
        if NA_VERCEL and caminho_banco is None:
            self._popular_demo()

        usuarios = UsuarioRepository(self.db)
        setores = SetorRepository(self.db)
        chamados = ChamadoRepository(self.db)
        self.sessao = SessaoUsuario(usuarios)

        auth_ctrl = AuthController(AuthService(usuarios), self.sessao)
        chamado_ctrl = ChamadoController(ChamadoService(chamados, setores), setores, self.sessao)
        self.flask.register_blueprint(auth_ctrl.blueprint)
        self.flask.register_blueprint(chamado_ctrl.blueprint)

        self._configurar_templates()

    def _configurar_templates(self) -> None:
        app = self.flask
        app.before_request(Csrf.verificar)

        @app.context_processor
        def globais():
            return {
                "usuario_logado": self.sessao.atual(),
                "csrf_token": Csrf.token,
                "Status": StatusChamado,
            }

        @app.errorhandler(404)
        def nao_encontrado(_e):
            return render_template("erro.html", codigo=404,
                                   mensagem="Essa página não existe. Volte para a lista de chamados."), 404

        @app.errorhandler(400)
        def requisicao_invalida(e):
            return render_template("erro.html", codigo=400, mensagem=e.description), 400

    def _popular_demo(self) -> None:
        """Na Vercel o banco nasce vazio a cada instância: preenche com exemplos."""
        from .demo import popular
        with self.flask.app_context():
            popular(ChamadoRepository(self.db), somente_se_vazio=True)

    @staticmethod
    def _chave_local() -> str:
        if NA_VERCEL:
            # Sem SECRET_KEY configurada, usa uma chave estável do projeto para que
            # todas as instâncias aceitem o mesmo cookie de sessão.
            base = os.environ.get("VERCEL_PROJECT_ID", "") + os.environ.get("VERCEL_GIT_REPO_ID", "sinaleiro")
            return hashlib.sha256(f"sinaleiro:{base}".encode()).hexdigest()
        arquivo = RAIZ / "data" / ".secret_key"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        if not arquivo.exists():
            arquivo.write_text(secrets.token_hex(32))
        return arquivo.read_text().strip()


def create_app(caminho_banco: Path | None = None) -> Flask:
    return HelpdeskApp(caminho_banco).flask
