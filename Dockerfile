FROM python:3.12

WORKDIR /usr/src/python/app

# Copia os requisitos e instala (otimizando cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Cria a pasta do banco e dá permissão ao script
RUN mkdir -p /usr/src/python/app/devadmin/data
RUN mkdir -p /usr/src/python/app/devadmin/media

COPY . .

RUN chmod +x /usr/src/python/app/entrypoint.sh
RUN chown -R root:root /usr/src/python/app/devadmin/data
RUN chown -R root:root /usr/src/python/app/devadmin/media

EXPOSE 8000

# Usa exec com wrapper para passar CMD como argumentos ($@)
ENTRYPOINT ["/bin/bash", "-c", "exec /usr/src/python/app/entrypoint.sh \"$@\"", "--"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]