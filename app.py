"""CeneoScraper — Flask web app for scraping Ceneo.pl product opinions."""

import io
import os

import pandas as pd
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from models import Product

app = Flask(__name__)
app.secret_key = "ceneo-scraper-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OPINIONS_FOLDER = os.path.join(BASE_DIR, "opinions")
os.makedirs(OPINIONS_FOLDER, exist_ok=True)


def _product_path(product_code):
    return os.path.join(OPINIONS_FOLDER, f"{product_code}.json")


def _load_product_or_404(product_code):
    path = _product_path(product_code)
    if not os.path.isfile(path):
        abort(404, description=f"No opinions stored for product '{product_code}'.")
    return Product.load_json(path)


def _export_dataframe(product):
    """Build a flat DataFrame suitable for CSV/XLSX export."""
    rows = []
    for opinion in product.opinions:
        row = opinion.to_dict()
        row["pros"] = "; ".join(row.get("pros") or [])
        row["cons"] = "; ".join(row.get("cons") or [])
        rows.append(row)
    return pd.DataFrame(rows, columns=product.opinions[0].FIELDS if product.opinions else None)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/extract", methods=["GET", "POST"])
def extract():
    if request.method == "POST":
        product_code = (request.form.get("product_code") or "").strip()

        if not product_code:
            flash("Please enter a product code.", "danger")
            return render_template("extract.html", product_code=product_code)

        try:
            product = Product.scrape(product_code)
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("extract.html", product_code=product_code)
        except Exception as exc:  # network / parsing errors
            flash(f"Could not scrape opinions: {exc}", "danger")
            return render_template("extract.html", product_code=product_code)

        product.save_json(OPINIONS_FOLDER)
        flash(
            f"Extracted {product.count} opinions for '{product.product_name}'.",
            "success",
        )
        return redirect(url_for("product", product_code=product_code))

    return render_template("extract.html", product_code="")


@app.route("/products")
def products():
    items = []
    for filename in sorted(os.listdir(OPINIONS_FOLDER)):
        if not filename.endswith(".json"):
            continue
        product = Product.load_json(os.path.join(OPINIONS_FOLDER, filename))
        items.append(
            {
                "product_code": product.product_code,
                "product_name": product.product_name,
                "count": product.count,
                "count_with_pros": product.count_with_pros,
                "count_with_cons": product.count_with_cons,
                "average_score": product.average_score,
            }
        )
    return render_template("products.html", products=items)


@app.route("/product/<product_code>")
def product(product_code):
    product = _load_product_or_404(product_code)
    return render_template("product.html", product=product)


@app.route("/product/<product_code>/charts")
def charts(product_code):
    product = _load_product_or_404(product_code)
    rec_dist = product.recommendation_distribution()
    score_dist = product.score_distribution()
    return render_template(
        "charts.html",
        product=product,
        rec_labels=list(rec_dist.keys()),
        rec_values=list(rec_dist.values()),
        score_labels=[f"{i}/5" for i in score_dist.keys()],
        score_values=list(score_dist.values()),
    )


@app.route("/product/<product_code>/download/<filetype>")
def download(product_code, filetype):
    product = _load_product_or_404(product_code)
    filetype = filetype.lower()

    if filetype == "json":
        return send_file(
            _product_path(product_code),
            mimetype="application/json",
            as_attachment=True,
            download_name=f"{product_code}.json",
        )

    if filetype == "csv":
        df = _export_dataframe(product)
        output = io.BytesIO(df.to_csv(index=False).encode("utf-8"))
        output.seek(0)
        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"{product_code}.csv",
        )

    if filetype == "xlsx":
        df = _export_dataframe(product)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"{product_code}.xlsx",
        )

    abort(404, description=f"Unsupported file type '{filetype}'.")


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", error=error), 404


if __name__ == "__main__":
    app.run(debug=True)
