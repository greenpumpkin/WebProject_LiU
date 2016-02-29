import sqlite3
from flask import g

DATABASE = 'Twidder/database.db'


# Connection to a database
def connect_db():
    return sqlite3.connect(DATABASE)


# Opens a connect_db() if there is None in the current context
def get_db():
    db = getattr(g, '_database', None)
    # If there is no database in g, database value is None
    if db is None:
        db = g._database = connect_db()
    return db


# Close a database
def close_db():
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


######## DATABASE OPERATIONS ########

# Inserts a user in the database when signing in
def sign_in_db(email, password):
    db = get_db()
    cursor = db.cursor()
    user = (email, password)
    try:
        request = cursor.execute('SELECT * FROM users WHERE email=? AND password=?', user)
        return request.fetchone()
    except sqlite3.Error:
        return False

# Inserts a user in the database when signing up
def insert_user(email, password, firstname, familyname, gender, city, country):
    db = get_db()
    user = (email, password, firstname, familyname, gender, city, country)
    try:
        db.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)', user)
    except sqlite3.Error:
        return False
    db.commit()
    return True


# Inserts a logged-in user in the database
def add_logged_in(token, email):
    db = get_db()
    cursor = db.cursor()
    user = (token, email)
    cursor.execute('INSERT INTO loggedIn VALUES (?, ?)', user)
    db.commit()
    close_db()

# Get a user who is logged in
def get_logged_in(token):
    db = get_db()
    cursor = db.cursor()
    try:
        request = cursor.execute('SELECT * FROM loggedIn WHERE token=?', (token,))
        return request.fetchone()
    except sqlite3.Error:
        return False

# Get a user who is logged in
def get_logged_in_by_mail(email):
    db = get_db()
    cursor = db.cursor()
    try:
        request = cursor.execute('SELECT * FROM loggedIn WHERE email=?', (email,))
        return request.fetchone()
    except sqlite3.Error:
        return False

# Checks if a password is valid for a user willing to change it
def check_pwd(email, password):
    db = get_db()
    cursor = db.cursor()
    pwd = cursor.execute('SELECT password FROM users WHERE email=?', email)
    fetch = pwd.fetchone()
    if fetch[0] == password:
        return True
    return False


# Signs out a user from the system
def sign_out_db(token):
    db = get_db()
    cursor = db.cursor()
    try:
        request = cursor.execute('SELECT * FROM loggedIn WHERE token=?', (token,))
        return request.fetchone()
    except sqlite3.Error:
        return False


# Removes a user from the loggedIn table in the database
def remove_logged_in(token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM loggedIn WHERE token=?', (token,))
    db.commit()
    close_db()

# Removes a user from the loggedIn table in the database
def remove_logged_in_by_mail(email):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM loggedIn WHERE email=?', (email,))
        db.commit()
        #close_db()
    except Exception, err:
        print cursor
        print err


# Modify the password in the database
def modify_pwd(email, pwd, newpwd):
    db = get_db()
    cursor = db.cursor()
    user = (newpwd, email, pwd)
    cursor.execute('UPDATE users SET password=? WHERE email=? AND password=?', user)
    db.commit()
    db.close()


# Get the email from the token
def get_email(token):
    db = get_db()
    cursor = db.cursor()
    try:
        request = cursor.execute('SELECT email FROM loggedIn WHERE token=?', (token,))
        return request.fetchone()
    except sqlite3.Error:
        return False


# Get a user in the users table
def in_users(email):
    db = get_db()
    cursor = db.cursor()
    try:
        request = cursor.execute('SELECT * FROM users WHERE email=?', (email,))
        return request.fetchone()
    except sqlite3.Error:
        return False


# Get data of a user in the database from its token
def get_user_data_by_token(token):
    db = get_db()
    cursor = db.cursor()
    mail = get_email(token)
    try:
        request = cursor.execute('SELECT email,firstname,familyname,gender,city,country FROM users WHERE email=?',
                                 (mail[0],))
        return request.fetchone()
    except sqlite3.Error:
        return False


# Get data of a user in the database from its email
def get_user_data_by_email(email):
    db = get_db()
    cursor = db.cursor()
    try:
        request = cursor.execute('SELECT email,firstname,familyname,gender,city,country FROM users WHERE email=?',
                                 (email,))
        return request.fetchone()
    except sqlite3.Error:
        return False


# Post a message which is stored on the database
def post_message(message, token, sender, email):
    db = get_db()
    cursor = db.cursor()
    msg = (message, token, sender, email)
    try:
        request = cursor.execute('INSERT INTO messages VALUES (?,?,?,?)', msg)
        db.commit()
        return request.fetchone()
    except sqlite3.Error:
        return False

# Retrieves the messages for the user whom the passed token is issued for in the database
def get_user_messages_by_token_db(token):
    db = get_db()
    cursor = db.cursor()
    receiver = (get_email(token)[0],)
    try:
        request = cursor.execute('SELECT message,sender_email FROM messages WHERE receiver=?', receiver)
        return request.fetchall()
    except sqlite3.Error:
        return False

# Retrieves the messages for the user whom the passed email is specified in the database
def get_user_messages_by_email_db(email):
    db = get_db()
    cursor = db.cursor()
    try:
        request = cursor.execute('SELECT message,sender_email FROM messages WHERE receiver=?', (email,))
        return request.fetchall()
    except sqlite3.Error:
        return False

# Creates the database based on database.schema
def init_db(app):
    with app.app_context():
        db = get_db()
        with app.open_resource('database.schema', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
