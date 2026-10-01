# 0007. A FastAPI endpoint and a plain TypeScript page, ahead of phases 7 and 8

Date: 2026-10-01
Status: accepted

## Context

The spec puts the API in phase 7 and a minimal frontend in phase 8. The
owner asked for a simple UI over strategy A now, so that retrieval can be
tried by typing rather than only from the CLI.

## Decision

- FastAPI, one route: `POST /api/search` with `{query, k}`, plus the static
  page served from `frontend/public/`.
- The query travels in the POST body, never a URL, so access logs do not
  keep what a person wrote.
- The page is TypeScript compiled by `tsc` into `frontend/public/dist/`.
  No framework and no bundler. Responses are checked at runtime before
  rendering, and all server text is set with `textContent`.
- Tests: vitest with jsdom for the frontend modules, and Playwright against
  the real app, Postgres, and corpus, with only the embedding model faked.

## Alternatives considered

**Plain JavaScript.** Fewer tools, but the owner asked for TypeScript, and
the response types are worth checking at compile time.

**React or Vite.** More tooling than one form and one list of results need.

**stdlib `http.server`.** No dependency, but more hand-written request
handling, and harder to test than FastAPI's TestClient.

## Consequences

The frontend needs Node and `npm install` for development and tests, though
not for running the API once `dist/` is built. Phase 7 now extends an
existing API rather than creating one. When strategies B and C exist, the
response's `strategy` field will need a matching request field.
