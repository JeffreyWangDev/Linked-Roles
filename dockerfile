FROM tiangolo/uwsgi-nginx-flask:python3.11
MAINTAINER CosmicCrow, <cosmiccrow@farmingcouncil.com>

EXPOSE 80 443 1121


copy . /app
copy requirements.txt requirements.txt
RUN pip install -r requirements.txt