from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib import error, request

from user.domain import ProductGateway


class FakeStoreProductGateway(ProductGateway):
    """Gateway that validates products against fakestoreapi.com."""

    BASE_URL = "https://fakestoreapi.com/products/{product_id}"

    def exists(self, product_id: int) -> bool:
        return self.get_details(product_id) is not None

    def get_details(self, product_id: int) -> Optional[Dict[str, Any]]:
        if product_id <= 0:
            return None

        url = self.BASE_URL.format(product_id=product_id)
        req = request.Request(url, method="GET")

        try:
            with request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    return None
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise RuntimeError(f"Product service returned HTTP {exc.code}") from exc
        except error.URLError as exc:
            raise RuntimeError("Could not reach product service") from exc

        return {
            "id": payload.get("id"),
            "title": payload.get("title"),
            "image": payload.get("image"),
            "price": payload.get("price"),
            "review": payload.get("rating"),
        }
