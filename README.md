# Sinaleiro — Helpdesk Web

Ferramenta web para abertura e acompanhamento de chamados de reparo de equipamentos
(computadores, impressoras etc.), feita em **Python (Flask)**, orientada a objetos e
integrada a um banco **SQLite**.

## Como executar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
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
| Cancelamento só sem tratativa iniciada, excluindo o registro | `ChamadoService.cancelar` + `ChamadoRepository.excluir_se_aberto` (atômico) |
| Admin altera status para "Em andamento" / "Finalizado" | `ChamadoService.alterar_status` |
| Admin consulta por data ou setor | filtros da lista (`FiltroChamados`) |
| Cores: verde = aberto, amarelo = andamento, vermelho = finalizado | `StatusChamado.cor` + semáforo na interface |

## Banco de dados

O sistema funciona com dois bancos, escolhidos automaticamente:

| Onde | Banco | Como |
|---|---|---|
| No seu computador | **SQLite** (`data/helpdesk.sqlite`) | nada a configurar |
| Na Vercel (produção) | **Postgres** (ex.: Neon) | variável `DATABASE_URL` (ou `POSTGRES_URL`) |

> **Por que Postgres na Vercel?** A Vercel roda o sistema em vários servidores
> temporários. Com SQLite, cada servidor teria a própria cópia do banco: um chamado
> cancelado em um servidor "voltava" quando a página era atendida por outro. Com
> Postgres todos usam o mesmo banco. Sem `DATABASE_URL` na Vercel, o sistema ainda
> funciona com um banco temporário e mostra um aviso para o administrador.

### Publicar na Vercel

1. Em vercel.com/new, importe o repositório e clique em **Deploy**.
2. No projeto, abra **Storage → Create Database → Neon (Postgres)** e conecte ao projeto.
   A Vercel cria a variável `DATABASE_URL` sozinha.
3. (Recomendado) Crie a variável `SECRET_KEY` com um texto aleatório longo.
4. Faça **Redeploy**. As tabelas e os usuários iniciais são criados no primeiro acesso.

Testes nos dois bancos: `python -m pytest` (SQLite) e
`TEST_DATABASE_URL=postgresql://... python -m pytest` (SQLite + Postgres).

## Arquitetura (orientada a objetos, em camadas)

```
helpdesk/
├── models.py        Entidades: Usuario, Chamado, Perfil (enum), StatusChamado (enum)
├── database.py      Database (abstrata) → SqliteDatabase / PostgresDatabase
├── repositories.py  UsuarioRepository, ChamadoRepository, SetorRepository (único lugar com SQL)
├── services.py      AuthService, ChamadoService (regras de negócio e validação)
├── security.py      SessaoUsuario (login/permissões por decorator) e Csrf
├── controllers.py   AuthController, ChamadoController (rotas HTTP)
├── __init__.py      HelpdeskApp: monta as dependências (injeção via construtor)
├── templates/       Telas (Jinja2)
└── static/          CSS e JS da interface
```

Cada camada só conhece a de baixo: controller → service → repository → database.
Herança e polimorfismo: `SqliteDatabase` e `PostgresDatabase` implementam a classe abstrata `Database`, e os repositórios funcionam com qualquer uma; todos os repositórios estendem `Repository`. Encapsulamento: regras como
"pode ser cancelado" ficam dentro da própria entidade `Chamado`.

## Interface

A identidade visual vem da **sinalização viária**, o mundo do nome Sinaleiro:

- **Tipografia Overpass**, derivada da *Highway Gothic*, a fonte das placas de estrada.
- **Asfalto e faixa de pista** no topo e na tela de login.
- **Botões como placas**: o azul de orientação com filete branco interno; ações destrutivas em vermelho de regulamentação.
- **Semáforo como indicador de status**, sempre com o texto ao lado (a informação não depende só da cor).
- **Etiqueta de patrimônio** desenhada como a plaqueta metálica do equipamento.
- **Logotipo**: os pingos dos dois "i" de Sinaleiro são lâmpadas.

### Movimento

- **Login**: um grupo focal realista (caixa, palas e lentes de LED) roda o ciclo verde → amarelo → vermelho. A legenda acende junto, e a faixa da pista anda no verde, freia no amarelo e para no vermelho. Ao entrar, o sinal abre no verde; com senha errada, o vermelho pisca.
- **Navegação** com View Transitions: a página troca suavemente e o marcador das abas desliza.
- **Lista**: as lâmpadas ligam com a cintilação de lâmpada real. O admin vê a cor nova antes de salvar, a linha alterada ou criada ganha destaque e o chamado cancelado sai da fila.
- **Avisos** com contagem regressiva tracejada, que pausa no hover.
- **Estado vazio** com o amarelo piscando, como semáforo de madrugada.
- Respeita `prefers-reduced-motion`. É responsiva até o celular, tem foco de teclado visível e usa CSRF em todos os formulários.
