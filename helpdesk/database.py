"""Acesso ao banco de dados.

`Database` define a interface usada pelos repositórios; `SqliteDatabase`
(desenvolvimento local) e `PostgresDatabase` (produção, ex.: Neon na Vercel)
implementam as diferenças de cada banco. Os repositórios escrevem SQL com
`?` como marcador e não sabem qual banco está por trás.
"""
from __future__ import annotations

import os
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from flask import Flask, g
from werkzeug.security import generate_password_hash

SETORES_INICIAIS = [
    "Administrativo", "Almoxarifado", "Comercial", "Financeiro", "Jurídico",
    "Logística", "Produção", "Recepção", "Recursos Humanos", "TI",
]

# {pk} é trocado pela coluna de chave primária autoincremental de cada banco.
ESQUEMA = [
    """CREATE TABLE IF NOT EXISTS usuarios (
        id      {pk},
        nome    TEXT    NOT NULL,
        login   TEXT    NOT NULL UNIQUE,
        senha   TEXT    NOT NULL,
        perfil  INTEGER NOT NULL DEFAULT 0 CHECK (perfil IN (0, 1))
    )""",
    """CREATE TABLE IF NOT EXISTS setores (
        id   {pk},
        nome TEXT NOT NULL UNIQUE
    )""",
    """CREATE TABLE IF NOT EXISTS chamados (
        id          {pk},
        usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
        data        TEXT    NOT NULL,
        setor       TEXT    NOT NULL,
        item        TEXT    NOT NULL,
        descricao   TEXT    NOT NULL,
        status      TEXT    NOT NULL DEFAULT 'aberto'
                    CHECK (status IN ('aberto', 'andamento', 'finalizado')),
        etiqueta    TEXT    NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_chamados_data  ON chamados (data)",
    "CREATE INDEX IF NOT EXISTS idx_chamados_setor ON chamados (setor)",
]


class Database(ABC):
    """Interface comum: uma conexão por requisição e métodos de consulta."""

    PK = ""
    temporario = False  # True quando os dados podem se perder (ex.: /tmp na Vercel)

    def init_app(self, app: Flask) -> None:
        self.criar_esquema()
        app.teardown_appcontext(self._fechar)

    # ---- conexão ----------------------------------------------------------
    @abstractmethod
    def _conectar(self) -> Any: ...

    def _adaptar(self, sql: str) -> str:
        return sql

    def conexao(self) -> Any:
        if "db" not in g:
            g.db = self._conectar()
        return g.db

    def _fechar(self, _exc=None) -> None:
        con = g.pop("db", None)
        if con is not None:
            con.close()

    # ---- operações --------------------------------------------------------
    def consultar(self, sql: str, params: tuple = ()) -> list[dict]:
        cur = self.conexao().execute(self._adaptar(sql), params)
        return [dict(linha) for linha in cur.fetchall()]

    def consultar_um(self, sql: str, params: tuple = ()) -> dict | None:
        linhas = self.consultar(sql, params)
        return linhas[0] if linhas else None

    def executar(self, sql: str, params: tuple = ()) -> int:
        """Executa uma alteração e confirma. Devolve quantas linhas mudaram."""
        con = self.conexao()
        cur = con.execute(self._adaptar(sql), params)
        con.commit()
        return cur.rowcount

    @abstractmethod
    def inserir(self, sql: str, params: tuple = ()) -> int:
        """Executa um INSERT e devolve o id gerado."""

    # ---- esquema e dados iniciais -----------------------------------------
    def criar_esquema(self) -> None:
        con = self._conectar()
        try:
            self._antes_do_esquema(con)
            for comando in ESQUEMA:
                con.execute(comando.format(pk=self.PK))
            self._popular(con)
            con.commit()
        finally:
            con.close()

    def _antes_do_esquema(self, con: Any) -> None:
        pass

    def _popular(self, con: Any) -> None:
        """Cria o administrador (perfil 1), o usuário comum (perfil 0) e os setores.
        Idempotente: pode rodar em várias instâncias ao mesmo tempo."""
        total = con.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()
        if (total["n"] if isinstance(total, dict) else total[0]) == 0:
            sql = self._adaptar(
                "INSERT INTO usuarios (nome, login, senha, perfil) VALUES (?, ?, ?, ?) "
                "ON CONFLICT (login) DO NOTHING"
            )
            for nome, login, senha, perfil in [("Administrador", "admin", "admin123", 1),
                                                ("Usuário Comum", "usuario", "usuario123", 0)]:
                con.execute(sql, (nome, login, generate_password_hash(senha), perfil))
        sql = self._adaptar("INSERT INTO setores (nome) VALUES (?) ON CONFLICT (nome) DO NOTHING")
        for setor in SETORES_INICIAIS:
            con.execute(sql, (setor,))


class SqliteDatabase(Database):
    PK = "INTEGER PRIMARY KEY AUTOINCREMENT"

    def __init__(self, caminho: Path, temporario: bool = False):
        self.caminho = Path(caminho)
        self.temporario = temporario

    def init_app(self, app: Flask) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        super().init_app(app)

    def _conectar(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.caminho)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def inserir(self, sql: str, params: tuple = ()) -> int:
        con = self.conexao()
        cur = con.execute(sql, params)
        con.commit()
        return cur.lastrowid


class PostgresDatabase(Database):
    PK = "INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY"

    def __init__(self, url: str):
        self.url = url

    def _conectar(self):
        import psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(self.url, row_factory=dict_row, connect_timeout=10)

    def _adaptar(self, sql: str) -> str:
        return sql.replace("?", "%s")

    def _antes_do_esquema(self, con) -> None:
        # Evita corrida quando várias instâncias sobem juntas.
        con.execute("SELECT pg_advisory_xact_lock(724242)")

    def inserir(self, sql: str, params: tuple = ()) -> int:
        con = self.conexao()
        linha = con.execute(self._adaptar(sql) + " RETURNING id", params).fetchone()
        con.commit()
        return linha["id"]


def criar_database(caminho: Path | None, raiz: Path, na_vercel: bool) -> Database:
    """Escolhe o banco: caminho explícito (testes) > Postgres (DATABASE_URL) > SQLite."""
    if caminho is not None:
        return SqliteDatabase(caminho)
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if url:
        return PostgresDatabase(url)
    if na_vercel:
        return SqliteDatabase(Path("/tmp/helpdesk.sqlite"), temporario=True)
    return SqliteDatabase(raiz / "data" / "helpdesk.sqlite")
