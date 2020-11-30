FROM python:3.9-alpine AS builder
# https://jacobtomlinson.dev/posts/2019/creating-github-actions-in-python/
ADD requirements/run.txt /app/requirements.txt
ADD task-params-template.json /app/task-params-template.json
WORKDIR /app
ENV TERM "xterm-256color"
RUN pip install pip --upgrade
RUN pip install --target=/app -r requirements.txt

ADD . /app

WORKDIR /app
ENV PYTHONPATH /app

CMD ["python", "/app/action/start.py"]