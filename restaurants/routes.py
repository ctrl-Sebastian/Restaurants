from flask import Flask, render_template, url_for, flash, redirect, request
from restaurants import app, db
from restaurants.models import Restaurant, Menu

@app.route('/')
@app.route('/restaurants')
def showRestaurants():
    #return "This page will show all restaurants"
    try:
        restaurants = db.query(Restaurant).all()
    except:
        restaurants = None
    return render_template('restaurants.html', restaurants = restaurants)


@app.route('/restaurant/new')
def newRestaurant():
    return "This page will be for making new restaurant"


@app.route('/restaurant/<int:restaurant_id>/edit')
def editRestaurant(restaurant_id):
    return "This page will be for editing restaurnt %s" % restaurant_id


@app.route('/restaurant/<int:restaurant_id>/delete')
def deleteRestaurant(restaurant_id):
    return "This page will be for deleting restaurant %s" % restaurant_id


@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    return "This page id for the menu for the restaurant %s" % restaurant_id


@app.route('/restaurant/<int:restaurant_id>/menu/new')
def newMenuItem(restaurant_id):
    return "This page is for making a new menu item for restaurant %s" % restaurant_id


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit')
def editMenuItem(restaurant_id, menu_id):
    return "This page is for editing menu item %s from restaurant" % menu_id


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete')
def deleteMenuItem(restaurant_id, menu_id):
    return "Tis page is for deleting menu item %s" % menu_id

