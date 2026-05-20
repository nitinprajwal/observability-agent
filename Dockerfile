# ─────────────────────────────────────────────────────────────────────────────
# observability-agent — Custom Image
# Contains:
#   - OpenTelemetry Collector Contrib  (ports 4317 gRPC, 4318 HTTP, 8888 metrics)
#   - React/Vite observability SPA     (served by nginx on port 8080)
#   - nginx reverse proxy
#   - supervisord process manager
#
# Multi-arch: builds for linux/amd64 and linux/arm64.
# Build: docker buildx build --platform linux/amd64,linux/arm64 -t observability-agent .
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build the React SPA ─────────────────────────────────────────────
FROM node:22-slim AS spa-builder

WORKDIR /build

COPY observability-app/package*.json ./
RUN npm ci --ignore-scripts

COPY observability-app/ .
RUN npm run build

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM debian:bookworm-slim AS runner

# TARGETARCH is set automatically by docker buildx: "amd64" or "arm64"
ARG TARGETARCH=amd64

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx supervisor curl ca-certificates gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Download OTel Collector Contrib binary — correct arch for the build platform.
# Using otelcol-contrib which includes all receivers/processors/exporters
# including the transform processor needed for log level enrichment.
ARG OTELCOL_VERSION=0.127.0
RUN ARCH="${TARGETARCH}" && \
    curl -fsSL \
    "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v${OTELCOL_VERSION}/otelcol-contrib_${OTELCOL_VERSION}_linux_${ARCH}.tar.gz" \
    -o /tmp/otelcol.tar.gz \
    && tar -xzf /tmp/otelcol.tar.gz -C /usr/local/bin otelcol-contrib \
    && rm /tmp/otelcol.tar.gz \
    && chmod +x /usr/local/bin/otelcol-contrib

# Copy built SPA
COPY --from=spa-builder /build/dist /usr/share/nginx/html

# Copy configs
COPY otel-collector-config.yaml /etc/otelcol/config.yaml
COPY nginx.conf /etc/nginx/sites-available/default
COPY supervisord.conf /etc/supervisor/conf.d/observability.conf
COPY start-nginx.sh /usr/local/bin/start-nginx.sh

# Runtime dirs — /tmp is always writable; /var/lib/otelcol for OTel state
RUN mkdir -p /var/log/supervisor /var/lib/otelcol /tmp/supervisor /etc/nginx/sites-enabled \
    && chmod +x /usr/local/bin/start-nginx.sh

# Expose ports:
#   8080 → nginx (SPA + health + proxy to backends)
#   4317 → OTel Collector gRPC  (OTLP gRPC receiver)
#   4318 → OTel Collector HTTP  (OTLP HTTP receiver)
#   8888 → OTel Collector internal metrics (scraped by Prometheus)
#   8889 → OTel Collector Prometheus exporter (metrics pull)
EXPOSE 8080 4317 4318 8888 8889

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/observability.conf"]
