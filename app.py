from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import os
import pytesseract
import pyscreenshot as ImageGrab
from PIL import Image
from yolov5 import YOLOv5
from datetime import date, datetime, timezone


def create_app():
    db = SQLAlchemy()
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://///Users/gaurabbhattarai/PycharmProjects/EMS/instance/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'your-secret-key'
    app.config['MAIL_SERVER'] = 'your-mail-server'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your-email@example.com'
    app.config['MAIL_PASSWORD'] = 'your-email-password'
    db.init_app(app)
    model = YOLOv5("yolov5s.pt", device="cpu")
    current_datetime = datetime.now

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        name = db.Column(db.String(120))
        password = db.Column(db.String(120), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)

        def __init__(self, email, name, password, is_admin=False):
            self.email = email
            self.name = name
            self.password = password
            self.is_admin = is_admin

    with app.app_context():
        db.create_all()
        admin_user = User.query.filter_by(email='gaurabbhattarai29@gmail.com').first()
        if not admin_user:
            admin_user = User(email='gaurabbhattarai29@gmail.com', name='Admin',
                              password='d09154c8b29a10d6f8f91ff9d4487c2731187dcb62660575d0e2e32007d6ca91',
                              is_admin=True)
            db.session.add(admin_user)
            db.session.commit()

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = ''

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/home')
    def home():
        return render_template('home.html')

    @app.route('/')
    def home2():
        return render_template('home.html')

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

    @app.route('/users')
    def get_all_users():
        users = User.query.all()
        for user in users:
            print(f"User {user.id}: {user.name} ({user.email}, {user.password})")
        return "User data printed in the terminal"

    @app.route('/admin', methods=['GET', 'POST'])
    @login_required
    def admin_panel():
        if not current_user.is_admin:
            error = "You do not have access to that"
            return render_template("home.html", error=error)

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'create':
                return redirect(url_for('admin-create'))

            elif action == 'edit':
                return redirect(url_for('admin-edit'))

        users = User.query.all()
        return render_template('admin_panel.html', users=users)

    @app.route('/admin-create-user', methods=['GET', 'POST'])
    @login_required
    def admin_create():
        if not current_user.is_admin:
            error = "You do not have access to that"
            return render_template("home.html", error=error)

        if request.method == 'POST':
            email = request.form['email']
            full_name = request.form['name']
            password = request.form['password']

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                error_message = "User already exists"
                return render_template('admin_create.html', error_message=error_message)
            else:
                new_user = User(email=email, name=full_name, password=password)
                db.session.add(new_user)
                db.session.commit()
                success_message = "New user created successfully"
                return render_template('admin_create.html', success_message=success_message)

        return render_template('admin_create.html')

    @app.route('/admin-edit-user-search', methods=['GET', 'POST'])
    @login_required
    def admin_edit_search():
        if not current_user.is_admin:
            error = "You do not have access to that"
            return render_template("home.html", error=error)

        if request.method == 'POST':
            search_email = request.form['search_email']
            users = User.query.filter(User.email.like(f"%{search_email}%")).all()
        else:
            users = []

        return render_template('admin_edit_user_search.html', users=users)

    @app.route('/admin-edit-user/<int:user_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_user(user_id):
        if not current_user.is_admin:
            error = "You do not have access to that"
            return render_template("home.html", error=error)

        user = User.query.get(user_id)
        if not user:
            return "User not found."

        if request.method == 'POST':
            action = request.form['action']
            if action == 'Update User':
                user.email = request.form['email']
                user.name = request.form['name']
                user.password = request.form['password']
                db.session.commit()
                success_edit = 'User edit updated successfully'
                return render_template('admin_edit.html', user=user, success_edit=success_edit)
            elif action == 'delete':
                db.session.delete(user)
                db.session.commit()
                success_delete = 'User deleted successfully'
                return render_template('admin_edit_user_search.html', success_delete=success_delete)

        return render_template('admin_edit.html', user=user)

    def capture_screenshot(filepath):
        screenshot = ImageGrab.grab()
        screenshot.save(filepath)

    def extract_text_from_image(image_path):
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image)
        return extracted_text

    def save_text_to_file(text, text_filepath):
        with open(text_filepath, 'w') as file:
            file.write(text)

    @app.route('/assistant', methods=['GET', 'POST'])
    def assistant():
        if not current_user.is_authenticated:
            error = "Login or signup to continue"
            return render_template("home.html", error=error)
        user_id = current_user.id
        user_folder = "ScreenshotFolder/"+"User "+str(user_id)
        screenshot_filepath = user_folder+"/screenshot"+str(user_id)+str(current_datetime)+".png"
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
            print("New user folder created")
        capture_screenshot(screenshot_filepath)
        print(user_folder, screenshot_filepath, user_id)
        extracted_text = ''
        if request.method == 'POST':
            run = request.form.get('run')
            if run == 'submit':
                extracted_text = extract_text_from_image(screenshot_filepath)
                text_filepath = "/Users/gaurabbhattarai/PycharmProjects/EMS/TextFolder/TextSaved"+str(user_id)+".txt"
                if os.path.exists(text_filepath):
                    os.remove(text_filepath)
                save_text_to_file(extracted_text, text_filepath)
            if run == 'reset':
                text_filepath = "/Users/gaurabbhattarai/PycharmProjects/EMS/TextFolder/TextSaved"+str(user_id)+".txt"
                extracted_text = ''
                save_text_to_file(extracted_text, text_filepath)
        return render_template('assistant_page.html', user_id=user_id, extracted_text=extracted_text)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        logout_success = "Successfully logged out"
        return render_template("home.html", logout=logout_success)

    @app.route('/register')
    def registerpage():
        return render_template('email_verification.html')

    @app.route('/registersuccess', methods=['GET', 'POST'])
    def registersuccess():
        if request.method == 'POST':
            email = request.form['email']
            full_name = request.form['name']
            password = request.form['password']
            new_user = User.query.filter_by(email=email).first()
            if '@' not in email:
                error = 'Invalid email format'
                return render_template('email_verification.html', error=error)
            elif new_user:
                return render_template('existingaccount.html')
            else:
                new_user = User(email=email, name=full_name, password=password)
                db.session.add(new_user)
                db.session.commit()
                return render_template('registersuccess.html', email=email)
    return app


app = create_app()

if __name__ == '__name__':
    app.run(debug=True)
