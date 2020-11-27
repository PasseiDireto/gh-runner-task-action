FROM python:3-slim AS builder
# https://jacobtomlinson.dev/posts/2019/creating-github-actions-in-python/
ADD requirements/run.txt /app/requirements.txt
WORKDIR /app
ENV TERM "xterm-256color"
ADD action /app
RUN pip install --target=/app -r requirements.txt

FROM gcr.io/distroless/python3-debian10
COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH /app

CMD ["/app/start.py"]