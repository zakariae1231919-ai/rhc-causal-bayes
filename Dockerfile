FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
# 1) dépendances d'abord : cette couche reste en cache tant que le lock ne change pas
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
# 2) le code ensuite : modifié souvent, reconstruit vite
COPY . .
RUN uv sync --frozen --no-dev
EXPOSE 7860
CMD ["uv", "run", "streamlit", "run", "app/app.py", "--server.port=7860", "--server.address=0.0.0.0"]
