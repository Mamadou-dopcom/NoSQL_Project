#C'est la classe qui nous permet de declarer tout nos base de données 
from flask_sqlalchemy import SQLAlchemy 

db = SQLAlchemy()

class UserFavs(db.Model):
	username = db.Column(db.String, primary_key=True)
	place = db.Column(db.String)
	country = db.Column(db.String)

	def __init__(self, username, place, country):
		self.username=username
		self.place=place
		self.country=country

	def __repr__(self):
		return f'<User-Place-country : {self.username}-{self.place}-{self.country}'

