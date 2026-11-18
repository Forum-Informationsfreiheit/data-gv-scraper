import httpx
from typing import Any, Dict, Optional

import time
class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=20.0)

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        request = httpx.Request(
            method=method,
            url=f"{self.base_url}{path}",
            params=params,
            json=json,
            headers=headers,
        )

        max_retries = 10
        retry_count = 0
        backoff = 2

        while retry_count < max_retries:
            response = self.client.send(request)

            if response.status_code == 500 and "search.max_open_scroll_context" in response.content.decode():
                retry_count += 1
                wait_time = backoff * retry_count
                print(f"Scroll context limit hit, waiting {wait_time}s before retry {retry_count}/{max_retries}")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response

        raise Exception(f"Failed after {max_retries} retries due to scroll context limit")

    def get(self, path: str, **kwargs) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> httpx.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    def patch(self, path: str, **kwargs) -> httpx.Response:
        return self.request("PATCH", path, **kwargs)
