"""Opinion model: represents a single Ceneo.pl product review."""


def _text(dom, selector):
    """Return stripped text of the first matching element, or None."""
    el = dom.select_one(selector)
    return el.get_text(strip=True) if el else None


def _attr(dom, selector, attribute):
    """Return an attribute of the first matching element, or None."""
    el = dom.select_one(selector)
    if el and el.has_attr(attribute):
        return el[attribute]
    return None


def _text_list(dom, selector):
    """Return a list of stripped texts for all matching elements."""
    return [el.get_text(strip=True) for el in dom.select(selector)]


# selector for the two <time> elements inside the "published" span
_TIME_SELECTOR = "span.user-post__published > time"


class Opinion:
    # field order is reused for table columns and DataFrame export
    FIELDS = [
        "opinion_id",
        "author",
        "recommendation",
        "score",
        "content",
        "pros",
        "cons",
        "helpful",
        "unhelpful",
        "publish_date",
        "purchase_date",
    ]

    def __init__(
        self,
        opinion_id=None,
        author=None,
        recommendation=None,
        score=None,
        content=None,
        pros=None,
        cons=None,
        helpful=None,
        unhelpful=None,
        publish_date=None,
        purchase_date=None,
    ):
        self.opinion_id = opinion_id
        self.author = author
        self.recommendation = recommendation
        self.score = score
        self.content = content
        self.pros = pros if pros is not None else []
        self.cons = cons if cons is not None else []
        self.helpful = helpful
        self.unhelpful = unhelpful
        self.publish_date = publish_date
        self.purchase_date = purchase_date

    @classmethod
    def from_dom(cls, dom):
        """Build an Opinion from a single review's BeautifulSoup element."""
        times = dom.select(_TIME_SELECTOR)
        publish_date = times[0]["datetime"] if len(times) > 0 and times[0].has_attr("datetime") else None
        purchase_date = times[1]["datetime"] if len(times) > 1 and times[1].has_attr("datetime") else None

        return cls(
            opinion_id=dom["data-entry-id"] if dom.has_attr("data-entry-id") else None,
            author=_text(dom, "span.user-post__author-name"),
            recommendation=_text(dom, "span.user-post__author-recomendation > em"),
            score=_text(dom, "span.user-post__score-count"),
            content=_text(dom, "div.user-post__text"),
            pros=_text_list(dom, "div.review-feature__item--positive"),
            cons=_text_list(dom, "div.review-feature__item--negative"),
            helpful=_text(dom, "button.vote-yes > span"),
            unhelpful=_text(dom, "button.vote-no > span"),
            publish_date=publish_date,
            purchase_date=purchase_date,
        )

    def score_value(self):
        """Parse a score like '4/5' or '4,5/5' into a float, or None."""
        if not self.score:
            return None
        try:
            numerator = self.score.split("/")[0].strip().replace(",", ".")
            return float(numerator)
        except (ValueError, IndexError):
            return None

    def to_dict(self):
        return {field: getattr(self, field) for field in self.FIELDS}

    @classmethod
    def from_dict(cls, data):
        return cls(**{field: data.get(field) for field in cls.FIELDS})
