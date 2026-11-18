"""Repositórios: única camada que escreve SQL."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from .database import Database
from .models import Chamado, Perfil, StatusChamado, Usuario


class Repository:
    def __init__(self, db: Database):
        self._db = db

    @property
    def con(self) -> sqlite3.Connection:
        return self._db.conexao()


class UsuarioRepository(Repository):
    def buscar_por_id(self, usuario_id: int) -> Usuario | None:
        row = self.con.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return self._mapear(row) if row else None

    def buscar_por_login(self, login: str) -> Usuario | None:
        row = self.con.execute(
            "SELECT * FROM usuarios WHERE login = ? COLLATE NOCASE", (login,)
        ).fetchone()
        return self._mapear(row) if row else None

    @staticmethod
    def _mapear(row: sqlite3.Row) -> Usuario:
        return Usuario(
            id=row["id"], nome=row["nome"], login=row["login"],
            senha_hash=row["senha"], perfil=Perfil(row["perfil"]),
        )


class SetorRepository(Repository):
    def listar(self) -> list[str]:
        return [r["nome"] for r in self.con.execute("SELECT nome FROM setores ORDER BY nome")]


@dataclass
class FiltroChamados:
    usuario_id: int | None = None  # None = todos os usuários (visão do administrador)
    data: date | None = None
    setor: str | None = None
    status: StatusChamado | None = None


class ChamadoRepository(Repository):
    _SELECT = """
        SELECT c.*, u.nome AS solicitante
          FROM chamados c
          JOIN usuarios u ON u.id = c.usuario_id
    """

    def buscar_por_id(self, chamado_id: int) -> Chamado | None:
        row = self.con.execute(self._SELECT + " WHERE c.id = ?", (chamado_id,)).fetchone()
        return self._mapear(row) if row else None

    def listar(self, filtro: FiltroChamados) -> list[Chamado]:
        where, params = self._where(filtro)
        sql = self._SELECT + where + " ORDER BY c.data DESC, c.id DESC"
        return [self._mapear(r) for r in self.con.execute(sql, params)]

    def contar_por_status(self, filtro: FiltroChamados) -> dict[StatusChamado, int]:
        sem_status = FiltroChamados(filtro.usuario_id, filtro.data, filtro.setor, None)
        where, params = self._where(sem_status)
        rows = self.con.execute(
            f"SELECT c.status, COUNT(*) AS total FROM chamados c{where} GROUP BY c.status", params
        )
        contagem = {s: 0 for s in StatusChamado}
        for r in rows:
            contagem[StatusChamado(r["status"])] = r["total"]
        return contagem

    def inserir(self, chamado: Chamado) -> Chamado:
        cur = self.con.execute(
            """INSERT INTO chamados (usuario_id, data, setor, item, descricao, status, etiqueta)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (chamado.usuario_id, chamado.data.isoformat(), chamado.setor, chamado.item,
             chamado.descricao, chamado.status.value, chamado.etiqueta),
        )
        self.con.commit()
        chamado.id = cur.lastrowid
        return chamado

    def atualizar_status(self, chamado_id: int, status: StatusChamado) -> None:
        self.con.execute("UPDATE chamados SET status = ? WHERE id = ?", (status.value, chamado_id))
        self.con.commit()

    def excluir(self, chamado_id: int) -> None:
        self.con.execute("DELETE FROM chamados WHERE id = ?", (chamado_id,))
        self.con.commit()

    @staticmethod
    def _where(filtro: FiltroChamados) -> tuple[str, list]:
        condicoes, params = [], []
        if filtro.usuario_id is not None:
            condicoes.append("c.usuario_id = ?")
            params.append(filtro.usuario_id)
        if filtro.data is not None:
            condicoes.append("c.data = ?")
            params.append(filtro.data.isoformat())
        if filtro.setor:
            condicoes.append("c.setor = ?")
            params.append(filtro.setor)
        if filtro.status is not None:
            condicoes.append("c.status = ?")
            params.append(filtro.status.value)
        return (" WHERE " + " AND ".join(condicoes) if condicoes else ""), params

    @staticmethod
    def _mapear(row: sqlite3.Row) -> Chamado:
        return Chamado(
            id=row["id"], usuario_id=row["usuario_id"], data=date.fromisoformat(row["data"]),
            setor=row["setor"], item=row["item"], descricao=row["descricao"],
            etiqueta=row["etiqueta"], status=StatusChamado(row["status"]),
            solicitante=row["solicitante"],
        )
