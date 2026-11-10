# Debian Trixie (not Alpine). 3.12.16 includes the Oct 2026 CPython
# security fixes (CVE-2026-115557, CVE-2026-114583, bundled Expat 2.9.0).
FROM python:3.12.16-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip setuptools \
    && pip install -r requirements.txt

COPY main.py ./

EXPOSE 8000

CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
