"""Product model: scrapes, stores and summarises a product's opinions."""

import json
import os

import requests
from bs4 import BeautifulSoup

from .opinion import Opinion

HEADERS = {
    "Host": "www.ceneo.pl",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

BASE_URL = "https://www.ceneo.pl/{product_code}/opinie-{page}"

# candidate selectors for the product name (Ceneo markup varies over time)
_NAME_SELECTORS = [
    "h1.product-top__product-info__name",
    "h1.product-top__product-info__name a",
    ".product-top__product-info__name",
    "h1",
]


class Product:
    def __init__(self, product_code, product_name=None, opinions=None):
        self.product_code = str(product_code)
        self.product_name = product_name or str(product_code)
        self.opinions = opinions if opinions is not None else []

    # ------------------------------------------------------------------ scrape
    @classmethod
    def scrape(cls, product_code):
        """Scrape every opinion page for the product code.

        Returns a Product instance. Raises ValueError if no opinions exist.
        """
        product = cls(product_code)
        page = 1
        product_name = None

        while True:
            url = BASE_URL.format(product_code=product_code, page=page)
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                break

            page_dom = BeautifulSoup(response.text, "html.parser")

            if product_name is None:
                product_name = cls._extract_name(page_dom)

            for review in page_dom.select("div.js_product-review"):
                product.opinions.append(Opinion.from_dom(review))

            if page_dom.select_one("a.pagination__next") is None:
                break
            page += 1

        if not product.opinions:
            raise ValueError(
                f"No opinions found for product code '{product_code}'. "
                "Check that the code is correct and that the product has reviews."
            )

        product.product_name = product_name or str(product_code)
        return product

    @staticmethod
    def _extract_name(dom):
        for selector in _NAME_SELECTORS:
            el = dom.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return None

    # ------------------------------------------------------------- persistence
    def json_path(self, folder):
        return os.path.join(folder, f"{self.product_code}.json")

    def save_json(self, folder):
        os.makedirs(folder, exist_ok=True)
        path = self.json_path(folder)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def load_json(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        opinions = [Opinion.from_dict(o) for o in (data if isinstance(data, list) else data.get("opinions", []))]
        return cls(
            product_code=data.get("product_code") if isinstance(data, dict) else None,
            product_name=data.get("product_name") if isinstance(data, dict) else None,
            opinions=opinions,
        )

    def to_dict(self):
        return {
            "product_code": self.product_code,
            "product_name": self.product_name,
            "opinions": [o.to_dict() for o in self.opinions],
        }

    def opinions_as_dicts(self):
        return [o.to_dict() for o in self.opinions]

    # ------------------------------------------------------------------- stats
    @property
    def count(self):
        return len(self.opinions)

    @property
    def count_with_pros(self):
        return sum(1 for o in self.opinions if o.pros)

    @property
    def count_with_cons(self):
        return sum(1 for o in self.opinions if o.cons)

    @property
    def average_score(self):
        values = [o.score_value() for o in self.opinions]
        values = [v for v in values if v is not None]
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    def recommendation_distribution(self):
        """Counts for Polecam / Nie polecam / None (no recommendation)."""
        dist = {"Polecam": 0, "Nie polecam": 0, "None": 0}
        for o in self.opinions:
            rec = (o.recommendation or "").strip().lower()
            if rec == "polecam":
                dist["Polecam"] += 1
            elif rec == "nie polecam":
                dist["Nie polecam"] += 1
            else:
                dist["None"] += 1
        return dist

    def score_distribution(self):
        """Counts of opinions for each whole star rating 1..5."""
        dist = {i: 0 for i in range(1, 6)}
        for o in self.opinions:
            value = o.score_value()
            if value is None:
                continue
            star = int(round(value))
            if star in dist:
                dist[star] += 1
        return dist
