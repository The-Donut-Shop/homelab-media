# yt-dlp runner (see runner.py). Same yt-dlp release as the Aurral image, plus
# node, which yt-dlp needs to solve YouTube's player challenges.
FROM node:24.22.1-trixie-slim AS node

FROM python:3.13.17-slim-trixie
COPY --from=node /usr/local/bin/node /usr/local/bin/node
RUN apt-get update \
 && apt-get install -y --no-install-recommends libstdc++6 \
 && rm -rf /var/lib/apt/lists/* \
 && node --version \
 && pip install --no-cache-dir "yt-dlp[default]==2026.10.26" \
 && yt-dlp --version \
 && useradd --uid 1000 --create-home runner \
 && install -d -o runner -g runner /cache
COPY runner.py /usr/local/bin/runner.py

USER runner
# yt-dlp keeps YouTube's player code here, which saves a download on every lookup.
ENV XDG_CACHE_HOME=/cache PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 8291
CMD ["python3", "/usr/local/bin/runner.py"]
