from functools import wraps
from flask import redirect,session,render_template

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return render_template("index.html")
        return f(*args, **kwargs)
    return decorated_function
