"""Sessão, controle de acesso por perfil e proteção CSRF."""
from __future__ import annotations

import secrets
from functools import wraps
from typing import Callable

from flask import abort, flash, g, redirect, request, session, url_for

from .models import Usuario
from .repositories import UsuarioRepository


class SessaoUsuario:
    CHAVE = "usuario_id"

    def __init__(self, usuarios: UsuarioRepository):
        self._usuarios = usuarios

    def entrar(self, usuario: Usuario) -> None:
        session.clear()
        session[self.CHAVE] = usuario.id
        session.permanent = True

    def sair(self) -> None:
        session.clear()

    def atual(self) -> Usuario | None:
        if "usuario" not in g:
            uid = session.get(self.CHAVE)
            g.usuario = self._usuarios.buscar_por_id(uid) if uid else None
        return g.usuario

    # ---- decorators -----------------------------------------------------
    def login_obrigatorio(self, view: Callable) -> Callable:
        @wraps(view)
        def wrapper(*args, **kwargs):
            if self.atual() is None:
                return redirect(url_for("auth.login", proximo=request.path))
            return view(*args, **kwargs)
        return wrapper

    def admin_obrigatorio(self, view: Callable) -> Callable:
        @wraps(view)
        def wrapper(*args, **kwargs):
            usuario = self.atual()
            if usuario is None:
                return redirect(url_for("auth.login"))
            if not usuario.is_admin:
                flash("Somente administradores podem fazer essa alteração.", "erro")
                return redirect(url_for("chamados.listar"))
            return view(*args, **kwargs)
        return wrapper


class Csrf:
    CHAVE = "_csrf"

    @classmethod
    def token(cls) -> str:
        if cls.CHAVE not in session:
            session[cls.CHAVE] = secrets.token_urlsafe(32)
        return session[cls.CHAVE]

    @classmethod
    def verificar(cls) -> None:
        if request.method == "POST":
            enviado = request.form.get(cls.CHAVE, "")
            if not enviado or not secrets.compare_digest(enviado, session.get(cls.CHAVE, "")):
                abort(400, "Formulário expirado. Recarregue a página e tente de novo.")
