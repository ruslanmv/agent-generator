"""Audit + request-id middleware.

For every request:

- Assigns a request id (UUID v4 if the client didn't send X-Request-Id)
  and echoes it back in the response header so logs from the SPA, the
  backend, and OTel traces can be stitched together.
- Logs a structured access line via ``structlog``.
- Persists an AuditEvent row for mutating methods on ``/api/*`` so
  admins can audit changes.

Health / static endpoints are not audited to keep the table tight.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.db.models.audit import AuditEvent
from app.db.session import get_sessionmaker
from app.security.deps import SESSION_COOKIE_NAME
from app.security.jwt import TokenError, decode_token

REQUEST_ID_HEADER = "X-Request-Id"
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_SKIP_PATHS = ("/livez", "/readyz", "/healthz", "/docs", "/openapi.json", "/redoc")

log = structlog.get_logger("http")


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        response.headers[REQUEST_ID_HEADER] = request_id

        log.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        await self._maybe_audit(request, response, request_id)
        structlog.contextvars.clear_contextvars()
        return response

    async def _maybe_audit(
        self, request: Request, response: Response, request_id: str
    ) -> None:
        if request.method not in _MUTATING_METHODS:
            return
        if not request.url.path.startswith("/api/"):
            return
        if any(request.url.path.startswith(p) for p in _SKIP_PATHS):
            return

        actor_id, actor_username = self._resolve_actor(request)

        Session = get_sessionmaker()  # noqa: N806
        try:
            async with Session() as session:
                session.add(
                    AuditEvent(
                        actor_id=actor_id,
                        actor_username=actor_username,
                        method=request.method,
                        path=request.url.path,
                        status_code=response.status_code,
                        request_id=request_id,
                        ip=self._client_ip(request),
                        user_agent=request.headers.get("user-agent"),
                    )
                )
                await session.commit()
        except Exception:  # pragma: no cover - audit must not break requests
            log.exception("audit.write_failed", path=request.url.path)

    @staticmethod
    def _resolve_actor(request: Request) -> tuple[str | None, str | None]:
        auth = request.headers.get("authorization")
        token: str | None = None
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
        else:
            token = request.cookies.get(SESSION_COOKIE_NAME)
        if not token:
            return None, None
        try:
            payload = decode_token(token, expected_typ="access")
        except TokenError:
            return None, None
        return payload.get("sub"), payload.get("username")

    @staticmethod
    def _client_ip(request: Request) -> str | None:
        # Honour the reverse-proxy chain when set; otherwise fall back
        # to the direct peer. The Helm chart sets `trust_forwarded`
        # only when behind a known load balancer.
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        if request.client is None:
            return None
        return request.client.host
