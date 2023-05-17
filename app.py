from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import datetime as time


def create_app():
    db = SQLAlchemy()
    app = Flask(__name__)
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'your-secret-key'
    db.init_app(app)

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        name = db.Column(db.String(120))
        password = db.Column(db.String(120), nullable=False)

        def __init__(self, email, name, password):
            self.email = email
            self.name = name
            self.password = password

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'loginpage'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/home')
    def home():
        return render_template('home.html')

    @app.route('/')
    def home2():
        return render_template('home.html')

    @app.route('/users')
    def get_all_users():
        users = User.query.all()
        for user in users:
            print(f"User {user.id}: {user.name} ({user.email}, {user.password})")
        return "User data printed in the terminal"

    @app.route('/login', methods=['GET', 'POST'])
    def loginpage():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            if user is None or not user.password == password:
                error = 'Invalid email or password'
                return render_template('login.html', error=error)
            login_user(user)
            return redirect(url_for('home'))
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('home'))

    @app.route('/register')
    def registerpage():
        return render_template('register.html')

    @app.route('/registersuccess', methods=['GET', 'POST'])
    def registersuccess():
        if request.method == 'POST':
            email = request.form['email']
            full_name = request.form['name']
            password = request.form['password']
            new_user = User.query.filter_by(email=email).first()
            if '@' not in email:
                error = 'Invalid email format'
                return render_template('register.html', error=error)
            elif new_user:
                return render_template('existingaccount.html')
            else:
                new_user = User(email=email, name=full_name, password=password)
                db.session.add(new_user)
                db.session.commit()
                return render_template('registersuccess.html', email=email)
    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)