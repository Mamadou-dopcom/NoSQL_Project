from flask import Flask, request, render_template
import redis

app = Flask(__name__)

# postgresql://username:password@host:port/database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev'

from models import db, UserFavs

db.init_app(app)
with app.app_context():
    # Pour créer / utiliser la base de données mentionnée dans l'URI
    db.create_all()
    db.session.commit()

red = redis.Redis(host='redis', port=6379, db=0)

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/save", methods=['POST'])
def save():
    username = str(request.form['username']).lower()
    place = str(request.form['place']).lower()
    country = str(request.form['country']).lower()

    # vérifier si les données du nom d'utilisateur existent déjà dans le redis
    if red.hgetall(username).keys():
        print("hget nom d'utilisateur:", red.hgetall(username))
        # renvoie un message au template, indiquant que l'utilisateur existe déjà (à partir de redis)
        return render_template('index.html', user_exists=1, msg='(From Redis)', username=username, place=red.hget(username,"place").decode('utf-8'), country=red.hget(username,"country").decode('utf-8'))

    # si ce n'est pas dans redis, alors on vérifie dans la base de données postgres
    elif len(list(red.hgetall(username)))==0:
        record =  UserFavs.query.filter_by(username=username).first()
        print("Records fecthed from db:", record)
        
        if record:
            red.hset(username, "place", place)
            red.hset(username, "country", country)
            # retourne un msg au template, disant que l'utilisateur existe déjà (depuis la base de données)
            return render_template('index.html', user_exists=1, msg='(From DataBase)', username=username, place=record.place, country=record.country)

    # si les données du nom d'utilisateur n'existent nulle part, on crée un nouvel enregistrement dans la base de données et stockez-le également dans Redis
    # créer un nouvel enregistrement dans la base de données
    new_record = UserFavs(username=username, place=place, country=country)
    db.session.add(new_record)
    db.session.commit()

    # enregistrer dans Redis aussi
    red.hset(username, "place", place)
    red.hset(username, "country", country)

    # vérification croisée de la réussite de l'insertion de l'enregistrement dans la base de données
    record =  UserFavs.query.filter_by(username=username).first()
    print("Enregistrements récupérés a partir de la base de données postgres après l'insertion :", record)

    # renvoie un message de réussite lors de la sauvegarde
    return render_template('index.html', saved=1, username=username, place=red.hget(username, "place").decode('utf-8'), country=red.hget(username, "country").decode('utf-8'))

@app.route("/keys", methods=['GET'])
def keys():
	records = UserFavs.query.all()
	names = []
	for record in records:
		names.append(record.username)
	return render_template('index.html', keys=1, usernames=names)


@app.route("/get", methods=['POST'])
def get():
	username = request.form['username']
	print("Username:", username)
	user_data = red.hgetall(username)
	print("GET Redis:", user_data)

	if not user_data:
		record = UserFavs.query.filter_by(username=username).first()
		print("GET Record:", record)
		if not record:
			print("Pas cette donnée dans redis ou postgres")
			return render_template('index.html', no_record=1, msg=f"Enregistrement non encore fait pour {username}")
		red.hset(username, "place", record.place)
		red.hset(username, "country", record.country)
		return render_template('index.html', get=1, msg="(From DataBase)",username=username, place=record.place, country=record.country)
	return render_template('index.html',get=1, msg="(From Redis)", username=username, place=user_data[b'place'].decode('utf-8'), country=user_data[b'country'].decode('utf-8'))