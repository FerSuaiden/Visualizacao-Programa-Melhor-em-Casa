# Visualizacao do Programa Melhor em Casa

Este diretorio contem o site estatico e os arquivos de infraestrutura
necessarios para servi-lo com Apache em Docker. A estrutura e autonoma: o
build usa apenas os arquivos dentro de `map_server`.

## Estrutura importante

- `htdocs/`: arquivos do site e visualizacoes servidos pelo Apache
- `Dockerfile`: imagem Apache que copia `htdocs` para `/usr/local/apache2/htdocs`
- `docker-compose.yml`: sobe o container mapeando a porta local (padrao `8080`) para `80` no container
- `scripts/deploy.sh`: script auxiliar para build e push da imagem Docker no registry configurado

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

## Atualizacao do site

1. Edite os arquivos em `htdocs/` (ex.: `htdocs/index.html`).
2. Reconstrua e suba o container:

```bash
docker compose up --build -d
```

## Conteudo incluido

O diretorio `htdocs/` inclui:

- Paginas principais: `index.html`, `oferta.html`, `composicao.html`, `conformidade.html`
- Assets locais: `css/` e `js/`
- Visualizacoes referenciadas nas paginas em `Outputs&Codigo/OFERTA`, `Outputs&Codigo/COMPOSICAO` e `Outputs&Codigo/CONFORMIDADE/visualizacoes`

## Distribuicao

Para executar o projeto em outra maquina, mantenha os arquivos versionados de
`map_server` e rode:

```bash
docker compose up --build -d
```

O site fica disponivel em `http://localhost:8080`. Se houver conflito de porta,
defina outra porta local:

```bash
HOST_PORT=8081 docker compose up --build -d
```

## Deploy - servidor 10.4.0.21 (USP/C4AI)

1. Conecte-se a VPN.
2. Gere e publique a imagem:

```bash
sh scripts/deploy.sh
```

3. Acesse o servidor:

```bash
ssh <usuario>@10.4.0.21
```

4. Entre no diretorio do projeto:

```bash
cd /etc/visualizacao-programa-melhor-em-casa
```

5. Suba o container:

```bash
docker compose up -d
```
