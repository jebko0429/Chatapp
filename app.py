from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, send
import sqlite3
from datetime import datetime

# Initialize Flask app and libraries
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with a strong secret key
bcrypt = Bcrypt(app)
socketio = SocketIO(app)

#admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "pass"


# Database initialization
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Create users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)

    # Create messages table
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

# Call init_db to initialize the database
init_db()

# Routes
@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, status) VALUES (?, ?, 'pending')", (username, hashed_password))
            conn.commit()
            conn.close()
            flash("Registration submitted! Await admin approval.", "info")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT password, status FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user:
            hashed_password, status = user
            if status == "pending":
                flash("Your registration is still pending approval.", "warning")
            elif bcrypt.check_password_hash(hashed_password, password):
                session["user"] = username
                flash("Login successful!", "success")
                return redirect(url_for("chat"))
            else:
                flash("Invalid credentials. Please try again.", "danger")
        else:
            flash("Invalid credentials. Please try again.", "danger")
    return render_template("login.html")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY id ASC")
    messages = c.fetchall()
    conn.close()
    return render_template("chat.html", username=session["user"], messages=messages)

@socketio.on("message")
def handle_message(msg):
    username = session["user"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)", (username, msg, timestamp))
    conn.commit()
    conn.close()
    send({"username": username, "message": msg, "timestamp": timestamp}, broadcast=True)

#old
"""
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        action = request.form["action"]
        user_id = request.args.get("user_id")  # Extract the user ID from the query string
        if not user_id:
            flash("Invalid user ID.", "danger")
            return redirect(url_for("admin"))
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        if action == "approve":
            c.execute("UPDATE users SET status = 'approved' WHERE id = ?", (user_id,))
            flash("User approved successfully.", "success")
        elif action == "reject":
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))
            flash("User rejected successfully.", "success")
        conn.commit()
        conn.close()

    # Fetch pending users for display
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE status = 'pending'")
    pending_users = c.fetchall()
    conn.close()
    return render_template("admin.html", pending_users=pending_users)
"""
###new
# Admin Login Route
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            return render_template("admin_login.html", error="Invalid credentials.")

    return render_template("admin_login.html")

# Admin Page Route
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE status='pending'")
    pending_users = c.fetchall()
    conn.close()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        action = request.form.get("action")

        if user_id and action:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            if action == "approve":
                c.execute("UPDATE users SET status='approved' WHERE id=?", (user_id,))
            elif action == "reject":
                c.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
            conn.close()

        return redirect(url_for("admin"))

    return render_template("admin.html", pending_users=pending_users)

# Admin Logout
@app.route("/admin-logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))
#####
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# Run the Flask app
if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
