from flask import Flask, render_template, session, redirect, request, flash
from mysqlconnection import MySQLConnector
import re
import md5
import hashlib
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app = Flask(__name__)
mysql = MySQLConnector(app, 'the_wall_db2')

app.secret_key = "supersecret"

@app.route('/')
def index():
    data = {
        'title': "login or register"
    }
    return render_template('index.html', data=data)

@app.route('/users/create', methods=['post'])
def register():
    #print request.form
    form = request.form
    errors = []
    if len(form['first_name']) < 2:
        errors.append('first name must be at least 2 characters')
    if len(form['last_name']) < 2:
        errors.append('last name must be at least 2 characters')
    #if not EMAIL_REGEX.match(form['email']):
    #    errors.append('must use valid email address')
    if len(form['password']) < 8:
        errors.append('password must be at least 8 characters')
    if form['password'] != form['confirm_pw']:
        errors.append('passwords must match')

    if errors:
        for error in errors:
            flash(error)
        return redirect('/')

#check to see whether a user already exists with email entered
    email_query = 'SELECT * FROM users WHERE email=:email'
    data = {
        'email': form['email']
    }
    user_list = mysql.query_db(email_query, data)

    if user_list:
        flash('email already in use')
        return redirect('/')

    #pw_hash = md5.new(form['password']).hexidigest()
    #print pw_hash
    #pw_hash = md5.new(form['password']).hexidigest()
    data = {
        'first_name': form['first_name'],
        'last_name': form['last_name'],
        'email': form['email'],
        'password': form['password'],
    }

    insert_query = 'INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())'

    user_id = mysql.query_db(insert_query, data) 
    user_query = 'SELECT * FROM users WHERE id = :user_id'
    data = {
        'user_id': user_id
    }
    user_list = mysql.query_db(user_query, data)

    if not user_list:
        flash('something went wrong')
        return redirect('/')
    
    user = user_list[0]

    #this creates that user. Now we need to store in session below
    session['user_id'] = user_id 
    session['user_name'] = user['first_name']
    #stores newly created user in session.
    return redirect('/wall')

@app.route('/login', methods=['post'])
def login():
    form = request.form
    email_query = 'SELECT * FROM users WHERE email=:email'
    data = {
        'email': form['email']
    }
    user_list = mysql.query_db(email_query, data)

    if not user_list:
        flash('email or password invalid')
        return redirect('/')

    user = user_list[0]
    print user['password'], form['password']


    if form['password'] != user['password']:
        flash('email or password invalid')
        return redirect('/')
    
    session['user_id'] = user['id']
    return redirect('/wall')
 
@app.route('/posts/create', methods=["POST"])
def create_post():
    if len(request.form['content']) < 2:
        flash('Post must be at least 2 characters')
        return redirect('/wall')

    post_query = 'INSERT INTO posts (content, user_id, created_at, updated_at) VALUES (:content, :user_id, NOW(), NOW())'
    data = {
        'content': request.form['content'],
        'user_id': session['user_id']
    }
    mysql.query_db(post_query, data)
    return redirect('/wall')

@app.route('/comments/create/<post_id>', methods=['POST'])
def create_comment(post_id):
    if len(request.form['content']) <2:
        flash('comment must be at least 2 characters long')
        return redirect('/')

    comment_query = 'INSERT INTO comments (content, user_id, post_id, created_at, updated_at) VALUES (:content, :user_id, :post_id, NOW(), NOW())'
    data = {
        'content': request.form['content'],
        'user_id': session['user_id'],
        'post_id': post_id
    }
    mysql.query_db(comment_query, data)
    return redirect('/wall')

@app.route('/wall')
def wall():
    if not 'user_id' in session:
        return redirect('/')

    post_query = 'SELECT users.first_name AS first, users.last_name AS last, posts.content AS content, posts.created_at AS created_at, posts.id AS id FROM posts JOIN users ON users.id = posts.user_id'
    posts = mysql.query_db(post_query)
    
    comment_query = 'SELECT comments.content AS content, comments.post_id AS post_id, users.first_name AS first, users.last_name AS last, comments.created_at AS created_at FROM comments JOIN users ON users.id = comments.user_id'
    comments = mysql.query_db(comment_query)
    data = {
        'title': 'the wall',
        'posts': posts,
        'comments': comments
    }
    return render_template('wall.html', data=data)

@app.route('/logout', methods=['post'])
def logout():
    session.clear()
    return redirect('/')

app.run(debug=True)