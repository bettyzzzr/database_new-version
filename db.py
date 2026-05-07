from flask import current_app, g
import pymysql
from pymysql.cursors import DictCursor


def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host=current_app.config["MYSQL_HOST"],
            port=current_app.config["MYSQL_PORT"],
            user=current_app.config["MYSQL_USER"],
            password=current_app.config["MYSQL_PASSWORD"],
            database=current_app.config["MYSQL_DB"],
            cursorclass=DictCursor,
            autocommit=False,
            charset="utf8mb4",
        )
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def fetch_one(sql, params=None):
    with get_db().cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchone()


def fetch_all(sql, params=None):
    with get_db().cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchall()


def execute(sql, params=None):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(sql, params or ())
        db.commit()
        return cursor.lastrowid


def execute_affected(sql, params=None):
    db = get_db()
    with db.cursor() as cursor:
        affected = cursor.execute(sql, params or ())
        db.commit()
        return affected
