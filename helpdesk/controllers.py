"""Controllers: recebem a requisição, chamam os serviços e escolhem a resposta."""
from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .models import StatusChamado
from .repositories import SetorRepository
from .security import SessaoUsuario
from .services import AuthService, ChamadoService, RegraNegocioError, ValidacaoError


class AuthController:
    def __init__(self, auth: AuthService, sessao: SessaoUsuario):
        self.auth = auth
        self.sessao = sessao
        self.blueprint = Blueprint("auth", __name__)
        self.blueprint.add_url_rule("/login", "login", self.login, methods=["GET", "POST"])
        self.blueprint.add_url_rule("/logout", "logout", self.logout, methods=["POST"])

    def login(self):
        if self.sessao.atual():
            return redirect(url_for("chamados.listar"))

        erro, login = None, ""
        if request.method == "POST":
            login = request.form.get("login", "")
            usuario = self.auth.autenticar(login, request.form.get("senha", ""))
            if usuario:
                self.sessao.entrar(usuario)
                destino = request.args.get("proximo", "")
                return redirect(destino if destino.startswith("/") and not destino.startswith("//")
                                else url_for("chamados.listar"))
            erro = "Login ou senha incorretos. Confira os dados e tente de novo."
        return render_template("auth/login.html", erro=erro, login=login), (401 if erro else 200)

    def logout(self):
        self.sessao.sair()
        flash("Você saiu do sistema.", "ok")
        return redirect(url_for("auth.login"))


class ChamadoController:
    def __init__(self, servico: ChamadoService, setores: SetorRepository, sessao: SessaoUsuario):
        self.servico = servico
        self.setores = setores
        self.sessao = sessao
        bp = Blueprint("chamados", __name__)
        login, admin = sessao.login_obrigatorio, sessao.admin_obrigatorio
        bp.add_url_rule("/", "inicio", login(lambda: redirect(url_for("chamados.listar"))))
        bp.add_url_rule("/chamados", "listar", login(self.listar))
        bp.add_url_rule("/chamados/novo", "novo", login(self.novo), methods=["GET", "POST"])
        bp.add_url_rule("/chamados/<int:chamado_id>/cancelar", "cancelar", login(self.cancelar), methods=["POST"])
        bp.add_url_rule("/chamados/<int:chamado_id>/status", "status", admin(self.alterar_status), methods=["POST"])
        self.blueprint = bp

    def listar(self):
        usuario = self.sessao.atual()
        data = self._data(request.args.get("data"))
        setor = request.args.get("setor") or None
        status = self._status(request.args.get("status"))

        filtro = self.servico.filtro_para(usuario, data=data, setor=setor, status=status)
        return render_template(
            "chamados/lista.html",
            chamados=self.servico.listar(filtro),
            contagem=self.servico.contagem(filtro),
            setores=self.setores.listar(),
            filtro=filtro,
            busca_ativa=bool(filtro.data or filtro.setor),
            status_admin=StatusChamado.alteraveis_pelo_admin(),
        )

    def novo(self):
        usuario = self.sessao.atual()
        dados = {"data": date.today().isoformat()}
        erros: dict[str, str] = {}

        if request.method == "POST":
            dados = request.form.to_dict()
            try:
                chamado = self.servico.abrir(usuario, dados)
            except ValidacaoError as e:
                erros = e.erros
            else:
                flash(f"Chamado {chamado.numero} aberto para {chamado.item}.", "ok")
                return redirect(url_for("chamados.listar", _anchor=f"chamado-{chamado.id}"))

        return render_template(
            "chamados/novo.html", dados=dados, erros=erros, setores=self.setores.listar(),
            hoje=date.today().isoformat(),
        ), (422 if erros else 200)

    def cancelar(self, chamado_id: int):
        try:
            chamado = self.servico.cancelar(self.sessao.atual(), chamado_id)
            flash(f"Chamado {chamado.numero} cancelado e removido do sistema.", "ok")
        except RegraNegocioError as e:
            flash(str(e), "erro")
        return redirect(self._voltar())

    def alterar_status(self, chamado_id: int):
        try:
            chamado = self.servico.alterar_status(self.sessao.atual(), chamado_id, request.form.get("status", ""))
            flash(f"Chamado {chamado.numero} agora está {chamado.status.rotulo.lower()}.", "ok")
        except RegraNegocioError as e:
            flash(str(e), "erro")
            return redirect(self._voltar())
        return redirect(f"{self._voltar()}#chamado-{chamado_id}")

    # ---- auxiliares -----------------------------------------------------
    @staticmethod
    def _voltar() -> str:
        destino = request.form.get("voltar", "")
        return destino if destino.startswith("/chamados") else url_for("chamados.listar")

    @staticmethod
    def _data(valor: str | None) -> date | None:
        try:
            return date.fromisoformat(valor) if valor else None
        except ValueError:
            return None

    @staticmethod
    def _status(valor: str | None) -> StatusChamado | None:
        try:
            return StatusChamado(valor) if valor else None
        except ValueError:
            return None
