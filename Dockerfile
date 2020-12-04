FROM python:3.9-alpine AS builder
# https://jacobtomlinson.dev/posts/2019/creating-github-actions-in-python/

COPY requirements/run.txt /action_workspace/run.txt

ENV TERM "xterm-256color"
RUN pip install -r /action_workspace/run.txt

COPY . /action_workspace
ENV PYTHONPATH /action_workspace

CMD ["python", "/action_workspace/action/start.py"]

