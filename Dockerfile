# Reproducible CPU image of the benchmark. Models are downloaded at run time
# into the hf-cache volume, never baked into the image.
FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/cache/huggingface \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY docker/constraints.txt docker/constraints.txt
RUN pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install -c docker/constraints.txt ".[tools]" \
    && pip install --no-deps rebuff==0.1.1 \
    && pip install \
       https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl \
       https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.8.0/fr_core_news_sm-3.8.0-py3-none-any.whl

RUN useradd --create-home bench && mkdir -p /cache && chown -R bench /app /cache
USER bench

ENTRYPOINT ["python", "-m", "guardbench"]
CMD ["--help"]
