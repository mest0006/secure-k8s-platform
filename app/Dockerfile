# Distroless runtime: no shell, no package manager, runs as non-root (uid 65532).
# The app is standard-library Python, so there is nothing to pip install.
# CI builds this image, scans it with Trivy, and deploys it by digest
# (never by a mutable tag) so every environment runs exactly what was scanned.
FROM gcr.io/distroless/python3-debian12:nonroot

WORKDIR /app
COPY --chown=65532:65532 src/server.py /app/server.py

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

EXPOSE 8080
USER 65532:65532

ENTRYPOINT ["python3", "/app/server.py"]
