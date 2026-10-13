# EventTech — Sistema de Gestão de Eventos

## Equipe

- Sophia Silveira dos Santos — RM 571932
- Renato da Silva Tenorio — RM 572928
- Renato Ruiz Ferreira Fonseca Scolamieri — RM 568667
- Matheus Ferreira Antônio — RM 570933
- João Vitor Cruz de Lima — RM 571277

## Objetivo e tecnologias

Cadastrar, listar, consultar, alterar e excluir eventos pelo navegador, usando
Python, POO, Flask, Oracle, oracledb, HTML, CSS, Jinja, requests e JSON.
A entidade, o DAO e os enums da equipe foram mantidos e ligados às telas.

## Como executar

Use Python 3.10 ou mais recente. No Windows, execute `INICIAR.bat` nesta pasta.
Ele prepara o ambiente isolado e, se faltar, cria o `.env` a partir do exemplo.
Preencha `ORACLE_USER` e `ORACLE_PASSWORD` no seu `.env`, com a sua conta Oracle.
Não envie esse arquivo para o GitHub nem compartilhe a senha.

Se a senha que estava no código anterior era real, troque-a no Oracle:
remover do arquivo atual não remove o valor do histórico antigo do Git.

Se a tabela EVENTOS ainda não existe, execute `script.sql` na sua conta Oracle.
Não execute esse script novamente sobre uma tabela já existente.
Depois abra [http://127.0.0.1:5000](http://127.0.0.1:5000).
O servidor fica ligado enquanto o terminal estiver aberto; `Ctrl+C` encerra.

Pelo terminal, os mesmos passos são:

```bat
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\python eventtech\App.py
```

O `copy` é necessário só se o `.env` ainda não existir. Edite-o antes de usar o banco.
A página inicial funciona sem Oracle; as operações de dados exigem a conexão configurada.
Reinicie o servidor depois de preencher ou alterar o `.env`.
Este é um servidor local de atividade, não uma implantação pública.

## Uso do sistema

- Listar eventos e consultar um ID na página de eventos.
- Cadastrar um ID novo e os demais campos obrigatórios.
- Editar preservando o ID e a data de cadastro.
- Excluir somente depois de conferir os dados e confirmar; Cancelar mantém o registro.
- Baixar `eventtech.json` e `eventtech.html` na listagem. Os dois consultam os dados atuais, não uma lista fixa.
- `/api/eventos` também disponibiliza os eventos em JSON.

O HTML exportado contém o CSS e pode ser aberto sem o servidor.
Para a entrega, gere os arquivos usando o Oracle real e salve-os junto às evidências.
Os arquivos exportados ficam ignorados no Git para não publicar dados acidentalmente.

## API utilizada

[ViaCEP](https://viacep.com.br/) — GET `https://viacep.com.br/ws/{cep}/json/`.
O parâmetro é um CEP brasileiro com 8 dígitos. O retorno JSON traz CEP,
logradouro, bairro, localidade e UF. A consulta usa timeout de 8 segundos
com tratamento de formato inválido, CEP inexistente, HTTP, JSON e indisponibilidade.
O botão Buscar CEP preenche o local do evento; o CEP é opcional e não cria campo novo no banco.
Se a API falhar, o local pode ser preenchido manualmente.

## Estrutura

```text
eventtech/
  App.py                   Rotas Flask e validações
  entity/Evento.py         Objeto que representa o evento
  dao/ConnectionFactory.py Conexão configurada pelo .env
  dao/EventoDAO.py          SQL com binds e transações
  enums/                   Categorias e status
  services/EnderecoAPI.py   Consulta ViaCEP
  templates/               Páginas HTML/Jinja
  static/                  CSS e JavaScript do CEP
tests/                     Testes sem acessar o Oracle real
script.sql                 Estrutura EVENTOS do enunciado
requirements.txt           Bibliotecas do projeto
INICIAR.bat                Inicialização no Windows
```

## Testes e uso de IA

Execute `.venv\Scripts\python -m unittest discover -s tests -v`.
Os testes usam dados de teste e requisições simuladas, sem inserir ou excluir
registros de vocês. A validação final deve repetir os cenários do enunciado no
Oracle real: três cadastros, ID duplicado, consulta, alteração, exclusão confirmada
ou cancelada e atualização dos arquivos HTML/JSON.

A assistência de IA e a contribuição anterior de Copilot estão registradas em
`REGISTRO_IA.md`. A equipe deve revisar, adaptar e saber explicar as rotas,
formulários, objeto Evento, consultas SQL e tratamento de erros antes da entrega.

### Verificação desta continuação em 13/10/2026

24 testes automáticos passaram com Oracle e requisições simulados.
Também foram conferidos os formulários, cadastro/edição/exclusão/cancelamento e
downloads no navegador com dados fictícios, no computador e em largura de celular.
A consulta pública real de CEP retornou HTTP 200 e preencheu o local do evento.
O Oracle real e a existência da tabela na conta da equipe ainda precisam ser
conferidos pela equipe após configurar o `.env`; esses testes não foram declarados como feitos.
