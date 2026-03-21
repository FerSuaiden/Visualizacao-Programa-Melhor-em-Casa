# Site em Docker com Apache

Este diretorio ja esta preparado para servir o site estatico completo em Apache usando Docker.

## Estrutura importante

- `htdocs/`: arquivos do site e visualizacoes (o Apache serve esse conteudo)
- `Dockerfile`: imagem Apache que copia `htdocs` para `/usr/local/apache2/htdocs`
- `docker-compose.yml`: sobe o container mapeando a porta local (padrao `8080`) para `80` no container

## Como executar

No terminal, entre neste diretorio:

```bash
cd site/map_server
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
- Visualizacoes referenciadas nas paginas em `Outputs&Codigo/PARTE1`, `Outputs&Codigo/PARTE2` e `Outputs&Codigo/PARTE4/visualizacoes`

## Entrega para o professor

Envie a pasta `site/map_server` contendo:

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
