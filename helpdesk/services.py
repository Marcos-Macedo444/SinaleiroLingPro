"""Regras de negócio do helpdesk."""
from __future__ import annotations

from datetime import date

from .models import Chamado, StatusChamado, Usuario
from .repositories import ChamadoRepository, FiltroChamados, SetorRepository, UsuarioRepository


class RegraNegocioError(Exception):
    """Ação não permitida pelas regras do sistema."""


class ValidacaoError(Exception):
    def __init__(self, erros: dict[str, str]):
        super().__init__("Dados inválidos")
        self.erros = erros


class AuthService:
    def __init__(self, usuarios: UsuarioRepository):
        self._usuarios = usuarios

    def autenticar(self, login: str, senha: str) -> Usuario | None:
        usuario = self._usuarios.buscar_por_login(login.strip())
        if usuario and usuario.verificar_senha(senha):
            return usuario
        return None


class ChamadoService:
    LIMITES = {"item": 80, "etiqueta": 30, "descricao": 1000}

    def __init__(self, chamados: ChamadoRepository, setores: SetorRepository):
        self._chamados = chamados
        self._setores = setores

    # ---- consulta -------------------------------------------------------
    def filtro_para(self, usuario: Usuario, *, data=None, setor=None, status=None) -> FiltroChamados:
        """Usuário comum vê os próprios chamados; o administrador vê todos e pode
        buscar por data ou setor."""
        if not usuario.is_admin:
            data, setor = None, None
        return FiltroChamados(
            usuario_id=None if usuario.is_admin else usuario.id,
            data=data, setor=setor or None, status=status,
        )

    def listar(self, filtro: FiltroChamados) -> list[Chamado]:
        return self._chamados.listar(filtro)

    def contagem(self, filtro: FiltroChamados) -> dict[StatusChamado, int]:
        return self._chamados.contar_por_status(filtro)

    # ---- abertura -------------------------------------------------------
    def abrir(self, usuario: Usuario, dados: dict[str, str]) -> Chamado:
        erros: dict[str, str] = {}
        campos = {k: (dados.get(k) or "").strip() for k in ("data", "setor", "item", "descricao", "etiqueta")}

        try:
            data_chamado = date.fromisoformat(campos["data"])
        except ValueError:
            data_chamado = None
            erros["data"] = "Informe a data do chamado."

        if campos["setor"] not in self._setores.listar():
            erros["setor"] = "Escolha o setor onde está o equipamento."
        if not campos["item"]:
            erros["item"] = "Informe qual equipamento precisa de reparo."
        if not campos["descricao"]:
            erros["descricao"] = "Descreva o problema para a equipe saber o que verificar."
        if not campos["etiqueta"]:
            erros["etiqueta"] = "Informe o número da etiqueta de patrimônio."
        for campo, limite in self.LIMITES.items():
            if len(campos[campo]) > limite and campo not in erros:
                erros[campo] = f"Use no máximo {limite} caracteres."

        if erros:
            raise ValidacaoError(erros)

        chamado = Chamado(
            id=None, usuario_id=usuario.id, data=data_chamado, setor=campos["setor"],
            item=campos["item"], descricao=campos["descricao"],
            etiqueta=campos["etiqueta"].upper(),
            status=StatusChamado.ABERTO,  # todo chamado começa "em aberto"
        )
        return self._chamados.inserir(chamado)

    # ---- cancelamento ---------------------------------------------------
    def cancelar(self, usuario: Usuario, chamado_id: int) -> Chamado:
        chamado = self._obter(chamado_id)
        if not usuario.is_admin and chamado.usuario_id != usuario.id:
            raise RegraNegocioError("Você só pode cancelar chamados abertos por você.")
        if not chamado.pode_ser_cancelado:
            raise RegraNegocioError(
                f"O chamado {chamado.numero} já está {chamado.status.rotulo.lower()} e não pode mais ser cancelado."
            )
        self._chamados.excluir(chamado_id)  # cancelamento exclui o chamado do sistema
        return chamado

    # ---- alteração de status (administrador) ----------------------------
    def alterar_status(self, usuario: Usuario, chamado_id: int, novo_status: str) -> Chamado:
        if not usuario.is_admin:
            raise RegraNegocioError("Somente administradores podem alterar o status.")
        try:
            status = StatusChamado(novo_status)
        except ValueError:
            raise RegraNegocioError("Status inválido.") from None
        if status not in StatusChamado.alteraveis_pelo_admin():
            raise RegraNegocioError("O status só pode ser alterado para Em andamento ou Finalizado.")

        chamado = self._obter(chamado_id)
        self._chamados.atualizar_status(chamado_id, status)
        chamado.status = status
        return chamado

    def _obter(self, chamado_id: int) -> Chamado:
        chamado = self._chamados.buscar_por_id(chamado_id)
        if chamado is None:
            raise RegraNegocioError("Chamado não encontrado. Ele pode ter sido cancelado.")
        return chamado
