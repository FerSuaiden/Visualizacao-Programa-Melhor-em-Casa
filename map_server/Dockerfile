FROM httpd:2.4-alpine

# Remove o index padrão do Apache e copia os meus arquivos
RUN rm -rf /usr/local/apache2/htdocs/*
COPY ./htdocs/ /usr/local/apache2/htdocs/

EXPOSE 80