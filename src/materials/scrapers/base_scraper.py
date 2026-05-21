import logging
import time

import requests

# Default delay between requests (seconds) to avoid being blocked
REQUEST_DELAY = 1.0
# Default retry settings
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # exponential backoff factor


class BaseScraper:
    """Base class for all material scrapers."""

    name: str = ""
    description: str = ""

    def __init__(self):
        self._request_delay = REQUEST_DELAY
        self._max_retries = MAX_RETRIES
        self._last_request_time = 0.0

    def _throttled_get(self, url: str, timeout: int = 15, headers: dict | None = None, **kwargs) -> requests.Response:
        """Make a GET request with rate limiting and retry with exponential backoff."""
        # Enforce minimum delay between requests
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self._request_delay:
            time.sleep(self._request_delay - elapsed)

        last_exc = None
        for attempt in range(self._max_retries):
            try:
                self._last_request_time = time.monotonic()
                resp = requests.get(url, timeout=timeout, headers=headers, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                last_exc = e
                if attempt < self._max_retries - 1:
                    wait = RETRY_BACKOFF ** attempt
                    logging.warning(
                        "%s: request failed (attempt %d/%d), retrying in %.1fs: %s",
                        self.name or type(self).__name__, attempt + 1, self._max_retries, wait, e,
                    )
                    time.sleep(wait)
        raise last_exc  # type: ignore[misc]

    def fetch(self) -> list[dict]:
        """Fetch materials. Must be implemented by subclasses."""
        raise NotImplementedError

    def is_available(self) -> bool:
        """Check if the data source is reachable."""
        try:
            resp = requests.head(self.BASE_URL, timeout=10)  # type: ignore[attr-defined]
            return resp.status_code < 400
        except requests.RequestException:
            return False
