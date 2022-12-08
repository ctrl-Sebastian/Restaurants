
from flask import Flask


app = Flask(__name__)

#oauth config

app.config['SECRET_KEY'] = 'd8df5a63801e9701cc6b9c04b5872992'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurants.db'

import restaurants.routes