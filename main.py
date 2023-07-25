import requests
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("Secret-Key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies-collection.db"
bootstrap = Bootstrap5(app)

db = SQLAlchemy()

db.init_app(app)

# API for fetching movies details

url = "https://api.themoviedb.org/3/search/movie"
detail_url = "https://api.themoviedb.org/3/movie/"

params = {
    'query' : "",
    'language' : "en-US"
}

headers = {
    "accept": "application/json",
    "Authorization": os.environ.get("Auth")
}


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True,  autoincrement=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'<Book {self.title}>'


class EditForm(FlaskForm):
    rating = FloatField('Enter your Rating out of 10 e.g 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    done = SubmitField('Done')


class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    add = SubmitField('Add Movie')


#------------------------------ Only for creating DataBase-------------------------------------#

# with app.app_context():
#     db.create_all()

# with app.app_context():
#     new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()

#-----------------------------------------------------------------------------------------------#

@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars()
    i = 1
    for movie in movies:
        movie.ranking = i
        i += 1
    db.session.commit()
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars()
    return render_template("index.html", movies=movies)


@app.route("/edit", methods=["POST", "GET"])
def edit():

    form = EditForm()
    id = request.args.get("id")

    if form.validate_on_submit() and request.method == "POST":
        data = form.data
        movie = db.get_or_404(Movie, id)
        movie.rating = data['rating']
        movie.review = data['review']
        db.session.commit()
        return redirect(url_for("home"))

    movie = db.get_or_404(Movie, id)
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete():
    id = request.args.get("id")
    movie = db.get_or_404(Movie, id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["POST", "GET"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        title = form.data['title']
        params['query'] = title
        response = requests.get(url, params=params, headers=headers)
        data = response.json()['results']
        return render_template("select.html", data=data)

    return render_template("add.html", form=form)


@app.route('/details')
def get_details():
    id = request.args.get("id")
    response = requests.get(detail_url + str(id) + "?language=en-US", headers=headers).json()
    movie = Movie(
        title = response['original_title'],
        year = int(response['release_date'].split("-")[0]),
        description = response['overview'],
        img_url="https://image.tmdb.org/t/p/w500" + response['poster_path']
    )
    db.session.add(movie)
    db.session.commit()
    return redirect(url_for("edit", id=movie.id))


if __name__ == '__main__':
    app.run(debug=True)
