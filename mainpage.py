from flask import Flask, render_template, url_for
from flask import request, redirect, flash, make_response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, TextBook, TBEdition, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import datetime

engine = create_engine('sqlite:///textbookeditions.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "Books Store"

DBSession = sessionmaker(bind=engine)
session = DBSession()
# Create anti-forgery state token
tbs_cat = session.query(TextBook).all()


# login
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    tbs_cat = session.query(TextBook).all()
    tbes = session.query(TBEdition).all()
    return render_template('login.html',
                           STATE=state, tbs_cat=tbs_cat, tbes=tbes)
    # return render_template('myhome.html', STATE=state
    # tbs_cat=tbs_cat,tbes=tbes)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; border-radius: 150px;'
    '-webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as e:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


# Home
@app.route('/')
@app.route('/home')
def home():
    tbs_cat = session.query(TextBook).all()
    return render_template('myhome.html', tbs_cat=tbs_cat)


# Book Category for admins
@app.route('/BookStore')
def BookStore():
    try:
        if login_session['username']:
            name = login_session['username']
            tbs_cat = session.query(TextBook).all()
            tbs = session.query(TextBook).all()
            tbes = session.query(TBEdition).all()
            return render_template('myhome.html', tbs_cat=tbs_cat,
                                   tbs=tbs, tbes=tbes, uname=name)
    except:
        return redirect(url_for('showLogin'))


# Showing books based on book category
@app.route('/BookStore/<int:tbid>/AllBooks')
def showEditions(tbid):
    tbs_cat = session.query(TextBook).all()
    tbs = session.query(TextBook).filter_by(id=tbid).one()
    tbes = session.query(TBEdition).filter_by(textbookid=tbid).all()
    try:
        if login_session['username']:
            return render_template('showEditions.html', tbs_cat=tbs_cat,
                                   tbs=tbs, tbes=tbes,
                                   uname=login_session['username'])
    except:
        return render_template('showEditions.html',
                               tbs_cat=tbs_cat, tbs=tbs, tbes=tbes)


# Add New Book
@app.route('/BookStore/addBook', methods=['POST', 'GET'])
def addBook():
    if request.method == 'POST':
        newbook = TextBook(name=request.form['name'],
                           user_id=login_session['user_id'])
        session.add(newbook)
        session.commit()
        return redirect(url_for('BookStore'))
    else:
        return render_template('addBook.html', tbs_cat=tbs_cat)


# Edit Book Category
@app.route('/BookStore/<int:tbid>/edit', methods=['POST', 'GET'])
def editCategory(tbid):
    editedBook = session.query(TextBook).filter_by(id=tbid).one()
    creator = getUserInfo(editedBook.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this Book Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('BookStore'))
    if request.method == "POST":
        if request.form['name']:
            editedBook.name = request.form['name']
        session.add(editedBook)
        session.commit()
        flash("Book Category Edited Successfully")
        return redirect(url_for('BookStore'))
    else:
        # tbs_cat is global variable we can them in entire application
        return render_template('editCategory.html',
                               tb=editedBook, tbs_cat=tbs_cat)


# Delete Book Category
@app.route('/BookStore/<int:tbid>/delete', methods=['POST', 'GET'])
def deleteCategory(tbid):
    tb = session.query(TextBook).filter_by(id=tbid).one()
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot Delete this Book Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('BookStore'))
    if request.method == "POST":
        session.delete(tb)
        session.commit()
        flash("Book Category Deleted Successfully")
        return redirect(url_for('BookStore'))
    else:
        return render_template('deleteCategory.html', tb=tb, tbs_cat=tbs_cat)


# Add New Book Edition Details
@app.route('/BookStore/addBook/addBookDetails/<string:tbname>/add',
           methods=['GET', 'POST'])
def addBookDetails(tbname):
    tbs = session.query(TextBook).filter_by(name=tbname).one()
    # See if the logged in user is not the owner of book
    creator = getUserInfo(tbs.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't add new book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showEditions', tbid=tbs.id))
    if request.method == 'POST':
        name = request.form['name']
        author = request.form['author']
        edition = request.form['edition']
        publisher = request.form['publisher']
        price = request.form['price']
        tbdetails = TBEdition(name=name, author=author,
                              edition=edition, publisher=publisher,
                              price=price,
                              date=datetime.datetime.now(),
                              textbookid=tbs.id,
                              user_id=login_session['user_id'])
        session.add(tbdetails)
        session.commit()
        return redirect(url_for('showEditions', tbid=tbs.id))
    else:
        return render_template('addBookDetails.html',
                               tbname=tbs.name, tbs_cat=tbs_cat)


# Edit Book Edition
@app.route('/BookStore/<int:tbid>/<string:tbename>/edit',
           methods=['GET', 'POST'])
def editBook(tbid, tbename):
    tb = session.query(TextBook).filter_by(id=tbid).one()
    tbdetails = session.query(TBEdition).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of book
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't edit this book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showEditions', tbid=tb.id))
    # POST methods
    if request.method == 'POST':
        tbdetails.name = request.form['name']
        tbdetails.author = request.form['author']
        tbdetails.edition = request.form['edition']
        tbdetails.publisher = request.form['publisher']
        tbdetails.price = request.form['price']
        tbdetails.date = datetime.datetime.now()
        session.add(tbdetails)
        session.commit()
        flash("Book Edited Successfully")
        return redirect(url_for('showEditions', tbid=tbid))
    else:
        return render_template('editTB.html',
                               tbid=tbid, tbdetails=tbdetails, tbs_cat=tbs_cat)


# Delte Book Editon
@app.route('/BookStore/<int:tbid>/<string:tbename>/delete',
           methods=['GET', 'POST'])
def deleteBook(tbid, tbename):
    tb = session.query(TextBook).filter_by(id=tbid).one()
    tbdetails = session.query(TBEdition).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of book
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't delete this book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showEditions', tbid=tb.id))
    if request.method == "POST":
        session.delete(tbdetails)
        session.commit()
        flash("Deleted Book Successfully")
        return redirect(url_for('showEditions', tbid=tbid))
    else:
        return render_template('deleteTB.html',
                               tbid=tbid, tbdetails=tbdetails, tbs_cat=tbs_cat)


# Logout
@app.route('/logout')
def logout():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = \
        h.request(uri=url, method='POST', body=None,
                  headers={'content-type': 'application/x-www-form-urlencoded'})[0]

    print result['status']
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successfully logged out")
        return redirect(url_for('showLogin'))
        # return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Json
@app.route('/BookStore/JSON')
def allBooksJSON():
    bookcategories = session.query(TextBook).all()
    category_dict = [c.serialize for c in bookcategories]
    for c in range(len(category_dict)):
        books = [i.serialize for i in session.query(
                 TBEdition).filter_by(textbookid=category_dict[c]["id"]).all()]
        if books:
            category_dict[c]["book"] = books
    return jsonify(TextBook=category_dict)


@app.route('/bookStore/bookCategories/JSON')
def categoriesJSON():
    books = session.query(TextBook).all()
    return jsonify(bookCategories=[c.serialize for c in books])


@app.route('/bookStore/editions/JSON')
def itemsJSON():
    items = session.query(TBEdition).all()
    return jsonify(editions=[i.serialize for i in items])


@app.route('/bookStore/<path:book_name>/editions/JSON')
def categoryItemsJSON(book_name):
    bookCategory = session.query(TextBook).filter_by(name=book_name).one()
    editions = session.query(TBEdition).filter_by(textbook=bookCategory).all()
    return jsonify(bookEdtion=[i.serialize for i in editions])


@app.route('/bookStore/<path:book_name>/<path:edition_name>/JSON')
def ItemJSON(book_name, edition_name):
    bookCategory = session.query(TextBook).filter_by(name=book_name).one()
    bookEdition = session.query(TBEdition).filter_by(
           name=edition_name, textbook=bookCategory).one()
    return jsonify(bookEdition=[bookEdition.serialize])

if __name__ == '__main__':
    global tbs_cat
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
