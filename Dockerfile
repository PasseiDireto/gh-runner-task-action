FROM python:3.9-alpine AS builder
# https://jacobtomlinson.dev/posts/2019/creating-github-actions-in-python/
ADD requirements/run.txt /app/requirements.txt
ADD task-params-template.json /app/task-params-template.json
WORKDIR /app
ENV TERM "xterm-256color"
RUN pip install --target=/app -r requirements.txt

ADD action /app

#FROM gcr.io/distroless/python3-debian10:3.9
#COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH /app

CMD ["python", "/app/start.py"]