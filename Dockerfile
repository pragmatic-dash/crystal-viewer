FROM --platform=linux/amd64 continuumio/miniconda3:4.12.0

RUN apt-get update 
RUN apt-get install gcc python3-dev -y

RUN mkdir -p /app
ADD requirements.txt /app/requirements.txt

# Install dependencies
RUN pip3 install -r /app/requirements.txt

ADD assets/ /app/assets
RUN cp /app/assets/more.v2.css $(python -c "from crystal_toolkit.settings import SETTINGS; print(SETTINGS.ASSETS_PATH, end='')")/
ENTRYPOINT [ "gunicorn", "--bind", "0.0.0.0:50002", "-w", "4", "-t", "300", "--preload", "--chdir", "/app", "app:server" ]

ADD app.py /app/app.py
