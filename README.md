# Central de Chamados — Helpdesk Web

Ferramenta web para abertura e acompanhamento de chamados de reparo de equipamentos
(computadores, impressoras etc.), feita em **Python (Flask)**, orientada a objetos e
integrada a um banco **SQLite**.

## Como executar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Acesse **http://localhost:5000**. O banco (`data/helpdesk.sqlite`) é criado sozinho na
primeira execução, já com os usuários iniciais:

| Perfil              | Login     | Senha        |
|---------------------|-----------|--------------|
| Administrador (1)   | `admin`   | `admin123`   |
| Usuário comum (0)   | `usuario` | `usuario123` |

Opcional, para popular chamados de exemplo: `python popular_demo.py`.
Testes automatizados: `python -m pytest`.

## Requisitos atendidos

| Requisito | Onde |
|---|---|
| Login e senha, senha com hash | `AuthService`, `SessaoUsuario` |
| Permissões 0 = comum, 1 = administrador | `Perfil(IntEnum)` + `CHECK (perfil IN (0,1))` no banco |
| Logout | `POST /logout` |
| Abertura de chamado: data, setor, item, descrição, status, etiqueta | `ChamadoService.abrir` |
| Status inicial sempre "Em aberto" | definido no serviço, não pelo formulário |
| Relatório ordenado do mais recente para o mais antigo | `ORDER BY data DESC, id DESC` |
| Cancelamento só sem tratativa iniciada, excluindo o registro | `ChamadoService.cancelar` + `Chamado.pode_ser_cancelado` |
| Admin altera status para "Em andamento" / "Finalizado" | `ChamadoService.alterar_status` |
| Admin consulta por data ou setor | filtros da lista (`FiltroChamados`) |
| Cores: verde = aberto, amarelo = andamento, vermelho = finalizado | `StatusChamado.cor` + semáforo na interface |

## Arquitetura (orientada a objetos, em camadas)

```
helpdesk/
├── models.py        Entidades: Usuario, Chamado, Perfil (enum), StatusChamado (enum)
├── database.py      Database: conexão SQLite, criação do esquema e dados iniciais
├── repositories.py  UsuarioRepository, ChamadoRepository, SetorRepository (único lugar com SQL)
├── services.py      AuthService, ChamadoService (regras de negócio e validação)
├── security.py      SessaoUsuario (login/permissões por decorator) e Csrf
├── controllers.py   AuthController, ChamadoController (rotas HTTP)
├── __init__.py      HelpdeskApp: monta as dependências (injeção via construtor)
├── templates/       Telas (Jinja2)
└── static/          CSS e JS da interface
```

Cada camada só conhece a de baixo: controller → service → repository → database.
Herança: todos os repositórios estendem `Repository`. Encapsulamento: regras como
"pode ser cancelado" ficam dentro da própria entidade `Chamado`.

## Interface

- O status é mostrado como um **semáforo** (caixa com três lâmpadas, acesa só a do status), sempre acompanhado do texto. Assim a informação não depende só da cor.
- A etiqueta de patrimônio aparece como uma plaqueta metálica, igual à colada no equipamento.
- Movimento com função:
  - transições entre páginas (View Transitions API);
  - lâmpadas que acendem com cintilação de lâmpada real;
  - o admin vê a cor nova na linha antes de salvar;
  - a linha alterada ou criada recebe destaque;
  - o chamado cancelado sai da lista;
  - avisos com contagem regressiva, que pausa no hover;
  - semáforo piscando amarelo quando a lista está vazia.
- Responsiva até celular, com foco de teclado visível, respeito a `prefers-reduced-motion` e proteção CSRF em todos os formulários.
