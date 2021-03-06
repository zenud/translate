from flask import Flask, render_template, url_for
import tr.py

app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)


@app.route("/load")
def about():
    return render_template('load.html', title='Load')


if __name__ == '__main__':
    app.run(debug=True)
