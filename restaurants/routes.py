from flask import render_template, url_for, flash, redirect, request, jsonify, session, abort, make_response
from restaurants import app
from restaurants.sql import cursor
from restaurants.sql.models import Base, Restaurant, Menu, User

#OAuth imports
import os
import pathlib
import requests
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from google.oauth2 import id_token
import json

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "610084126582-l8v4hv1clqcphtep9pmv01fd1m031ig5.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file, 
        scopes=["https://www.googleapis.com/auth/userinfo.profile", 
        "https://www.googleapis.com/auth/userinfo.email", 
        "openid"],
        redirect_uri="http://127.0.0.1:5000/callback"
        )

def return_user_if_exist(name):
    try:
        return cursor.query(User).filter_by(name=name).one()
    except:
        return None

def getUserID(email):
    try:
        user = cursor.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

def getUserInfo(user_id):
    user = cursor.query(User).filter_by(id = user_id).one()
    return user

def createUser():
    newUser = User(name = session["name"], email = session["email"], picture = session["picture"])
    cursor.add(newUser)
    cursor.commit()

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return redirect(url_for('errorRestaurant', error='You must be logged in'))
        else:
            return function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return wrapper


@app.route('/login')
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/restaurants")

@app.route('/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)
    """
    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!
    """
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    session["picture"] = id_info.get("picture")

    user = return_user_if_exist(session['name'])

    if not user:
        createUser()
        user = cursor.query(User).filter_by(name=session["name"]).one() #Retrieving user_id
    return redirect("/restaurants")



@app.route('/protected_area')
@login_is_required
def protected_area():
    return f"Hello {session['name']}!, email: {session['email']}, picture: {session['picture']} <br/> <a href='/logout'><button>Logout</button></a>"

# Routes
@app.route('/restaurants/error/<string:error>')
def errorRestaurant(error):
    return render_template('error.html', error=error, login=login, userLogged = session["name"] if "google_id" in session else None)

@app.route('/')
@app.route('/restaurants')
def showRestaurant():
    try:
        restaurants = cursor.query(Restaurant).all()
    except:
        restaurants = None
    login = "google_id" in session
    return render_template('restaurants.html', restaurants=restaurants, login=login, userLogged = session["name"] if "google_id" in session else None)


@app.route('/restaurant/new', methods=['POST', 'GET'])
@login_is_required
def newRestaurant():
    if request.method == 'POST':
        try:
            restaurant_name = request.form['restaurant_name']
            if not restaurant_name:
                raise Exception
            user = cursor.query(User).filter_by(name=session["name"]).one()
            new_restaurant = Restaurant(name=restaurant_name, user_id = user.id)
            
            cursor.add(new_restaurant)
            cursor.commit()
            
            flash('New restaurant created', 'success')
            return redirect(url_for('showRestaurant'))
        except:
            return redirect(url_for('errorRestaurant', error='Creating restaurant'))
    return render_template('newRestaurant.html', login=login, userLogged = session["name"] if "google_id" in session else None)

@app.route('/restaurant/<int:restaurant_id>/edit', methods=['POST', 'GET'])
@login_is_required
def editRestaurant(restaurant_id):
    restaurant = cursor.query(Restaurant).get(restaurant_id)
    user = cursor.query(User).filter_by(name=session["name"]).one()
    if restaurant.user_id == user.id:
        if request.method == 'POST':
            try:
                new_restaurant_name = request.form['restaurant_name']
                if not new_restaurant_name:
                    raise Exception
                
                restaurant.name = new_restaurant_name
                
                cursor.add(restaurant)
                cursor.commit()
                
                flash('Restaurant successfully Edited', 'warning')
                return redirect(url_for('showRestaurant'))
            except:
                return redirect(url_for('errorRestaurant', error='Editing restaurant'))
        try:
            restaurant = cursor.query(Restaurant).get(restaurant_id)
            return render_template('editRestaurant.html', restaurant=restaurant, login=login, userLogged = session["name"] if "google_id" in session else None)
        except:
            return redirect(url_for('errorRestaurant', error='Retrieving restaurant'))
    else:
        return redirect(url_for('errorRestaurant', error='You can\'t modify others restaurants'))

@app.route('/restaurant/<int:restaurant_id>/delete', methods=['POST', 'GET'])
@login_is_required
def deleteRestaurant(restaurant_id):
    restaurant = cursor.query(Restaurant).get(restaurant_id)
    user = cursor.query(User).filter_by(name=session["name"]).one()
    if restaurant.user_id == user.id:
        if request.method == 'POST':
            try:
                menus = cursor.query(Menu).filter_by(restaurant_id=restaurant_id).all()
                for menu in menus:
                    cursor.delete(menu)
                
                cursor.delete(restaurant)
                cursor.commit()
                
                flash('Restaurant successfully Deleted', 'danger')
                return redirect(url_for('showRestaurant'))
            except:
                return redirect(url_for('errorRestaurant', error='Deleting restaurant'))
        try:
            restaurant = cursor.query(Restaurant).get(restaurant_id)
            return render_template('deleteRestaurant.html', restaurant=restaurant, login=login, userLogged = session["name"] if "google_id" in session else None)
        except:
            return redirect(url_for('errorRestaurant', error='Retrieving restaurant'))
    else:
        return redirect(url_for('errorRestaurant', error='You can\'t modify others restaurants'))

@app.route('/restaurant/<int:restaurant_id>')
@app.route('/restaurant/<int:restaurant_id>/menu', methods=['GET'])
def showMenu(restaurant_id):

    try:
        restaurant = cursor.query(Restaurant).get(restaurant_id)
        menus = cursor.query(Menu).filter_by(restaurant_id=restaurant_id).all()    
    except:
        return redirect(url_for('errorRestaurant', error='Retrieving menus or restaurant'))
    return render_template('menu.html', restaurant=restaurant, menus=menus, login=login, userLogged = session["name"] if "google_id" in session else None)

@app.route('/restaurant/<int:restaurant_id>/menu/new', methods=['POST', 'GET'])
@login_is_required
def newMenuItem(restaurant_id):
    restaurant = cursor.query(Restaurant).get(restaurant_id)
    user = cursor.query(User).filter_by(name=session["name"]).one()
    if restaurant.user_id == user.id:
        if request.method == 'POST':
            try:
                
                menu_name = request.form['menu_name']
                menu_price = float(request.form['menu_price'])
                menu_description = request.form['menu_description']

                new_menu = Menu(name=menu_name, price=menu_price, 
                description=menu_description, restaurant_id=restaurant_id, 
                restaurant=restaurant, user_id = user.id)
                
                cursor.add(new_menu)
                cursor.commit()
                
                flash('Menu Item successfully Created', 'success')
                return redirect(url_for('showMenu', restaurant_id=restaurant_id))
            except:
                return redirect(url_for('errorRestaurant'))
        try:
            restaurant = cursor.query(Restaurant).get(restaurant_id)
            return render_template('newMenuItem.html', restaurant=restaurant, login=login, userLogged = session["name"] if "google_id" in session else None)
        except:
            return redirect(url_for('errorRestaurant', error='Retrieving restaurant'))
    else:
        return redirect(url_for('errorRestaurant', error='You can\'t modify others restaurants'))

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
@login_is_required
def editMenuItem(restaurant_id, menu_id):
    restaurant = cursor.query(Restaurant).get(restaurant_id)
    user = cursor.query(User).filter_by(name=session["name"]).one()
    if restaurant.user_id == user.id:
        if request.method == 'POST':
            try:
                menu = cursor.query(Menu).get(menu_id)
                
                menu.name = request.form['menu_name']
                menu.price = float(request.form['menu_price'])
                menu.description = request.form['menu_description']
                
                cursor.commit()
                
                flash('Menu Item successfully Edited', 'warning')
                return redirect(url_for('showMenu', restaurant_id=restaurant_id))
            except:
                return redirect(url_for('errorRestaurant'))
        try:
            restaurant = cursor.query(Restaurant).get(restaurant_id)
            menu = cursor.query(Menu).get(menu_id)
            return render_template('editMenuItem.html', restaurant=restaurant, menu=menu, login=login, userLogged = session["name"] if "google_id" in session else None)
        except:
            return redirect(url_for('errorRestaurant', error='Retrieving menu or restaurant'))
    else:
        return redirect(url_for('errorRestaurant', error='You can\'t modify others restaurants'))

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
@login_is_required
def deleteMenuItem(restaurant_id, menu_id):
    restaurant = cursor.query(Restaurant).get(restaurant_id)
    user = cursor.query(User).filter_by(name=session["name"]).one()
    if restaurant.user_id == user.id:
        if request.method == 'POST':
            try:
                menu = cursor.query(Menu).get(menu_id)
                
                cursor.delete(menu)
                cursor.commit()
                
                flash('Menu Item successfully Deleted', 'danger')
                return redirect(url_for('showMenu', restaurant_id=restaurant_id))
            except:
                return redirect(url_for('errorRestaurant', error='Deleting Menu Item'))
        try:
            restaurant = cursor.query(Restaurant).get(restaurant_id)
            menu = cursor.query(Menu).get(menu_id)
            return render_template('deleteMenuItem.html', restaurant=restaurant, menu=menu, login=login, userLogged = session["name"] if "google_id" in session else None)
        except:
            return redirect(url_for('errorRestaurant', error='Retrieving menu or restaurant'))
    else:
        return redirect(url_for('errorRestaurant', error='You can\'t modify others restaurants'))
    
#TODO Json API endpoint
@app.route('/restaurants/JSON')
def restaurants_JSON():
    restaurants = cursor.query(Restaurant).all()
    return jsonify(Restaurants=[i.serialize for i in restaurants])
    
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurant_menus_JSON(restaurant_id):
    try:
        restaurant = cursor.query(Restaurant).get(restaurant_id)
        menus = cursor.query(Menu).filter_by(restaurant_id=restaurant_id).all()
        return jsonify(Restaurant={
            'Restaurant': restaurant.serialize,
            'menus': [i.serialize for i in menus]    
        })
    except:
        return jsonify(Error={'Message':'Restaurant not found'})

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def restaurant_menu_JSON(restaurant_id, menu_id):
    try:
        restaurant = cursor.query(Restaurant).get(restaurant_id)
        menu = cursor.query(Menu).filter_by(menu_id=menu_id).one()
        return jsonify(Menu=menu.serialize)
    except:
        return jsonify(Error={'Message':'Restaurant or Menu not found'})

@app.route('/users')
def showUsers():
    try:
        users = cursor.query(User).all()
    except:
        users = None
    login = "google_id" in session
    return render_template('users.html', users=users, login=login, userlogged = session["name"] if "google_id" in session else None)


@app.route('/users/<int:user_id>/delete', methods=['POST', 'GET'])
@login_is_required
def deleteUser(user_id):
    if request.method == 'POST':
        try:
            user = cursor.query(User).get(user_id)
            
            cursor.delete(user)
            cursor.commit()
            
            flash('User successfully Deleted', 'danger')
            return redirect(url_for('showUsers'))
        except:
            return redirect(url_for('errorRestaurant', error='Deleting user'))
    try:
        user = cursor.query(User).get(user_id)
        return render_template('deleteUser.html', user=user, login=login, userlogged = session["name"] if "google_id" in session else None)
    except:
        return redirect(url_for('errorRestaurant', error='Retrieving user'))

@app.route('/privacy-policy')
def privacyPolicy():
    return render_template('privacyPolicy.html', userlogged = session["name"] if "google_id" in session else None)

