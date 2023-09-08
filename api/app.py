import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from functools import wraps
from slugify import slugify


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ogonda'
app.config['UPLOAD_FOLDER'] = 'api/static/images'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://sql11645133:zdSP4TbvUF@sql11.freesqldatabase.com:3306/sql11645133'


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'


class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default='admin')

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to perform this action.', 'danger')
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)
    return decorated_view

# Admin registration route
@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_admin = Admin(username=username, password_hash=hashed_password)
        db.session.add(new_admin)
        db.session.commit()

        flash('Admin account created successfully!', 'success')
        return redirect(url_for('admin_login'))

    return render_template('admin_register.html')

# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()

        if admin and bcrypt.check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('index'))
        else:
            flash('Admin login failed. Please check your credentials.', 'danger')

    return render_template('admin_login.html')

# Admin logout route
@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

# Create the 'Post' model for representing blog posts
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True, nullable=False)

# Create post and delete post routes
@app.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files['image']

        # Generate the slug from the post title
        slug = slugify(title)

        if image:
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))

        new_post = Post(title=title, content=content, image=image.filename, slug=slug)
        db.session.add(new_post)
        db.session.commit()

        flash('Post created successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('create_post.html')

@app.route('/delete/<string:slug>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_post(slug):
    post = Post.query.filter_by(slug=slug).first()

    if request.method == 'POST':
        db.session.delete(post)
        db.session.commit()

        flash('Post deleted successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('delete_post.html', post=post)

@app.route('/edit/<string:slug>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(slug):
    post = Post.query.filter_by(slug=slug).first()

    if not post:
        flash('Post not found', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['content']

        # Generate a new slug based on the updated title
        new_slug = slugify(new_title)

        post.title = new_title
        post.content = new_content
        post.slug = new_slug  # Update the slug with the new one
        db.session.commit()

        flash('Post updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_post.html', post=post)


# Default route to view all posts
@app.route('/')
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('index.html', posts=posts)


# Route to display the content of a blog post
@app.route('/mixxes/<string:slug>')
def content(slug):
    post = Post.query.filter_by(slug=slug).first()
    return render_template('mixxes.html', post=post)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
