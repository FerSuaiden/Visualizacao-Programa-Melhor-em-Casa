FROM httpd:2.4-alpine

# Remove o index padrao do Apache e copia apenas conteudo local de htdocs.
RUN rm -rf /usr/local/apache2/htdocs/*
COPY ./htdocs/ /usr/local/apache2/htdocs/

EXPOSE 80