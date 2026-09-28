# app.py (minimal, just to test the schema)
from flask import Flask
from models import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///recon.db"
db.init_app(app)

with app.app_context():
    db.create_all()
    print("Tables created successfully")
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Transaction, SaleRecord
from parser import load_statement, load_sales_record
from matcher import exact_match, fuzzy_match, summarize
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///recon.db"
app.config["SECRET_KEY"] = "dev-only-change-this"
app.config["UPLOAD_FOLDER"] = "uploads"
db.init_app(app)

@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        statement_file = request.files.get("statement")
        sales_file = request.files.get("sales")

        if not statement_file or not sales_file:
            flash("Please upload both files.")
            return redirect(url_for("upload"))

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        statement_path = os.path.join(app.config["UPLOAD_FOLDER"], statement_file.filename)
        sales_path = os.path.join(app.config["UPLOAD_FOLDER"], sales_file.filename)
        statement_file.save(statement_path)
        sales_file.save(sales_path)

        try:
            transactions_df = load_statement(statement_path)
            sales_df = load_sales_record(sales_path)
        except ValueError as e:
            flash(f"Error processing files: {e}")
            return redirect(url_for("upload"))

        exact_pairs, unmatched_txns, unmatched_sales = exact_match(transactions_df, sales_df)
        fuzzy_pairs = fuzzy_match(unmatched_txns, unmatched_sales)

        # Remove fuzzy-matched rows from the "still unmatched" sets for accurate summary
        fuzzy_txn_ids = {t for t, s, c in fuzzy_pairs}
        fuzzy_sale_ids = {s for t, s, c in fuzzy_pairs}
        still_unmatched_txns = unmatched_txns[~unmatched_txns.index.isin(fuzzy_txn_ids)]
        still_unmatched_sales = unmatched_sales[~unmatched_sales.index.isin(fuzzy_sale_ids)]

        summary = summarize(transactions_df, exact_pairs, fuzzy_pairs, still_unmatched_txns, still_unmatched_sales)

        return render_template(
            "dashboard.html",
            summary=summary,
            unmatched_txns=still_unmatched_txns.to_dict("records"),
            unmatched_sales=still_unmatched_sales.to_dict("records"),
        )

    return render_template("upload.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0")