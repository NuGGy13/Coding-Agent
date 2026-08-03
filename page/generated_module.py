"""
generated_module.py

A complete Flask user authentication module featuring login, dashboard,
and logout functionality with password hashing and session management.
"""

import os
from functools import wraps
from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# In-memory user database (username -> hashed password)
# In production, replace this with a database model (e.g., SQLAlchemy)
USERS = {
    "admin": generate_password_hash("admin123"),
    "user": generate_password_hash("user123"),
}

# HTML Templates using Bootstrap 5 for clean UI
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Flask App{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .auth-card { max-width: 400px; margin: 80px auto; }
    </style>
</head>
<body>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="mt-4">
                {% for category, message in messages %}
                    <div class="alert alert-{{ category if category != 'error' else 'danger' }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

LOGIN_TEMPLATE = BASE_LAYOUT + """
{% block title %}Login{% endblock %}
{% block content %}
<div class="card auth-card shadow-sm">
    <div class="card-body p-4">
        <h3 class="card-title text-center mb-4">Sign In</h3>
        <form method="POST" action="{{ url_for('login') }}">
            <div class="mb-3">
                <label for="username" class="form-label">Username</label>
                <input type="text" class="form-control" id="username" name="username" required autofocus>
            </div>
            <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <button type="submit" class="btn btn-primary w-100 mt-2">Log In</button>
        </form>
        <div class="mt-3 text-muted text-center">
            <small>Demo users: admin/admin123 or user/user123</small>
        </div>
    </div>
</div>
{% endblock %}
"""

DASHBOARD_TEMPLATE = BASE_LAYOUT + """
{% block title %}Dashboard{% endblock %}
{% block content %}
<div class="row justify-content-center mt-5">
    <div class="col-md-8">
        <div class="card shadow-sm">
            <div class="card-body p-4">
                <h2 class="card-title">Welcome, {{ session['username'] }}!</h2>
                <p class="lead">You have successfully logged into the application.</p>
                <hr>
                <a href="{{ url_for('logout') }}" class="btn btn-danger">Sign Out</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""


def login_required(f):
    """Decorator to protect routes requiring user authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def dashboard():
    """Protected dashboard route."""
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user authentication and renders the login form."""
    if "username" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        stored_hash = USERS.get(username)
        if stored_hash and check_password_hash(stored_hash, password):
            session["username"] = username
            flash(f"Welcome back, {username}!", "success")
            
            # Redirect to originally requested page if present
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template_string(LOGIN_TEMPLATE)


@app.route("/logout")
def logout():
    """Logs out the user by clearing the session."""
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)