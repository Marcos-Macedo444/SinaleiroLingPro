"""Chamados de exemplo para demonstração."""
from datetime import date, timedelta

from .models import Chamado, StatusChamado
from .repositories import ChamadoRepository, FiltroChamados

EXEMPLOS = [
    (0, "Financeiro", "Impressora HP LaserJet", "Papel enrosca na bandeja 2 e a impressão sai manchada nas bordas.", "PAT-004512", "aberto", 2),
    (0, "Recepção", "Telefone IP", "Sem tom de discagem desde a troca do cabo de rede.", "PAT-003107", "andamento", 2),
    (1, "Comercial", "Notebook Dell Latitude", "Bateria não carrega acima de 40% e o carregador esquenta.", "PAT-005220", "aberto", 2),
    (2, "Produção", "Computador da linha 3", "Reinicia sozinho ao abrir o sistema de apontamento.", "PAT-002981", "finalizado", 1),
    (3, "Recursos Humanos", "Monitor LG 24\"", "Imagem piscando e com faixa verde na lateral direita.", "PAT-004090", "andamento", 1),
    (5, "Logística", "Leitor de código de barras", "Não reconhece etiquetas novas da expedição.", "PAT-006433", "finalizado", 2),
    (8, "TI", "Nobreak sala de servidores", "Alarme sonoro intermitente e bateria indicando falha.", "PAT-001002", "finalizado", 1),
]


def popular(repo: ChamadoRepository, somente_se_vazio: bool = False) -> int:
    if somente_se_vazio and repo.listar(FiltroChamados()):
        return 0
    for dias, setor, item, desc, etq, status, uid in EXEMPLOS:
        repo.inserir(Chamado(None, uid, date.today() - timedelta(days=dias), setor, item, desc, etq, StatusChamado(status)))
    return len(EXEMPLOS)
