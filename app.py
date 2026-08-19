from flask import Flask, render_template, request, redirect
import sqlite3
import re

app = Flask(__name__)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blog_id INTEGER,
            content TEXT,
            risk TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- SAMPLE BLOGS ----------------
def seed_blogs():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM blogs")
    count = c.fetchone()[0]

    if count == 0:
        c.execute("INSERT INTO blogs (title, content) VALUES (?, ?)",
                  ("Cyber Security Basics",
                   "Cyber security protects systems, networks, and data from digital attacks. It ensures confidentiality, integrity, and availability of information."))

        c.execute("INSERT INTO blogs (title, content) VALUES (?, ?)",
                  ("Web Development Guide",
                   "Web development involves creating websites and web applications using frontend, backend, and database technologies."))

    conn.commit()
    conn.close()

seed_blogs()

# ---------------- XSS DETECTOR ----------------
def detect_xss(text):
    patterns = [
        r"<script",
        r"javascript:",
        r"onerror=",
        r"onload=",
        r"<iframe",
        r"alert\("
    ]

    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return "RISKY"
    return "SAFE"

# ---------------- HOME ----------------
@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM blogs")
    blogs = c.fetchall()

    conn.close()

    return render_template("index.html", blogs=blogs)

# ---------------- VIEW BLOG ----------------
@app.route("/blog/<int:blog_id>")
def blog(blog_id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM blogs WHERE id=?", (blog_id,))
    blog = c.fetchone()

    c.execute("SELECT * FROM comments WHERE blog_id=?", (blog_id,))
    comments = c.fetchall()

    conn.close()

    return render_template("blog.html",
                           blog=blog,
                           comments=comments,
                           blog_id=blog_id)

# ---------------- ADD COMMENT ----------------
@app.route("/add_comment/<int:blog_id>", methods=["POST"])
def add_comment(blog_id):

    comment = request.form["comment"]

    # Detect harmful/XSS comment
    risk = detect_xss(comment)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO comments (blog_id, content, risk) VALUES (?, ?, ?)",
        (blog_id, comment, risk)
    )

    conn.commit()
    conn.close()

    return redirect(f"/blog/{blog_id}")

# ---------------- DELETE COMMENT ----------------
@app.route("/delete/<int:id>/<int:blog_id>")
def delete(id, blog_id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM comments WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect(f"/blog/{blog_id}")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM comments WHERE risk='SAFE'")
    safe = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM comments WHERE risk='RISKY'")
    risky = c.fetchone()[0]

    c.execute("SELECT * FROM comments ORDER BY id DESC")
    comments = c.fetchall()

    conn.close()

    return render_template("dashboard.html", safe=safe, risky=risky, comments=comments)

if __name__ == "__main__":
    app.run(debug=True)