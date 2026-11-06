# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm AS deps
WORKDIR /app

# The harness is stdlib-only; no runtime dependencies to install.
COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY PRODUCT_COMPARATOR_V13.json ./
COPY README.md ./

FROM python:3.12-slim-bookworm AS runner
WORKDIR /app

RUN addgroup --system --gid 1001 appuser \
    && adduser --system --uid 1001 appuser

COPY --from=deps /app/scripts ./scripts
COPY --from=deps /app/tests ./tests
COPY --from=deps /app/PRODUCT_COMPARATOR_V13.json .
COPY --from=deps /app/README.md .

USER appuser

CMD ["python", "scripts/validate_agent.py", "--strict", "--no-readme"]
