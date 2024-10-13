from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, logout_user, LoginManager, UserMixin, current_user
import bcrypt
from flask_session import Session
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__, template_folder="templates")
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:cOpyarGO56@niffy-database.cveaaey865r1.eu-north-1.rds.amazonaws.com:3306/niffy'
app.config['SECRET_KEY'] = 'adehhtt56cssdv'

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

Session(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)

PASSWORD = 'ade34$$&ght103pre4&$$' 
bcrypt_salt_rounds = 12

class Cake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(100))
    title = db.Column(db.Text)
    high_price= db.Column(db.String(20))
    low_price = db.Column(db.String(20))
    description = db.Column(db.String(255))
    description1 = db.Column(db.String(255))
    description2 = db.Column(db.String(255))
    
    
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id    
    
# Create the database tables
with app.app_context():
    db.create_all()
    
@login_manager.user_loader 
def load_user(user_id):
    return Cake.query.get(int(user_id))      

@login_manager.user_loader 
def load_user(user_id):
    return User(user_id)   
    
@app.route('/')
def index():
    cakes = Cake.query.all()
    cakes.reverse()
    return render_template('index.html', cakes=cakes, user=current_user)
  
@app.route('/success')
def success():
    return render_template('success.html') 
 
@app.route('/message')
def message():
    return render_template('message.html')  

@app.route('/upload3456g$32', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        image = request.files['image']
        title = request.form['title']
        high_price = request.form['high_price'].replace(',', '')  # Remove existing commas if any
        low_price = request.form['low_price'].replace(',', '')  # Remove existing commas if any
        description = request.form['description']
        description1 = request.form['description1']
        description2 = request.form['description2']

        # Ensure file extensions are valid
        allowed_image_extensions = {'.png'}

        image_extension = os.path.splitext(image.filename)[1].lower()
        if image_extension not in allowed_image_extensions:
            flash("Invalid image file format. Please use PNG.", category="error")
            return redirect(url_for('upload'))

        image_filename = secure_filename(image.filename)
        # Save the movie file to a specific directory
        image.save(os.path.join('static', 'cakes_img', image_filename))
        
        high_price = "{:,.0f}".format(float(high_price))
        low_price = "{:,.0f}".format(float(low_price))

        # Create a Series object and save it to the database
        cakes = Cake(
            image=image_filename,
            title=title,
            high_price=high_price,
            low_price=low_price,
            description=description,
            description1=description1,
            description2=description2,
        )

        db.session.add(cakes)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('upload.html')     

@app.route('/cake-info/<int:cake_id>')
def cake_info(cake_id):
    cake = Cake.query.get(cake_id)
    return render_template('cake_info.html', cake=cake)

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/delete_cake/<int:cake_id>', methods=['POST'])
def delete_cake(cake_id):
    cake = Cake.query.get(cake_id)
    
    if cake:
        # Delete the cake from the database
        db.session.delete(cake)
        db.session.commit()
        flash('Cake deleted successfully', 'success')
    else:
        flash('Cake not found', 'danger')

    return redirect(url_for('index'))

from flask import session

# 'add_to_cart' route
@app.route('/add_to_cart/<int:cake_id>', methods=['POST'])
def add_to_cart(cake_id):
    if 'cart' not in session:
        session['cart'] = {}

    cake = Cake.query.get(cake_id)
    if cake:
        try:
            price = float(cake.high_price.replace(',', ''))  # Ensure price is converted to a float
        except ValueError:
            flash('Invalid price for the item', 'danger')
            return redirect(url_for('index'))

        item = {
            'id': cake.id,
            'title': cake.title,
            'price': price,
            'quantity': 1  # Add initial quantity
        }

        user_session_id = session.sid  # Get the user's session ID
        if user_session_id not in session['cart']:
            session['cart'][user_session_id] = []

        cart = session['cart'][user_session_id]

        # Check if the item is already in the cart
        for cart_item in cart:
            if cart_item['id'] == cake.id:
                cart_item['quantity'] += 1
                break
        else:
            session['cart'][user_session_id].append(item)

        session.modified = True  # Ensure the session is saved after modification
        flash('Item added to the cart', 'success')
    else:
        flash('Cake not found', 'danger')

    return redirect(url_for('index'))

# 'view_cart' route
@app.route('/cart')
def view_cart():
    user_session_id = session.sid  # Get the user's session ID

    if 'cart' in session and user_session_id in session['cart']:
        cart = session['cart'][user_session_id]
    else:
        cart = []

    total_price = 0
    total_plus_1000 = 0

    for item in cart:
        try:
            price = float(item['price']) * item['quantity']  # Calculate total price based on quantity
            total_price += price
        except ValueError:
            # Handle invalid price values here, such as logging the issue or setting a default value.
            pass

        total_plus_1000 = total_price + 1000
     # Format total_price and total_plus_1000 with commas
    total_price = "{:,.0f}".format(total_price)
    total_plus_1000 = "{:,.0f}".format(total_plus_1000)    

    # Check if the user's cart is not empty
    if cart:
        return render_template('cart.html', cart=cart, total_price=total_price, total_plus_1000=total_plus_1000)
    else:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('index'))

@app.route('/increase_quantity/<int:cake_id>', methods=['POST'])
def increase_quantity(cake_id):
    user_session_id = session.sid  # Get the user's session ID

    if 'cart' in session and user_session_id in session['cart']:
        cart = session['cart'][user_session_id]
        for item in cart:
            if item['id'] == cake_id:
                item['quantity'] += 1
                break
        session.modified = True  # Ensure the session is saved after modification
        flash('Increased quantity of the item', 'success')
    else:
        flash('Item not found in the cart', 'danger')

    return redirect(url_for('view_cart'))

@app.route('/decrease_quantity/<int:cake_id>', methods=['POST'])
def decrease_quantity(cake_id):
    user_session_id = session.sid  # Get the user's session ID

    if 'cart' in session and user_session_id in session['cart']:
        cart = session['cart'][user_session_id]
        for item in cart:
            if item['id'] == cake_id:
                if item['quantity'] > 1:
                    item['quantity'] -= 1
                else:
                    cart.remove(item)
                break
        session.modified = True  # Ensure the session is saved after modification
        flash('Decreased quantity of the item', 'success')
    else:
        flash('Item not found in the cart', 'danger')

    return redirect(url_for('view_cart'))

    
    
@app.route('/remove_from_cart/<int:cake_id>', methods=['POST'])
def remove_from_cart(cake_id):
    user_session_id = session.sid  # Get the user's session ID

    if 'cart' in session and user_session_id in session['cart']:
        cart = session['cart'][user_session_id]
        # Find the item with the specified cake_id and remove it
        for item in cart:
            if item['id'] == cake_id:
                cart.remove(item)
                break
        session.modified = True  # Ensure the session is saved after modification
    else:
        flash('Item not found in the cart', 'danger')

    return redirect(url_for('view_cart'))
    


@app.route('/submit_form', methods=['POST'])
def submit_form():
    subject = "Nathaniel, Someone Ordered"
    sender = "nathanielademola499@gmail.com"
    recipients = ["nathanielademola499@gmail.com"]
    password = "cadf mkse ldzs jtxh"

    name = request.form.get('name')
    address = request.form.get('address')
    phone = request.form.get('phone')
    message = request.form.get('message')
    item_titles = request.form.getlist('item_titles[]')
    item_prices = request.form.getlist('item_prices[]')
    item_quantities = request.form.getlist('item_quantities[]')
    item_total = request.form.get('item_total[]')
    delivery = request.form.get('delivery[]')

    # Create a detailed body for the email
    body = (
        f"Name: {name}\n"
        f"Address: {address}\n"
        f"Phone: {phone}\n"
        f"Message: {message}\n\n"
        "Order Details:\n"
    )

    for title, price, quantity in zip(item_titles, item_prices, item_quantities):
        body += f"Product: {title}\nPrice: {price}\nQuantity: {quantity}\n\n"

    body += f"Total: {item_total}\nSubtotal: {delivery}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, recipients, msg.as_string())
            
        # Clear the user's cart session after successfully placing the order
        session.pop('cart', None)
    except Exception as e:
        flash(f"Error placing order: {str(e)}", category="error")  
        return redirect(url_for('cart_view'))  
    
    return redirect(url_for('success'))

@app.route('/contact_form', methods=['POST'])
def contact_form():
    # Extract form data
    subject = "Nathaniel - Message From Your Website"
    sender = "nathanielademola499@gmail.com"
    recipients = ["nathanielademola499@gmail.com"]
    password = "cadf mkse ldzs jtxh"

    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    phone = request.form.get('phone')
    message = request.form.getlist('message')
    

    body = f"Name: {name}\nEmail: {email}\nSubject: {subject}\nPhone: {phone}\nMessage: {message}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, recipients, msg.as_string())
    except Exception as e:
        flash(f"Error sending message:", category="error")  
        return redirect(url_for('contact_form'))    
    
    return redirect(url_for('message'))

@app.route('/cancel_cart', methods=['POST'])
def cancel_cart():
    # Clear the cart by removing the 'cart' key from the session.
    session.pop('cart', None)
    flash('All Items Removed from Cart.', 'success')
    return redirect(url_for('index'))


@app.route('/login4578@thotfwdeh', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password_attempt = request.form.get('password')
        
        hashed_password = bcrypt.hashpw("ade34$$&ght103pre4&$$".encode('utf-8'), bcrypt.gensalt(bcrypt_salt_rounds))

        if bcrypt.checkpw(password_attempt.encode('utf-8'), hashed_password):
            user = User(1)
            login_user(user)
            flash('Logged in successfully!', category='success')
            return redirect(url_for('upload'))
        else:
            flash('Incorrect password, try again.', category='error')

    return render_template("login.html")


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('index'))   

if __name__ == '__main__':
    app.run(debug=True)
