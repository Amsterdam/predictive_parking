FROM python:3.5
MAINTAINER datapunt.ois@amsterdam.nl

ENV PYTHONUNBUFFERED 1

EXPOSE 8080

RUN apt-get update \
	&& apt-get install -y \
		gdal-bin \
		libgeos-dev \
		unrar \
		unzip \
		netcat \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
	&& adduser --system datapunt \
	&& mkdir -p /static \
	&& chown datapunt /static \
	&& pip install uwsgi

WORKDIR /app/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

VOLUME /app/diva/
ENV DJANGO_SETTINGS_MODULE=predictive_parking.settings

USER datapunt
COPY bag /app/
CMD /app/docker-entrypoint.sh
