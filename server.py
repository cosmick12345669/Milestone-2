from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3
import os
import urllib.parse

print("LOADING SERVER CODE")
DB_NAME = "Road_Accidents v2.0.db"

def render_page(page_title, content_html):
    """Load base.html and insert title and content."""
    with open("templates/base.html", "r", encoding="utf-8") as f:
        base = f.read()
    base = base.replace("{{PAGE_TITLE}}", page_title)
    base = base.replace("{{PAGE_CONTENT}}", content_html)
    return base

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == "/":
        elif path.startswith("/static/"):
            self.handle_static(path)
        elif path == "/Explorer":
            self.handle_explore_page("Injury Outcomes Explorer", "templates/darren_l2.html", parsed_path)
        else:
            self.send_error(404, "Not found")   
        
    def handle_simple_page(self, title, template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            content_html = f.read()
        full_html = render_page(title, content_html)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(full_html.encode("utf-8"))
  
    def handle_explore_page(self, title, template_path, parsed_path):
        query_params = urllib.parse.parse_qs(parsed_path.query)

        # Read form inputs from the URL query string
        age_group = query_params.get("age_group", [""])[0]
        injury_outcome = query_params.get("injury_outcome", [""])[0]
        hospital = query_params.get("hospital", [""])[0]
        ejected = query_params.get("ejected", [""])[0]
        sort_order = query_params.get("sort_order", ["DESC"])[0]

        # Build SQL query
        sql = """
        SELECT
            AGE_GROUP,
            TAKEN_TO_HOSPITAL,
            EJECTED_CODE,
            INJURY_OUTCOME,
            COUNT(*) AS TotalPeople
        FROM PERSON
        """

        conditions = []
        values = []

        if age_group:
            conditions.append("AGE_GROUP = ?")
            values.append(age_group)

        if injury_outcome:
            conditions.append("INJURY_OUTCOME = ?")
            values.append(injury_outcome)

        if hospital:
            conditions.append("TAKEN_TO_HOSPITAL = ?")
            values.append(hospital)

        if ejected:
            conditions.append("EJECTED_CODE = ?")
            values.append(ejected)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += """
        GROUP BY
            AGE_GROUP,
            TAKEN_TO_HOSPITAL,
            EJECTED_CODE,
            INJURY_OUTCOME
        """

        sql += f" ORDER BY TotalPeople {sort_order}"

        # Run database query
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(sql, values)
        rows = cur.fetchall()
        conn.close()

        # Build table rows HTML
        table_rows_html = ""
        for agg_age, agg_hospital, agg_ejected, agg_injury, total in rows:
            table_rows_html += f"""
            <tr>
                <td>{agg_age}</td>
                <td>{agg_hospital}</td>
                <td>{agg_ejected}</td>
                <td>{agg_injury}</td>
                <td>{total}</td>
            </tr>
            """
        
        if not rows:
            table_rows_html = """
            <tr>
                <td colspan="5">
                    No records match the selected filters.
                </td>
            </tr>
            """
        
        # Build filter summary description
        filters = []
        if age_group:
            filters.append(f"Age Group: {age_group}")
        if injury_outcome:
            filters.append(f"Injury Outcome: {injury_outcome}")
        if hospital:
            filters.append(f"Hospitalised: {hospital}")
        if ejected:
            filters.append(f"Ejected: {ejected}")

        if filters:
            filter_summary = "Showing results for " + ", ".join(filters)
        else:
            filter_summary = "Showing all crash records."

        # Load template and swap tokens
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        html = (
            html.replace("{{TABLE_ROWS}}", table_rows_html)
            .replace("{{FILTER_SUMMARY}}", filter_summary)
        )

        full_html = render_page(title, html)

        # Send response
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(full_html.encode("utf-8"))

    def handle_static(self, path):
        file_path = path.lstrip("/")  # remove leading '/'
        if os.path.isfile(file_path):
            if file_path.endswith(".css"):
                content_type = "text/css"
            else:
                content_type = "application/octet-stream"

            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "Static file not found")


def run():
    server_address = ("", 8000)  # localhost:8000
    httpd = HTTPServer(server_address, RequestHandler)
    print("Server running at http://localhost:8000")
    httpd.serve_forever()


if __name__ == "__main__":
    run()