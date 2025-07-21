# ────────────────────────────────────────────────────────────────
#  src/agent_generator/providers/watsonx_provider.py
# ────────────────────────────────────────────────────────────────
"""
Implementation of the IBM Watson x.ai text‑generation endpoint.

Docs:
https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/fm-api-ref.html
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

import requests
from pydantic import ValidationError

from agent_generator.config import get_settings
from agent_generator.providers.base import BaseProvider

_LOG = logging.getLogger("agentgen.provider.watsonx")


class WatsonXProvider(BaseProvider):
    """Call IBM watsonx.ai via the generative AI inference API."""

    name = "watsonx"

    # 👉 Update if IBM changes pricing; USD per 1 K tokens (prompt, completion)
    PRICING_PER_1K = (0.003, 0.015)

    def __init__(self) -> None:
        super().__init__(get_settings())

        missing = [
            env
            for env in ("watsonx_api_key", "watsonx_project_id")
            if not getattr(self.settings, env)
        ]
        if missing:
            raise ValueError(
                f"WatsonXProvider: missing required environment variable(s): {missing}"
            )

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.watsonx_api_key}",
            }
        )
        self._url = (
            f"{self.settings.watsonx_url}/ml/v1/"
            f"projects/{self.settings.watsonx_project_id}/"
            "text/generation"
        )

    # --------------------------------------------------------------------- #
    # Public
    # --------------------------------------------------------------------- #

    def generate(self, prompt: str, **kwargs) -> str:  # noqa: D401
        """
        Send the prompt to IBM WatsonX and return the completion text.

        Extra kwargs are passed through to the API body, allowing
        advanced users to tweak ``stop_sequences``, ``top_p``, etc.
        """
        body: Dict[str, Any] = {
            "model_id": self.settings.model,
            "input": prompt,
            "parameters": {
                "max_new_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                "temperature": kwargs.get("temperature", self.settings.temperature),
            },
        }
        _LOG.debug("WatsonX payload: %s", body)

        resp = self._session.post(self._url, data=json.dumps(body), timeout=60)
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:  # pragma: no cover
            _LOG.error("WatsonX error %s: %s", resp.status_code, resp.text)
            raise RuntimeError(f"WatsonX API error: {resp.text}") from exc

        try:
            data: Dict[str, Any] = resp.json()
            choices: List[Dict[str, str]] = data["results"]
            completion = choices[0]["generated_text"]
        except (KeyError, ValidationError) as exc:  # pragma: no cover
            raise RuntimeError(f"Unexpected WatsonX response: {resp.text}") from exc

        _LOG.debug("WatsonX completion: %s", completion)
        return completion
