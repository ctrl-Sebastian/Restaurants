from flask import render_template, url_for, flash, redirect, request, jsonify, session, abort
from restaurants import app
from restaurants.sql import cursor
from restaurants.sql.models import Base, Restaurant, Menu

GOOGLE_CLIENT_ID = "610084126582-l8v4hv1clqcphtep9pmv01fd1m031ig5.apps.googleusercontent.com"

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401) #authorization required
        else:
            return function()
    return wrapper


@app.route('/login')
def login():
    session["google_id"] = "Test"
    return redirect("/protected_area")

@app.route('/callback')
def callback():
    pass

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/restaurants")

@app.route('/protected_area')
@login_is_required
def protected_area():
    return "Protected Area! <a href='/logout'><button>Logout</button></a>"

@app.route('/restaurants/error/<string:error>')
def errorRestaurant(error):
    return render_template('error.html', error=error)

@app.route('/')
@app.route('/restaurants')
def showRestaurant():
    try:
        restaurants = cursor.query(Restaurant).all()
    except:
        restaurants = None
    return render_template('restaurants.html', restaurants=restaurants)


@app.route('/restaurant/new', methods=['POST', 'GET'])
def newRestaurant():
    if request.method == 'POST':
        try:
            restaurant_name = request.form['restaurant_name']
            if not restaurant_name:
                raise Exception
            
            new_restaurant = Restaurant(name=restaurant_name)
            
            cursor.add(new_restaurant)
            cursor.commit()
            
            flash('New restaurant created', 'success')
            return redirect(url_for('showRestaurant'))
        except:
            return redirect(url_for('errorRestaurant', error='Creating restaurant'))
    return render_template('newRestaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit', methods=['POST', 'GET'])
def editRestaurant(restaurant_id):
    if request.method == 'POST':
        try:
            new_restaurant_name = request.form['restaurant_name']
            if not new_restaurant_name:
                raise Exception
            
            restaurant = cursor.query(Restaurant).get(restaurant_id)
            restaurant.name = new_restaurant_name
            
            cursor.add(restaurant)
            cursor.commit()
            
            flash('Restaurant successfully Edited', 'warning')
            return redirect(url_for('showRestaurant'))
        except:
            return redirect(url_for('errorRestaurant', error='Editing restaurant'))
    try:
        restaurant = cursor.query(Restaurant).get(restaurant_id)
        return render_template('editRestaurant.html', restaurant=restaurant)
    except:
        return redirect(url_for('errorRestaurant', error='Retrieving restaurant'))
    

@app.route('/restaurant/<int:restaurant_id>/delete', methods=['POST', 'GET'])
def deleteRestaurant(restaurant_id):
    if request.method == 'POST':
        try:
            restaurant = cursor.query(Restaurant).get(restaurant_id)
            
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
        return render_template('deleteRestaurant.html', restaurant=restaurant)
    except:
        return redirect(url_for('errorRestaurant', error='Retrieving restaurant'))
    

@app.route('/restaurant/<int:restaurant_id>')
@app.route('/restaurant/<int:restaurant_id>/menu', methods=['GET'])
def showMenu(restaurant_id):
    """
    try:
        restaurants = cursor.query(Restaurant).all()
    except:
        restaurants = None
    return render_template('restaurants.html', restaurants=restaurants)
    """

    try:
        restaurant = cursor.query(Restaurant).get(restaurant_id)
        menus = cursor.query(Menu).filter_by(restaurant_id=restaurant_id).all()    
    except:
        return redirect(url_for('errorRestaurant', error='Retrieving menus or restaurant'))
    return render_template('menu.html', restaurant=restaurant, menus=menus)

@app.route('/restaurant/<int:restaurant_id>/menu/new', methods=['POST', 'GET'])
def newMenuItem(restaurant_id):
    if request.method == 'POST':
        try:
            restaurant = cursor.query(Restaurant).get(restaurant_id)
            
            menu_name = request.form['menu_name']
            menu_price = float(request.form['menu_price'])
            menu_description = request.form['menu_description']
            
            new_menu = Menu(name=menu_name, price=menu_price, description=menu_description, restaurant_id=restaurant_id, restaurant=restaurant)
            
            cursor.add(new_menu)
            cursor.commit()
            
            flash('Menu Item successfully Created', 'success')
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))
        except:
            return redirect(url_for('errorRestaurant'))
    try:
        restaurant = cursor.query(Restaurant).get(restaurant_id)
        return render_template('newMenuItem.html', restaurant=restaurant)
    except:
        return redirect(url_for('errorRestaurant', error='Retrieving restaurant'))

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
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
        return render_template('editMenuItem.html', restaurant=restaurant, menu=menu)
    except:
        return redirect(url_for('errorRestaurant', error='Retrieving menu or restaurant'))
        

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if request.method == 'POST':
        try:
            restaurant = cursor.query(Restaurant).get(restaurant_id)
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
        return render_template('deleteMenuItem.html', restaurant=restaurant, menu=menu)
    except:
        return redirect(url_for('errorRestaurant', error='Retrieving menu or restaurant'))
    
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