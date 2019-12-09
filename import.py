import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    db.execute("CREATE TABLE users (id SERIAL, username VARCHAR, password VARCHAR)")
    db.execute("CREATE TABLE reviews (isbn VARCHAR, review VARCHAR, rating INT, username VARCHAR)")
    db.execute("CREATE TABLE books (isbn VARCHAR, title VARCHAR, author VARCHAR, year VARCHAR)")

    f = open("books.csv")
    reader = csv.reader(f)

    for isbn,title,author,year in reader:
        if year == "year":
            print('skipped first line')
        else:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:a, :b, :c, :d)", {"a":isbn, "b":title, "c":author, "d":year})
    print("done")
    db.commit()
if __name__ == "__main__":
    main()
