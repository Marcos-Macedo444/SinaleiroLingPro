"""Acesso ao banco SQLite: criação do esquema e dados iniciais."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, g
from werkzeug.security import generate_password_hash

SETORES_INICIAIS = [
    "Administrativo", "Almoxarifado", "Comercial", "Financeiro", "Jurídico",
    "Logística", "Produção", "Recepção", "Recursos Humanos", "TI",
]

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nome    TEXT    NOT NULL,
    login   TEXT    NOT NULL UNIQUE,
    senha   TEXT    NOT NULL,
    perfil  INTEGER NOT NULL DEFAULT 0 CHECK (perfil IN (0, 1))
);

CREATE TABLE IF NOT EXISTS setores (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS chamados (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    data        TEXT    NOT NULL,
    setor       TEXT    NOT NULL,
    item        TEXT    NOT NULL,
    descricao   TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'aberto'
                CHECK (status IN ('aberto', 'andamento', 'finalizado')),
    etiqueta    TEXT    NOT NULL,
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_chamados_data  ON chamados (data);
CREATE INDEX IF NOT EXISTS idx_chamados_setor ON chamados (setor);
"""


class Database:
    """Gerencia uma conexão SQLite por requisição."""

    def __init__(self, caminho: Path):
        self.caminho = caminho

    def init_app(self, app: Flask) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.criar_esquema()
        app.teardown_appcontext(self._fechar)

    def conexao(self) -> sqlite3.Connection:
        if "db" not in g:
            g.db = self._conectar()
        return g.db

    def _conectar(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.caminho)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def _fechar(self, _exc=None) -> None:
        con = g.pop("db", None)
        if con is not None:
            con.close()

    def criar_esquema(self) -> None:
        with self._conectar() as con:
            con.executescript(ESQUEMA)
            if con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
                self._popular(con)

    @staticmethod
    def _popular(con: sqlite3.Connection) -> None:
        """Cria o administrador (perfil 1) e o usuário comum (perfil 0) iniciais."""
        con.executemany(
            "INSERT INTO usuarios (nome, login, senha, perfil) VALUES (?, ?, ?, ?)",
            [
                ("Administrador", "admin", generate_password_hash("admin123"), 1),
                ("Usuário Comum", "usuario", generate_password_hash("usuario123"), 0),
            ],
        )
        con.executemany(
            "INSERT OR IGNORE INTO setores (nome) VALUES (?)",
            [(s,) for s in SETORES_INICIAIS],
        )
