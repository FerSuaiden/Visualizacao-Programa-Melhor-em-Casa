# Site em Docker com Apache

Este diretorio esta preparado para servir o site estatico completo em Apache usando Docker.
Agora a estrutura esta autonoma: o build usa apenas arquivos dentro de map_server.

## Estrutura importante

- `htdocs/`: arquivos do site e visualizacoes servidos pelo Apache
- `Dockerfile`: imagem Apache que copia `htdocs` para `/usr/local/apache2/htdocs`
- `docker-compose.yml`: sobe o container mapeando a porta local (padrao `8080`) para `80` no container

## Como executar

No terminal, entre neste diretorio:

```bash
cd map_server
```

Suba o servidor:

```bash
docker compose up --build -d
```

Se a porta `8080` ja estiver em uso, rode com outra porta (ex.: `8081`):

```bash
HOST_PORT=8081 docker compose up --build -d
```

Abra no navegador:

- `http://localhost:8080`

Se usou `HOST_PORT=8081`, acesse:

- `http://localhost:8081`

Para parar:

```bash
docker compose down
```

## Como atualizar o site

1. Edite os arquivos em `htdocs/` (ex.: `htdocs/index.html`).
2. Rode novamente:

```bash
docker compose up --build -d
```

## Conteudo incluido para funcionar completo

Este pacote ja inclui:

- Paginas principais: `index.html`, `oferta.html`, `composicao.html`, `conformidade.html`
- Assets locais: `css/` e `js/`
- Visualizacoes referenciadas nas paginas em `Outputs&Codigo/OFERTA`, `Outputs&Codigo/COMPOSICAO` e `Outputs&Codigo/CONFORMIDADE/visualizacoes`

Observacao: a pasta `site/` nao e necessaria para subir o container. Se quiser, pode remover essa pasta e manter apenas `htdocs/`.

## Entrega para o professor

Envie a pasta `map_server` contendo:

- `Dockerfile`
- `docker-compose.yml`
- `htdocs/` (com o `index.html` e outros arquivos do site)
- `README.md`

Com isso, ele so precisa executar:

```bash
docker compose up --build -d
```

E acessar `http://localhost:8080`.

Se houver conflito de porta, ele pode usar:

```bash
HOST_PORT=8081 docker compose up --build -d
```
