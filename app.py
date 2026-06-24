from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import qrcode
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jewelry.db'

db = SQLAlchemy(app)

class Jewelry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rfid_id = db.Column(db.String(100), unique=True)
    ornament_name = db.Column(db.String(100))
    weight = db.Column(db.Float)
    purity = db.Column(db.String(20))
    price = db.Column(db.Float)
    status = db.Column(db.String(20))

@app.route('/')
def home():

    items = Jewelry.query.all()

    total_items = len(items)

    total_weight = sum(item.weight for item in items)

    total_value = sum(item.price for item in items)

    available_stock = len([
    item for item in items
    if item.status == "Available"
])

    return render_template(
        'home.html',
        total_items=total_items,
        total_weight=total_weight,
        total_value=total_value,
        available_stock=available_stock
    )
@app.route('/add', methods=['GET', 'POST'])
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
            status="Available"
        )

        db.session.add(jewelry)
        db.session.commit()

        qr = qrcode.make(jewelry.rfid_id)
        qr.save(f"static/qrcodes/{jewelry.rfid_id}.png")

        return redirect('/')

    return render_template('add_jewelry.html')

@app.route('/inventory')
def inventory():

    search = request.args.get('search')

    if search:

        items = Jewelry.query.filter(
            Jewelry.rfid_id.contains(search)
        ).all()

    else:

        items = Jewelry.query.all()

    return render_template(
        'inventory.html',
        items=items
    )
    
@app.route('/scan', methods=['GET', 'POST'])
def scan():

    item = None

    if request.method == 'POST':

        rfid = request.form['rfid_id']

        item = Jewelry.query.filter_by(
            rfid_id=rfid
        ).first()

    return render_template(
        'scan.html',
        item=item
    )

@app.route('/delete/<int:id>')
def delete_item(id):

    item = Jewelry.query.get(id)

    qr_path = f"static/qrcodes/{item.rfid_id}.png"

    if os.path.exists(qr_path):
        os.remove(qr_path)

    db.session.delete(item)
    db.session.commit()

    return redirect('/inventory')

@app.route('/sold/<int:id>')
def mark_sold(id):

    item = Jewelry.query.get(id)

    item.status = "Sold"

    db.session.commit()

    return redirect('/inventory')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):

    item = Jewelry.query.get_or_404(id)

    if request.method == 'POST':

        item.ornament_name = request.form['ornament_name']
        item.weight = float(request.form['weight'])
        item.purity = request.form['purity']
        item.price = float(request.form['price'])
        item.status = request.form['status']

        db.session.commit()

        return redirect('/inventory')

    return render_template(
        'edit.html',
        item=item
    )
@app.route('/generate_all_qr')
def generate_all_qr():

    items = Jewelry.query.all()

    for item in items:
        qr = qrcode.make(item.rfid_id)
        qr.save(f"static/qrcodes/{item.rfid_id}.png")

    return "All QR Codes Generated Successfully!"

@app.route('/print_qr/<int:id>')
def print_qr(id):

    item = Jewelry.query.get_or_404(id)

    return render_template(
        'print_qr.html',
        item=item
    )

@app.route('/test123')
def test123():
    return "ROUTE WORKING"
@app.route('/items')
def items():
    all_items = Jewelry.query.all()
    return str([(i.id, i.rfid_id) for i in all_items])


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True, port=8000)
