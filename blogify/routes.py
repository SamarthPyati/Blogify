import os
from flask import redirect, render_template, request, url_for, flash, abort, jsonify
from sqlalchemy.engine import url
from PIL import Image
import secrets
from blogify import app, db, bcrypt, mail
from blogify.forms import PostForm, RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm
from blogify.models import User, Post, PostReaction
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(per_page=4, page=page)
    return render_template("home.html", posts=posts, title="Home")


@app.route("/about")
def about():
    return render_template("about.html", title="About")

@app.route("/search")
def search():
    query = request.args.get('query')
    page = request.args.get('page', 1, type=int)
    if query:
        posts = Post.query.filter(Post.title.contains(query) | Post.content.contains(query)).paginate(page=page, per_page=5)
    else:
        posts = Post.query.paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    # checks if from was validated when submitted
    if form.validate_on_submit():
        # Hash the password entered by the user
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        # Flash message generated
        flash(f"Your account was succesfully created for {form.username.data}. You can now log in.", category='success')
        return redirect(url_for('login'))
    return render_template("register.html", title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            # next is url trying to access without loging in
            # we will return this same url if user logs in as it would be conveinient for user
            _next = request.args.get('next')
            return redirect(_next) if _next else redirect(url_for('home'))
        else:
            flash(f"Login unsuccessful. Please check email and password.", category='danger')
    return render_template("login.html", title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/post/<int:post_id>/react", methods=['POST'])
@login_required
def react_to_post(post_id):
    reaction_type = request.json.get('reaction_type')  # Expected: 'like' or 'dislike'

    if reaction_type not in ['like', 'dislike']:
        return jsonify({"error": "Invalid reaction type"}), 400

    post = Post.query.get_or_404(post_id)

    # Check if the user has already reacted to this post
    existing_reaction = PostReaction.query.filter_by(post_id=post_id, user_id=current_user.id).first()

    if existing_reaction:
        # If the user has already reacted, update their reaction
        if existing_reaction.reaction_type == reaction_type:
            # If they are trying to react the same way again, remove the reaction
            db.session.delete(existing_reaction)
            if reaction_type == 'like':
                post.likes_count -= 1
            else:
                post.dislikes_count -= 1
        else:
            # If they had a different reaction, change it
            existing_reaction.reaction_type = reaction_type
            if reaction_type == 'like':
                post.likes_count += 1
                post.dislikes_count -= 1
            else:
                post.dislikes_count += 1
                post.likes_count -= 1
    else:
        # If the user has not reacted before, create a new reaction
        new_reaction = PostReaction(post_id=post_id, user_id=current_user.id, reaction_type=reaction_type)
        db.session.add(new_reaction)
        if reaction_type == 'like':
            post.likes_count += 1
        else:
            post.dislikes_count += 1

    db.session.commit()
    return jsonify({"message": "Reaction updated successfully", "likes": post.likes_count, "dislikes": post.dislikes_count}), 200


@app.route("/post/<int:post_id>/reactions", methods=['GET'])
@login_required
def get_reactions(post_id):
    post = Post.query.get_or_404(post_id)

    # Get the total count of likes and dislikes
    likes_count = post.likes_count
    dislikes_count = post.dislikes_count

    # Check if the current user has already reacted to this post
    existing_reaction = PostReaction.query.filter_by(post_id=post_id, user_id=current_user.id).first()

    # If the user has reacted, return their reaction type ('like' or 'dislike')
    user_reaction = None
    if existing_reaction:
        user_reaction = existing_reaction.reaction_type

    return jsonify({
        "likes": likes_count,
        "dislikes": dislikes_count,
        "user_reaction": user_reaction  # This will be None if the user has not reacted
    }), 200



def save_picture(form_picture) -> str:
    ''' Converting the image to a hex name to ensure it doesn't collide with any other image name '''
    if form_picture is None:
        raise ValueError("form_picture cannot be None")
    
    hex_name = secrets.token_hex(8)
    _, ext = os.path.splitext(form_picture.filename)
    pic_name = hex_name + ext
    pic_path = os.path.join(app.root_path, 'static/profile_pics', pic_name)
    
    try:
        output_size = (125, 125)
        resized = Image.open(form_picture)
        resized = resized.resize(output_size, resample=Image.Resampling.LANCZOS)
        resized.save(pic_path)
    except Exception as e:
        raise Exception("Error occurred while saving image: {}".format(str(e)))
    
    return pic_name


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            pic_file = save_picture(form.picture.data)
            current_user.profile_pic = pic_file
        current_user.username = form.username.data
        current_user.email = form.email.data  
        db.session.commit()
        flash("Your account has been updated successfully!", category='success')
        return redirect(url_for('account'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email  # Corrected line
    image_file = url_for('static', filename='profile_pics/' + current_user.profile_pic)
    return render_template("account.html", title='Account', image_file=image_file, form=form)

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created succesfully!", category='success')
        return redirect(url_for('home'))
    return render_template("create_post.html", title="New Post", form=form, legend="New Post")

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != 'admin' and current_user != post.author:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Post has been updated successfully!", category="success")
        return redirect(url_for("post", post_id=post_id))
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template("create_post.html", title="Update Post", form=form, legend="Update Post")

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != 'admin' and current_user != post.author:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted successfully!", category="success")
    return redirect(url_for("home"))

@app.route("/user/<string:username>")
@login_required
def user_posts(username: str):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(per_page=2, page=page)
    return render_template("user_posts.html", posts=posts, user=user, title="User")

def send_reset_email(user: User):
    token = user.get_reset_token()
    msg = Message('BLOGIFY: Password Reset Request', 
        sender='samarthpyati@gmail.com',
        recipients=[user.email]
        )
    
    msg.html = f'''<b>To reset your password, visit the following link</b>
    <br>
    
    {url_for('reset_token', token=token, _external=True)}
    
    <br>
    <b><i>If you did not make this request, then simply ignore this email.</i></b>
    '''

    mail.send(msg)
    

@app.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        flash("You must be logged out before resetting password.", "warning")
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash("An email has been sent with instructions to reset your password.", "success")
        return redirect(url_for('login'))

    return render_template('reset_requests.html', title='Reset Password', form=form)

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        flash("You must be logged out before resetting password.", "warning")
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash("This is an invalid or expired token.", "warning")
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_pw
        db.session.commit()
        flash(f"The password is updated.", category='success')
    return render_template('reset_token.html', title='Reset Password', form=form)
