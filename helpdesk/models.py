"""Entidades do domínio: usuário, chamado, perfis e status."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum, IntEnum

from werkzeug.security import check_password_hash


class Perfil(IntEnum):
    """Lógica de permissões exigida: 0 = usuário comum, 1 = administrador."""

    COMUM = 0
    ADMINISTRADOR = 1

    @property
    def rotulo(self) -> str:
        return "Administrador" if self is Perfil.ADMINISTRADOR else "Usuário comum"


class StatusChamado(Enum):
    ABERTO = "aberto"
    ANDAMENTO = "andamento"
    FINALIZADO = "finalizado"

    @property
    def rotulo(self) -> str:
        return {
            StatusChamado.ABERTO: "Em aberto",
            StatusChamado.ANDAMENTO: "Em andamento",
            StatusChamado.FINALIZADO: "Finalizado",
        }[self]

    @property
    def cor(self) -> str:
        """Sistema de cores: verde = aberto, amarelo = andamento, vermelho = finalizado."""
        return {
            StatusChamado.ABERTO: "verde",
            StatusChamado.ANDAMENTO: "amarelo",
            StatusChamado.FINALIZADO: "vermelho",
        }[self]

    @classmethod
    def alteraveis_pelo_admin(cls) -> list[StatusChamado]:
        return [cls.ANDAMENTO, cls.FINALIZADO]


@dataclass
class Usuario:
    id: int
    nome: str
    login: str
    senha_hash: str
    perfil: Perfil

    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self) -> bool:
        return self.perfil is Perfil.ADMINISTRADOR

    @property
    def iniciais(self) -> str:
        partes = [p for p in self.nome.split() if p]
        return "".join(p[0] for p in partes[:2]).upper() or "?"


@dataclass
class Chamado:
    id: int | None
    usuario_id: int
    data: date
    setor: str
    item: str
    descricao: str
    etiqueta: str
    status: StatusChamado = StatusChamado.ABERTO
    solicitante: str | None = None

    @property
    def pode_ser_cancelado(self) -> bool:
        """Só pode ser cancelado enquanto nenhuma tratativa foi iniciada."""
        return self.status is StatusChamado.ABERTO

    @property
    def data_formatada(self) -> str:
        return self.data.strftime("%d/%m/%Y")

    @property
    def numero(self) -> str:
        return f"{self.id:04d}" if self.id else "—"
