from pathlib import Path
import sqlite3

from flask import Flask, render_template

app = Flask(__name__)

# Finds the folder where app.py is stored.
BASE_DIR = Path(__file__).resolve().parent

# Connects to the database inside the database folder.
DATABASE_PATH = BASE_DIR / "database" / "road_accidents.db"


def get_db_connection():
    """Create and return a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/")
def home():
    """Display the landing page."""
    return render_template("index.html")


@app.route("/conditions")
def conditions():
    """Display the Level 2 crash-conditions summary page."""

    connection = get_db_connection()

    results = connection.execute(
        """
        SELECT
            ac.ATMOSPH_COND_DESC AS ATMOSPHERIC_CONDITION,
            lc.COND_NAME AS LIGHT_CONDITION,
            rsc.SURFACE_COND_DESC AS ROAD_SURFACE,
            COUNT(DISTINCT a.ACCIDENT_NO) AS TOTAL_CRASHES
        FROM Accident AS a
        JOIN Light_Condition AS lc
            ON a.LIGHT_CONDITION = lc.COND_ID
        JOIN Atmospheric_Cond_Seq AS acs
            ON a.ACCIDENT_NO = acs.ACCIDENT_NO
        JOIN Amospheric_Cond AS ac
            ON acs.ATMOSPH_COND = ac.ATMOSPH_COND
        JOIN Surface_Cond_Seq AS scs
            ON a.ACCIDENT_NO = scs.ACCIDENT_NO
        JOIN Road_Surface_Cond AS rsc
            ON scs.SURFACE_COND = rsc.SURFACE_COND
        GROUP BY
            ac.ATMOSPH_COND_DESC,
            lc.COND_NAME,
            rsc.SURFACE_COND_DESC
        ORDER BY TOTAL_CRASHES DESC;
        """
    ).fetchall()

    connection.close()

    return render_template("level2.html", results=results)


@app.route("/discover")
def discover():
    """Display the draft Level 3 discovery page."""
    return render_template("level3.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)
    