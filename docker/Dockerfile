# syntax=docker/dockerfile:1

# ---- Stage 1: test -------------------------------------------------------
# Run the unit tests while building. If a test fails, the build fails, and no
# image is produced. Nothing from this stage ends up in the final image except
# the file we copy out of it below.
FROM python:3.13.18-slim-trixie AS test
WORKDIR /src
COPY app/ ./
RUN python -m unittest -v

# ---- Stage 2: runtime ----------------------------------------------------
# Start again from a clean base, and copy in only what the app needs to run.
FROM python:3.13.18-slim-trixie AS runtime

# Print logs straight away, and do not write .pyc files into the image.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# A dedicated user with no login shell and no home directory to speak of.
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app
# Copying from the test stage means the tests must pass before this step can run.
# The file stays owned by root, so the app cannot change its own code.
COPY --from=test /src/app.py ./app.py

# From here on, everything runs as the unprivileged user.
USER app

EXPOSE 8080

# Ask the app itself whether it is healthy. The slim image has no curl, so use Python.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8080') + '/health', timeout=2)"]

# Exec form: python is PID 1 and receives signals such as docker stop's SIGTERM.
CMD ["python", "app.py"]
