from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import qrcode
import os

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "balaji_jewellers_secret_2026"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jewelry.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Jewelry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rfid_id = db.Column(db.String(100), unique=True)
    ornament_name = db.Column(db.String(100))
    weight = db.Column(db.Float)
    purity = db.Column(db.String(20))
    price = db.Column(db.Float)
    status = db.Column(db.String(20))
    metal_type = db.Column(db.String(20), default="Gold")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            login_user(admin)
            return redirect("/")

        return "Invalid Username or Password"

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/")
@login_required
def home():
    items = Jewelry.query.all()

    total_items = len(items)
    total_weight = sum(item.weight for item in items)
    total_value = sum(item.price for item in items)
    available_stock = len([i for i in items if i.status == "Available"])

    gold_items = [i for i in items if i.metal_type == "Gold"]
    silver_items = [i for i in items if i.metal_type == "Silver"]

    gold_count = len(gold_items)
    silver_count = len(silver_items)
    gold_weight = sum(i.weight for i in gold_items)
    silver_weight = sum(i.weight for i in silver_items)
    gold_value = sum(i.price for i in gold_items)
    silver_value = sum(i.price for i in silver_items)

    return render_template(
        'home.html',
        total_items=total_items,
        total_weight=total_weight,
        total_value=total_value,
        available_stock=available_stock,
        gold_count=gold_count,
        silver_count=silver_count,
        gold_weight=gold_weight,
        silver_weight=silver_weight,
        gold_value=gold_value,
        silver_value=silver_value
    )


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_jewelry():
    if request.method == 'POST':
        existing = Jewelry.query.filter_by(
            rfid_id=request.form['rfid_id']
        ).first()

        if existing:
            return "RFID already exists!"

        jewelry = Jewelry(
            rfid_id=request.form['rfid_id'],
            ornament_name=request.form['ornament_name'],
            weight=float(request.form['weight']),
            purity=request.form['purity'],
            price=float(request.form['price']),
            metal_type=request.form['metal_type'],
            status="Available"
        )

        db.session.add(jewelry)
        db.session.commit()

        qr = qrcode.make(jewelry.rfid_id)
        qr.save(f"static/qrcodes/{jewelry.rfid_id}.png")

        return redirect('/')

    return render_template('add_jewelry.html')


@app.route('/inventory')
@login_required
def inventory():
    search = request.args.get('search', '').strip()
    metal = request.args.get('metal', '').strip()

    query = Jewelry.query

    if metal in ("Gold", "Silver"):
        query = query.filter_by(metal_type=metal)

    if search:
        like_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Jewelry.rfid_id.like(like_term),
                Jewelry.ornament_name.like(like_term),
                Jewelry.metal_type.like(like_term),
                Jewelry.status.like(like_term)
            )
        )

    items = query.all()

    return render_template(
        'inventory.html',
        items=items,
        active_filter=metal,
        search_query=search
    )


@app.route('/inventory/gold')
@login_required
def inventory_gold():
    return redirect(url_for('inventory', metal='Gold'))


@app.route('/inventory/silver')
@login_required
def inventory_silver():
    return redirect(url_for('inventory', metal='Silver'))


@app.route('/scan', methods=['GET', 'POST'])
@login_required
def scan():
    item = None

    if request.method == 'POST':
        rfid = request.form['rfid_id']
        item = Jewelry.query.filter_by(rfid_id=rfid).first()

    return render_template('scan.html', item=item)


@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_item(id):
    item = Jewelry.query.get(id)
    qr_path = f"static/qrcodes/{item.rfid_id}.png"

    if os.path.exists(qr_path):
        os.remove(qr_path)

    db.session.delete(item)
    db.session.commit()

    return redirect('/inventory')


@app.route('/sold/<int:id>', methods=['POST'])
@login_required
def mark_sold(id):
    item = Jewelry.query.get(id)
    item.status = "Sold"
    db.session.commit()

    return redirect('/inventory')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    item = Jewelry.query.get_or_404(id)

    if request.method == 'POST':
        item.ornament_name = request.form['ornament_name']
        item.weight = float(request.form['weight'])
        item.purity = request.form['purity']
        item.price = float(request.form['price'])
        item.status = request.form['status']
        item.metal_type = request.form['metal_type']

        db.session.commit()
        return redirect('/inventory')

    return render_template('edit.html', item=item)


@app.route('/generate_all_qr')
@login_required
def generate_all_qr():
    items = Jewelry.query.all()

    for item in items:
        qr = qrcode.make(item.rfid_id)
        qr.save(f"static/qrcodes/{item.rfid_id}.png")

    return "All QR Codes Generated Successfully!"


@app.route('/print_qr/<int:id>')
def print_qr(id):
    item = Jewelry.query.get_or_404(id)
    return render_template('print_qr.html', item=item)


@app.route('/test123')
@login_required
def test123():
    return "ROUTE WORKING"


@app.route('/items')
@login_required
def items():
    all_items = Jewelry.query.all()
    return str([(i.id, i.rfid_id) for i in all_items])


@app.route('/bill/<int:id>')
@login_required
def bill(id):
    item = Jewelry.query.get_or_404(id)
    return render_template('bill.html', item=item)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Migration: add metal_type column if missing (SQLite)
        try:
            db.session.execute(
                db.text("SELECT metal_type FROM jewelry LIMIT 1")
            )
        except Exception:
            db.session.execute(
                db.text("ALTER TABLE jewelry ADD COLUMN metal_type VARCHAR(20) DEFAULT 'Gold'")
            )
            db.session.commit()

        if not Admin.query.filter_by(username="admin").first():
            admin = Admin(
                username="admin",
                password=generate_password_hash("balaji123")
            )
            db.session.add(admin)
            db.session.commit()
            print("Default Admin Created")

    app.run(debug=True, port=8000)
