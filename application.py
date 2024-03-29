import os

import json
from models import *
import requests

from flask import Flask, session, render_template, redirect, url_for,request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
@login_required
def index():
    return render_template("main.html",name = session["username"])

@app.route("/register_user")
def register_user():
    return render_template("register_user.html")

@app.route("/register", methods=["POST","GET"])
def register():
    #registrar usuario
    username = request.form.get('username')
    password = request.form.get('password')
    repassword = request.form.get('repassword')
    if password != repassword:
        return render_template('error.html', message="Error password different.")
    #revisar si ya esta el usuario
    if db.execute("SELECT username FROM users where username = :username", {"username": username}).rowcount != 0:
        return render_template("error.html", message = "Account already exits!")
    #generar cuenta
    db.execute("INSERT INTO users (username,password) VALUES (:a,:b)",{"a":username,"b":password})
    db.commit()
    return render_template('success.html', message="Success! You can log in now.")

@app.route("/login", methods=["POST","GET"])
def login():
    emailLogIn=request.form.get('emailLogIn')
    userPasswordLogIn=request.form.get('userPasswordLogIn')

    if db.execute("SELECT * FROM users WHERE username = :a",{"a":emailLogIn}).rowcount == 0:
        return render_template("error.html", message = "Wrong user or password")
    data = db.execute("SELECT * FROM users WHERE username = :a",{"a":emailLogIn}).fetchone()
    if data.username==emailLogIn and data.password==userPasswordLogIn:
        session["username"]=emailLogIn
        return render_template("main.html", name = session["username"])
    else:
        return render_template("error.html", message = "Wrong user or password")

@app.route("/logout")
def logout():
    session.clear()
    return render_template("index.html")

@app.route("/search",methods=["GET","POST"])
@login_required
def search():
    username=session.get('username')
    session["books"]=[]
    if request.method=="POST":
        message=('')
        text=str(request.form.get('text'))
        data=db.execute("SELECT * FROM books WHERE author iLIKE '%"+text+"%' OR title iLIKE '%"+text+"%' OR isbn iLIKE '%"+text+"%'").fetchall()
        for x in data:
            session['books'].append(x)
        if len(session["books"])==0:
            message=('Nothing found. Try again.')
    return render_template("result.html",data=session['books'],message=message,username=username,name = session["username"])

@app.route("/isbn/<string:isbn>",methods=["GET","POST"])
@login_required
def bookpage(isbn):
    warning=""
    username=session.get('username')
    session["reviews"]=[]
    secondreview=db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND username= :username",{"username":username,"isbn":isbn}).fetchone()
    if request.method=="POST" and secondreview==None:
        review=request.form.get('textarea')
        rating=request.form.get('stars')
        db.execute("INSERT INTO reviews (isbn, review, rating, username) VALUES (:a,:b,:c,:d)",{"a":isbn,"b":review,"c":rating,"d":username})
        db.commit()
    if request.method=="POST" and secondreview!=None:
        warning="Sorry. You cannot add second review."

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "k0OeVCx8Qipbr8oIotGnxw", "isbns": isbn})
    average_rating=res.json()['books'][0]['average_rating']
    work_ratings_count=res.json()['books'][0]['work_ratings_count']
    reviews=db.execute("SELECT * FROM reviews WHERE isbn = :isbn",{"isbn":isbn}).fetchall()
    for y in reviews:
        session['reviews'].append(y)
    data=db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    return render_template("book.html",data=data,reviews=session['reviews'],average_rating=average_rating,work_ratings_count=work_ratings_count,username=username,warning=warning,name = session["username"])

@app.route("/api/<string:isbn>")
@login_required
def api(isbn):
    data=db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    if data==None:
        return render_template('404.html')
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "k0OeVCx8Qipbr8oIotGnxw", "isbns": isbn})
    average_rating=res.json()['books'][0]['average_rating']
    work_ratings_count=res.json()['books'][0]['work_ratings_count']
    x = {
    "title": data.title,
    "author": data.author,
    "year": data.year,
    "isbn": isbn,
    "review_count": work_ratings_count,
    "average_score": average_rating
    }
    api=json.dumps(x)
    return render_template("api.json",api=api)
