# src/agent_generator/integrations/matrix_connector.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    # SDK from the uploaded zip (matrix_python_sdk)
    from matrix_sdk.client import Client as MatrixClient
except Exception:
    MatrixClient = None  # graceful degradation


class _SimpleObj:
    """Tiny helper so planner can do a.name / t.name, t.kind, t.entrypoint..."""

    def __init__(self, **fields: Any) -> None:
        self.__dict__.update(fields)


class MatrixConnector:
    """
    Thin wrapper over matrix_sdk.Client.

    Reads config from environment:
      - MATRIX_URL (or MATRIX_BASE_URL)
      - MATRIX_TOKEN (or MATRIX_API_TOKEN)

    Methods used by the planner:
      - healthy() -> bool
      - list_agents(query: str) -> list of objects with .name
      - list_tools(query: str)  -> list of objects with .name, .kind, .description, .entrypoint
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = 8.0,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("MATRIX_URL") or os.getenv("MATRIX_BASE_URL") or ""
        ).strip()
        self.token = (
            token or os.getenv("MATRIX_TOKEN") or os.getenv("MATRIX_API_TOKEN") or ""
        ).strip()
        self.timeout = timeout

        self._client = None
        if MatrixClient and self.base_url and self.token:
            try:
                self._client = MatrixClient(
                    base_url=self.base_url, token=self.token, timeout=self.timeout
                )
            except Exception:
                # Leave _client as None → healthy() becomes False and planner will fall back
                self._client = None

    # --- lifecycle / health ---------------------------------------------------

    def healthy(self) -> bool:
        """True if SDK is available and credentials look usable."""
        return self._client is not None

    # --- discovery ------------------------------------------------------------

    def _search(
        self, *, q: str, type_: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Internal unified search. Returns a list of dict-like items whether the SDK
        gives typed models (with .items) or plain dicts (with ['items']).
        """
        if not self.healthy():
            return []
        resp = self._client.search(
            q=q or "*", type=type_, limit=limit
        )  # SDK returns typed or dict
        items = getattr(resp, "items", None) or (
            resp.get("items", []) if isinstance(resp, dict) else []
        )
        return items or []

    def list_agents(self, *, query: str = "", limit: int = 10) -> List[_SimpleObj]:
        items = self._search(q=query, type_="agent", limit=limit)
        out: List[_SimpleObj] = []
        for it in items:
            # typed object or dict
            name = getattr(it, "name", None) or (
                it.get("name") if isinstance(it, dict) else None
            )
            if name:
                out.append(_SimpleObj(name=name))
        return out

    def list_tools(self, *, query: str = "", limit: int = 10) -> List[_SimpleObj]:
        items = self._search(q=query, type_="tool", limit=limit)
        out: List[_SimpleObj] = []
        for it in items:
            name = getattr(it, "name", None) or (
                it.get("name") if isinstance(it, dict) else None
            )
            kind = getattr(it, "kind", None) or (
                it.get("kind") if isinstance(it, dict) else None
            )
            desc = getattr(it, "description", None) or (
                it.get("description") if isinstance(it, dict) else None
            )
            entry = getattr(it, "entrypoint", None) or (
                it.get("entrypoint") if isinstance(it, dict) else None
            )
            if name:
                out.append(
                    _SimpleObj(name=name, kind=kind, description=desc, entrypoint=entry)
                )
        return out
