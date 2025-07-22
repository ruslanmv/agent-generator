# ────────────────────────────────────────────────────────────────
#  src/agent_generator/providers/watsonx_provider.py
# ────────────────────────────────────────────────────────────────
"""
Implementation of the IBM watsonx.ai text‑generation REST API.
"""

from __future__ import annotations

import json
import logging
from typing import Any, ClassVar, Dict, List, Optional

import requests
from pydantic import ValidationError

from agent_generator.config import Settings
from agent_generator.providers.base import BaseProvider

_LOG = logging.getLogger("agentgen.provider.watsonx")


class WatsonXProvider(BaseProvider):
    """
    Call IBM watsonx.ai via the foundation model inference REST API.
    """

    name = "watsonx"
    PRICING_PER_1K = (0.003, 0.015)  # USD per 1K tokens

    # Use a fixed version date matching the docs example (must be kept up-to-date)
    API_VERSION: ClassVar[str] = "2025-02-11"

    # IAM token endpoint (global)
    IAM_TOKEN_URL: ClassVar[str] = "https://iam.cloud.ibm.com/identity/token"

    def __init__(self, settings: Optional[Settings] = None) -> None:
        super().__init__(settings)

        # Ensure credentials
        missing = [
            field
            for field in ("watsonx_api_key", "watsonx_project_id")
            if not getattr(self.settings, field)
        ]
        if missing:
            raise ValueError(
                f"WatsonXProvider: missing required credential(s): {missing}"
            )

        # Prepare HTTP session without Authorization header for now
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # Endpoint URL (version as query param)
        self._url = (
            f"{self.settings.watsonx_url}/ml/v1/text/generation"
            f"?version={self.API_VERSION}"
        )

    def _get_iam_token(self) -> str:
        """
        Exchange the long‑lived API key for a short‑lived IAM access token.
        """
        payload = {
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": self.settings.watsonx_api_key,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.post(
            self.IAM_TOKEN_URL,
            data=payload,
            headers=headers,
            timeout=10,
        )
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            _LOG.error("Failed to fetch IAM token %s: %s", resp.status_code, resp.text)
            raise RuntimeError("Unable to retrieve IAM token") from exc

        token = resp.json().get("access_token")
        if not token:
            raise RuntimeError(
                f"IAM response did not include access_token: {resp.text}"
            )
        return token

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Send the prompt to IBM watsonx.ai and return the generated text.
        """
        # 1) Fetch a fresh IAM token and set it on the session
        iam_token = self._get_iam_token()
        self._session.headers["Authorization"] = f"Bearer {iam_token}"

        # 2) Build payload
        body: Dict[str, Any] = {
            "project_id": self.settings.watsonx_project_id,
            "model_id": self.settings.model,
            "input": prompt,
            "parameters": {
                "max_new_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                "temperature": kwargs.get("temperature", self.settings.temperature),
            },
        }
        _LOG.debug("WatsonX payload: %s", body)

        # 3) Call the text‑generation endpoint
        resp = self._session.post(self._url, data=json.dumps(body), timeout=300)
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            _LOG.error("WatsonX error %s: %s", resp.status_code, resp.text)
            raise RuntimeError(f"WatsonX API error: {resp.text}") from exc

        # 4) Parse out the generated text
        try:
            data: Dict[str, Any] = resp.json()
            choices: List[Dict[str, str]] = data["results"]
            return choices[0]["generated_text"]
        except (KeyError, ValidationError) as exc:
            raise RuntimeError(f"Unexpected WatsonX response: {resp.text}") from exc

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Use BaseProvider for cost unless IBM updates pricing significantly.
        """
        return super().estimate_cost(prompt_tokens, completion_tokens)
