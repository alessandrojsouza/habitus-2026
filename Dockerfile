FROM python:3.12

WORKDIR /usr/src/python/app

# Copia os requisitos e instala (otimizando cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Cria a pasta do banco e dá permissão ao script
RUN mkdir -p /usr/src/python/app/devadmin/data

COPY . .

RUN chmod +x /usr/src/python/app/entrypoint.sh
RUN chown -R root:root /usr/src/python/app/devadmin/data

EXPOSE 8000

# O ENTRYPOINT roda sempre, o CMD vira o argumento do entrypoint
ENTRYPOINT ["/usr/src/python/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]