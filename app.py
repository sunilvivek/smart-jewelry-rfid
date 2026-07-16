from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import qrcode
import csv
import os

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32).hex())
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jewelry.db"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 86400

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "error"


def log_audit(action, details="", item_id=None):
    entry = AuditLog(
        user=current_user.username if current_user.is_authenticated else "system",
        action=action,
        details=details,
        item_id=item_id,
    )
    db.session.add(entry)
    db.session.commit()


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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(500))
    item_id = db.Column(db.Integer, nullable=True)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    pincode = db.Column(db.String(10))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sales = db.relationship("Sale", backref="customer", lazy=True)
    repairs = db.relationship("Repair", backref="customer", lazy=True)


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    jewelry_id = db.Column(db.Integer, db.ForeignKey("jewelry.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    sale_price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(30), default="Cash")
    notes = db.Column(db.Text)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    jewelry = db.relationship("Jewelry", backref="sales_record", lazy=True)


class Repair(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repair_id = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    jewelry_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    estimated_cost = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    status = db.Column(db.String(20), default="Pending")
    received_date = db.Column(db.DateTime, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page Not Found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Internal Server Error"), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template("login.html")

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            login_user(admin)
            flash(f"Welcome back, {admin.username}!", "success")
            return redirect("/")

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect("/login")


@app.route("/")
@login_required
def home():
    items = Jewelry.query.all()

    total_items = len(items)
    total_weight = round(sum(item.weight or 0 for item in items), 2)
    total_value = round(sum(item.price or 0 for item in items), 2)
    available_stock = len([i for i in items if i.status == "Available"])

    gold_items = [i for i in items if i.metal_type == "Gold"]
    silver_items = [i for i in items if i.metal_type == "Silver"]

    gold_count = len(gold_items)
    silver_count = len(silver_items)
    gold_weight = round(sum(i.weight or 0 for i in gold_items), 2)
    silver_weight = round(sum(i.weight or 0 for i in silver_items), 2)
    gold_value = round(sum(i.price or 0 for i in gold_items), 2)
    silver_value = round(sum(i.price or 0 for i in silver_items), 2)

    return render_template(
        "home.html",
        total_items=total_items,
        total_weight=total_weight,
        total_value=total_value,
        available_stock=available_stock,
        gold_count=gold_count,
        silver_count=silver_count,
        gold_weight=gold_weight,
        silver_weight=silver_weight,
        gold_value=gold_value,
        silver_value=silver_value,
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_jewelry():
    if request.method == "POST":
        rfid_id = request.form.get("rfid_id", "").strip()
        ornament_name = request.form.get("ornament_name", "").strip()
        metal_type = request.form.get("metal_type", "").strip()
        weight_str = request.form.get("weight", "").strip()
        purity = request.form.get("purity", "").strip()
        price_str = request.form.get("price", "").strip()

        if not all([rfid_id, ornament_name, metal_type, weight_str, purity, price_str]):
            flash("All fields are required.", "error")
            return render_template("add_jewelry.html")

        try:
            weight = float(weight_str)
            price = float(price_str)
        except ValueError:
            flash("Weight and Price must be valid numbers.", "error")
            return render_template("add_jewelry.html")

        if weight <= 0 or price <= 0:
            flash("Weight and Price must be positive values.", "error")
            return render_template("add_jewelry.html")

        if metal_type not in ("Gold", "Silver"):
            flash("Metal type must be Gold or Silver.", "error")
            return render_template("add_jewelry.html")

        existing = Jewelry.query.filter_by(rfid_id=rfid_id).first()
        if existing:
            flash(f"RFID '{rfid_id}' already exists in inventory.", "error")
            return render_template("add_jewelry.html")

        jewelry = Jewelry(
            rfid_id=rfid_id,
            ornament_name=ornament_name,
            weight=weight,
            purity=purity,
            price=price,
            metal_type=metal_type,
            status="Available",
        )
        db.session.add(jewelry)
        db.session.commit()

        qr = qrcode.make(jewelry.rfid_id)
        os.makedirs("static/qrcodes", exist_ok=True)
        qr.save(os.path.join("static/qrcodes", f"{secure_filename(jewelry.rfid_id)}.png"))

        log_audit("add_item", f"Added {ornament_name} ({metal_type}) RFID:{rfid_id}", jewelry.id)
        flash(f"{ornament_name} added to inventory successfully.", "success")
        return redirect("/")

    return render_template("add_jewelry.html")


@app.route("/inventory")
@login_required
def inventory():
    search = request.args.get("search", "").strip()
    metal = request.args.get("metal", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

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
                Jewelry.status.like(like_term),
                Jewelry.purity.like(like_term),
            )
        )

    query = query.order_by(Jewelry.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "inventory.html",
        items=pagination.items,
        pagination=pagination,
        active_filter=metal,
        search_query=search,
    )


@app.route("/inventory/gold")
@login_required
def inventory_gold():
    return redirect(url_for("inventory", metal="Gold"))


@app.route("/inventory/silver")
@login_required
def inventory_silver():
    return redirect(url_for("inventory", metal="Silver"))


@app.route("/export/csv")
@login_required
def export_csv():
    metal = request.args.get("metal", "").strip()
    search = request.args.get("search", "").strip()

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
            )
        )

    items = query.order_by(Jewelry.id.desc()).all()

    output = []
    output.append(["ID", "RFID", "Ornament Name", "Metal Type", "Weight (g)", "Purity", "Price (₹)", "Status", "Created At"])
    for item in items:
        output.append([
            item.id,
            item.rfid_id,
            item.ornament_name,
            item.metal_type,
            item.weight,
            item.purity,
            item.price,
            item.status,
            item.created_at.strftime("%d-%b-%Y %H:%M") if item.created_at else "",
        ])

    log_audit("export_csv", f"Exported {len(items)} items to CSV")

    si = "\ufeff" + "\n".join([",".join(str(cell) for cell in row) for row in output])
    return Response(
        si,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"},
    )


@app.route("/scan", methods=["GET", "POST"])
@login_required
def scan():
    item = None
    scanned_rfid = ""
    not_found = False

    if request.method == "POST":
        scanned_rfid = request.form.get("rfid_id", "").strip()
        if scanned_rfid:
            item = Jewelry.query.filter_by(rfid_id=scanned_rfid).first()
            if not item:
                not_found = True
                flash(f"No item found with RFID '{scanned_rfid}'.", "warning")
            else:
                log_audit("scan_item", f"Scanned RFID:{scanned_rfid}", item.id)

    return render_template("scan.html", item=item, scanned_rfid=scanned_rfid, not_found=not_found)


@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_item(id):
    item = db.session.get(Jewelry, id)
    if not item:
        flash("Item not found.", "error")
        return redirect("/inventory")

    name = item.ornament_name
    rfid = item.rfid_id

    qr_path = os.path.join("static/qrcodes", f"{secure_filename(rfid)}.png")
    if os.path.exists(qr_path):
        os.remove(qr_path)

    db.session.delete(item)
    db.session.commit()

    log_audit("delete_item", f"Deleted {name} (RFID:{rfid})", id)
    flash(f"{name} deleted from inventory.", "success")
    return redirect("/inventory")


@app.route("/sold/<int:id>", methods=["GET", "POST"])
@login_required
def mark_sold(id):
    item = db.session.get(Jewelry, id)
    if not item:
        flash("Item not found.", "error")
        return redirect("/inventory")

    if item.status != "Available":
        flash("This item is not available for sale.", "error")
        return redirect("/inventory")

    if request.method == "POST":
        customer_id_str = request.form.get("customer_id", "").strip()
        sale_price_str = request.form.get("sale_price", "").strip()
        payment_method = request.form.get("payment_method", "Cash").strip()
        notes = request.form.get("notes", "").strip()

        if not customer_id_str:
            flash("Please select a customer.", "error")
            customers = Customer.query.order_by(Customer.full_name).all()
            return render_template("sell.html", item=item, customers=customers)

        try:
            customer_id = int(customer_id_str)
        except ValueError:
            flash("Invalid customer selected.", "error")
            customers = Customer.query.order_by(Customer.full_name).all()
            return render_template("sell.html", item=item, customers=customers)

        customer = db.session.get(Customer, customer_id)
        if not customer:
            flash("Customer not found.", "error")
            customers = Customer.query.order_by(Customer.full_name).all()
            return render_template("sell.html", item=item, customers=customers)

        if not sale_price_str:
            flash("Sale price is required.", "error")
            customers = Customer.query.order_by(Customer.full_name).all()
            return render_template("sell.html", item=item, customers=customers)

        try:
            sale_price = float(sale_price_str)
        except ValueError:
            flash("Sale price must be a valid number.", "error")
            customers = Customer.query.order_by(Customer.full_name).all()
            return render_template("sell.html", item=item, customers=customers)

        if sale_price <= 0:
            flash("Sale price must be a positive value.", "error")
            customers = Customer.query.order_by(Customer.full_name).all()
            return render_template("sell.html", item=item, customers=customers)

        if payment_method not in ("Cash", "Card", "UPI", "Bank Transfer", "Other"):
            payment_method = "Cash"

        item.status = "Sold"
        item.updated_at = datetime.utcnow()

        sale = Sale(
            invoice_number=generate_invoice_number(),
            jewelry_id=item.id,
            customer_id=customer.id,
            sale_price=sale_price,
            payment_method=payment_method,
            notes=notes,
        )
        db.session.add(sale)
        db.session.commit()

        log_audit("mark_sold", f"Sold {item.ornament_name} (RFID:{item.rfid_id}) to {customer.full_name} for \u20b9{sale_price:,.0f} [{sale.invoice_number}]", id)
        flash(f"{item.ornament_name} sold to {customer.full_name}. Invoice: {sale.invoice_number}", "success")
        return redirect(f"/sales/{sale.id}")

    customers = Customer.query.order_by(Customer.full_name).all()
    return render_template("sell.html", item=item, customers=customers)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_item(id):
    item = db.session.get(Jewelry, id)
    if not item:
        flash("Item not found.", "error")
        return redirect("/inventory")

    if request.method == "POST":
        ornament_name = request.form.get("ornament_name", "").strip()
        metal_type = request.form.get("metal_type", "").strip()
        weight_str = request.form.get("weight", "").strip()
        purity = request.form.get("purity", "").strip()
        price_str = request.form.get("price", "").strip()
        status = request.form.get("status", "").strip()

        if not all([ornament_name, metal_type, weight_str, purity, price_str, status]):
            flash("All fields are required.", "error")
            return render_template("edit.html", item=item)

        try:
            weight = float(weight_str)
            price = float(price_str)
        except ValueError:
            flash("Weight and Price must be valid numbers.", "error")
            return render_template("edit.html", item=item)

        if weight <= 0 or price <= 0:
            flash("Weight and Price must be positive values.", "error")
            return render_template("edit.html", item=item)

        if metal_type not in ("Gold", "Silver"):
            flash("Metal type must be Gold or Silver.", "error")
            return render_template("edit.html", item=item)

        if status not in ("Available", "Sold"):
            flash("Invalid status.", "error")
            return render_template("edit.html", item=item)

        item.ornament_name = ornament_name
        item.weight = weight
        item.purity = purity
        item.price = price
        item.status = status
        item.metal_type = metal_type
        item.updated_at = datetime.utcnow()
        db.session.commit()

        log_audit("edit_item", f"Updated {ornament_name} (RFID:{item.rfid_id})", id)
        flash(f"{ornament_name} updated successfully.", "success")
        return redirect("/inventory")

    return render_template("edit.html", item=item)


@app.route("/generate_all_qr")
@login_required
def generate_all_qr():
    items = Jewelry.query.all()
    os.makedirs("static/qrcodes", exist_ok=True)

    count = 0
    for item in items:
        qr = qrcode.make(item.rfid_id)
        qr.save(os.path.join("static/qrcodes", f"{secure_filename(item.rfid_id)}.png"))
        count += 1

    log_audit("generate_qr", f"Generated QR codes for {count} items")
    flash(f"QR codes generated for {count} items.", "success")
    return redirect("/inventory")


@app.route("/print_qr/<int:id>")
def print_qr(id):
    item = db.session.get(Jewelry, id)
    if not item:
        return render_template("error.html", code=404, message="Item Not Found"), 404
    return render_template("print_qr.html", item=item)


@app.route("/bill/<int:id>")
@login_required
def bill(id):
    item = db.session.get(Jewelry, id)
    if not item:
        flash("Item not found.", "error")
        return redirect("/inventory")
    sale = Sale.query.filter_by(jewelry_id=item.id).first()
    return render_template("bill.html", item=item, sale=sale)


@app.route("/sales")
@login_required
def sales_history():
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    query = Sale.query

    if search:
        like_term = f"%{search}%"
        query = query.join(Jewelry).join(Customer).filter(
            db.or_(
                Sale.invoice_number.like(like_term),
                Jewelry.ornament_name.like(like_term),
                Jewelry.rfid_id.like(like_term),
                Customer.full_name.like(like_term),
                Customer.phone_number.like(like_term),
            )
        )

    query = query.order_by(Sale.sale_date.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template("sales.html", sales=pagination.items, pagination=pagination, search_query=search)


@app.route("/sales/<int:id>")
@login_required
def sale_detail(id):
    sale = db.session.get(Sale, id)
    if not sale:
        flash("Sale record not found.", "error")
        return redirect("/sales")
    return render_template("sale_detail.html", sale=sale)


@app.route("/audit")
@login_required
def audit_log():
    page = request.args.get("page", 1, type=int)
    per_page = 30
    pagination = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("audit.html", logs=pagination.items, pagination=pagination)


def generate_customer_id():
    last = Customer.query.order_by(Customer.id.desc()).first()
    if last and last.customer_id:
        num = int(last.customer_id.replace("CUST", "")) + 1
    else:
        num = 1
    return f"CUST{num:06d}"


def generate_invoice_number():
    last = Sale.query.order_by(Sale.id.desc()).first()
    if last and last.invoice_number:
        num = int(last.invoice_number.replace("INV", "")) + 1
    else:
        num = 1
    return f"INV{num:06d}"


def generate_repair_id():
    last = Repair.query.order_by(Repair.id.desc()).first()
    if last and last.repair_id:
        num = int(last.repair_id.replace("REP", "")) + 1
    else:
        num = 1
    return f"REP{num:06d}"


@app.route("/customers")
@login_required
def customers():
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    query = Customer.query

    if search:
        like_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Customer.customer_id.like(like_term),
                Customer.full_name.like(like_term),
                Customer.phone_number.like(like_term),
                Customer.email.like(like_term),
            )
        )

    query = query.order_by(Customer.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "customers.html",
        customers=pagination.items,
        pagination=pagination,
        search_query=search,
    )


@app.route("/customers/add", methods=["GET", "POST"])
@login_required
def add_customer():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        pincode = request.form.get("pincode", "").strip()
        notes = request.form.get("notes", "").strip()

        if not full_name or not phone_number:
            flash("Full Name and Phone Number are required.", "error")
            return render_template("add_customer.html")

        if not phone_number.isdigit() or len(phone_number) < 10:
            flash("Phone number must be at least 10 digits.", "error")
            return render_template("add_customer.html")

        if email and "@" not in email:
            flash("Please enter a valid email address.", "error")
            return render_template("add_customer.html")

        existing = Customer.query.filter_by(phone_number=phone_number).first()
        if existing:
            flash(f"Phone number '{phone_number}' is already registered to {existing.full_name}.", "error")
            return render_template("add_customer.html")

        customer = Customer(
            customer_id=generate_customer_id(),
            full_name=full_name,
            phone_number=phone_number,
            email=email,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            notes=notes,
        )
        db.session.add(customer)
        db.session.commit()

        log_audit("add_customer", f"Added customer {full_name} ({customer.customer_id})")
        flash(f"Customer {full_name} added successfully.", "success")
        return redirect("/customers")

    return render_template("add_customer.html")


@app.route("/customers/<int:id>")
@login_required
def customer_profile(id):
    customer = db.session.get(Customer, id)
    if not customer:
        flash("Customer not found.", "error")
        return redirect("/customers")

    sales = Sale.query.filter_by(customer_id=customer.id).order_by(Sale.sale_date.desc()).all()
    repairs = Repair.query.filter_by(customer_id=customer.id).order_by(Repair.created_at.desc()).all()

    total_spent = sum(s.sale_price for s in sales)
    total_repairs = len(repairs)
    active_repairs = len([r for r in repairs if r.status in ("Pending", "In Progress")])

    return render_template(
        "customer_profile.html",
        customer=customer,
        sales=sales,
        repairs=repairs,
        total_spent=total_spent,
        total_repairs=total_repairs,
        active_repairs=active_repairs,
    )


@app.route("/customers/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_customer(id):
    customer = db.session.get(Customer, id)
    if not customer:
        flash("Customer not found.", "error")
        return redirect("/customers")

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        pincode = request.form.get("pincode", "").strip()
        notes = request.form.get("notes", "").strip()

        if not full_name or not phone_number:
            flash("Full Name and Phone Number are required.", "error")
            return render_template("edit_customer.html", customer=customer)

        if not phone_number.isdigit() or len(phone_number) < 10:
            flash("Phone number must be at least 10 digits.", "error")
            return render_template("edit_customer.html", customer=customer)

        if email and "@" not in email:
            flash("Please enter a valid email address.", "error")
            return render_template("edit_customer.html", customer=customer)

        existing = Customer.query.filter(
            Customer.phone_number == phone_number, Customer.id != id
        ).first()
        if existing:
            flash(f"Phone number '{phone_number}' is already registered to {existing.full_name}.", "error")
            return render_template("edit_customer.html", customer=customer)

        customer.full_name = full_name
        customer.phone_number = phone_number
        customer.email = email
        customer.address = address
        customer.city = city
        customer.state = state
        customer.pincode = pincode
        customer.notes = notes
        customer.updated_at = datetime.utcnow()
        db.session.commit()

        log_audit("edit_customer", f"Updated customer {full_name} ({customer.customer_id})")
        flash(f"Customer {full_name} updated successfully.", "success")
        return redirect(f"/customers/{id}")

    return render_template("edit_customer.html", customer=customer)


@app.route("/customers/delete/<int:id>", methods=["POST"])
@login_required
def delete_customer(id):
    customer = db.session.get(Customer, id)
    if not customer:
        flash("Customer not found.", "error")
        return redirect("/customers")

    name = customer.full_name
    cid = customer.customer_id

    db.session.delete(customer)
    db.session.commit()

    log_audit("delete_customer", f"Deleted customer {name} ({cid})")
    flash(f"Customer {name} deleted successfully.", "success")
    return redirect("/customers")


@app.route("/repairs")
@login_required
def repairs():
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    query = Repair.query

    if status_filter in ("Pending", "In Progress", "Completed"):
        query = query.filter_by(status=status_filter)

    if search:
        like_term = f"%{search}%"
        query = query.join(Customer).filter(
            db.or_(
                Repair.repair_id.like(like_term),
                Repair.jewelry_name.like(like_term),
                Customer.full_name.like(like_term),
                Customer.phone_number.like(like_term),
            )
        )

    query = query.order_by(Repair.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    pending_count = Repair.query.filter_by(status="Pending").count()
    in_progress_count = Repair.query.filter_by(status="In Progress").count()
    completed_count = Repair.query.filter_by(status="Completed").count()

    return render_template(
        "repairs.html",
        repairs=pagination.items,
        pagination=pagination,
        search_query=search,
        status_filter=status_filter,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
    )


@app.route("/repairs/add", methods=["GET", "POST"])
@login_required
def add_repair():
    if request.method == "POST":
        customer_id_str = request.form.get("customer_id", "").strip()
        jewelry_name = request.form.get("jewelry_name", "").strip()
        description = request.form.get("description", "").strip()
        estimated_cost_str = request.form.get("estimated_cost", "").strip()
        notes = request.form.get("notes", "").strip()

        if not customer_id_str or not jewelry_name:
            flash("Customer and Jewelry Name are required.", "error")
            customers = Customer.query.order_by(Customer.full_name).all()
            return render_template("add_repair.html", customers=customers)

        try:
            customer_id = int(customer_id_str)
        except ValueError:
            flash("Invalid customer selected.", "error")
            customers = Customer.query.order_by(Customer.full_name).all()
            return render_template("add_repair.html", customers=customers)

        customer = db.session.get(Customer, customer_id)
        if not customer:
            flash("Customer not found.", "error")
            customers = Customer.query.order_by(Customer.full_name).all()
            return render_template("add_repair.html", customers=customers)

        estimated_cost = None
        if estimated_cost_str:
            try:
                estimated_cost = float(estimated_cost_str)
                if estimated_cost < 0:
                    flash("Estimated cost must be a positive value.", "error")
                    customers = Customer.query.order_by(Customer.full_name).all()
                    return render_template("add_repair.html", customers=customers)
            except ValueError:
                flash("Estimated cost must be a valid number.", "error")
                customers = Customer.query.order_by(Customer.full_name).all()
                return render_template("add_repair.html", customers=customers)

        repair = Repair(
            repair_id=generate_repair_id(),
            customer_id=customer.id,
            jewelry_name=jewelry_name,
            description=description,
            estimated_cost=estimated_cost,
            notes=notes,
        )
        db.session.add(repair)
        db.session.commit()

        log_audit("add_repair", f"Added repair {repair.repair_id} for {customer.full_name} - {jewelry_name}")
        flash(f"Repair {repair.repair_id} created for {customer.full_name}.", "success")
        return redirect("/repairs")

    customers = Customer.query.order_by(Customer.full_name).all()
    return render_template("add_repair.html", customers=customers)


@app.route("/repairs/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_repair(id):
    repair = db.session.get(Repair, id)
    if not repair:
        flash("Repair not found.", "error")
        return redirect("/repairs")

    if request.method == "POST":
        jewelry_name = request.form.get("jewelry_name", "").strip()
        description = request.form.get("description", "").strip()
        estimated_cost_str = request.form.get("estimated_cost", "").strip()
        actual_cost_str = request.form.get("actual_cost", "").strip()
        status = request.form.get("status", "").strip()
        notes = request.form.get("notes", "").strip()

        if not jewelry_name:
            flash("Jewelry Name is required.", "error")
            return render_template("edit_repair.html", repair=repair)

        if status not in ("Pending", "In Progress", "Completed"):
            flash("Invalid status.", "error")
            return render_template("edit_repair.html", repair=repair)

        estimated_cost = None
        if estimated_cost_str:
            try:
                estimated_cost = float(estimated_cost_str)
            except ValueError:
                flash("Estimated cost must be a valid number.", "error")
                return render_template("edit_repair.html", repair=repair)

        actual_cost = None
        if actual_cost_str:
            try:
                actual_cost = float(actual_cost_str)
            except ValueError:
                flash("Actual cost must be a valid number.", "error")
                return render_template("edit_repair.html", repair=repair)

        was_completed = repair.status != "Completed" and status == "Completed"

        repair.jewelry_name = jewelry_name
        repair.description = description
        repair.estimated_cost = estimated_cost
        repair.actual_cost = actual_cost
        repair.status = status
        repair.notes = notes
        repair.updated_at = datetime.utcnow()

        if was_completed:
            repair.completed_date = datetime.utcnow()

        db.session.commit()

        log_audit("edit_repair", f"Updated repair {repair.repair_id} - status: {status}")
        flash(f"Repair {repair.repair_id} updated successfully.", "success")
        return redirect(f"/repairs/{id}")

    return render_template("edit_repair.html", repair=repair)


@app.route("/repairs/<int:id>")
@login_required
def repair_detail(id):
    repair = db.session.get(Repair, id)
    if not repair:
        flash("Repair not found.", "error")
        return redirect("/repairs")
    return render_template("repair_detail.html", repair=repair)


@app.route("/repairs/delete/<int:id>", methods=["POST"])
@login_required
def delete_repair(id):
    repair = db.session.get(Repair, id)
    if not repair:
        flash("Repair not found.", "error")
        return redirect("/repairs")

    rid = repair.repair_id
    customer_name = repair.customer.full_name

    db.session.delete(repair)
    db.session.commit()

    log_audit("delete_repair", f"Deleted repair {rid} for {customer_name}")
    flash(f"Repair {rid} deleted successfully.", "success")
    return redirect("/repairs")


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new_pass = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if not check_password_hash(current_user.password, current):
            flash("Current password is incorrect.", "error")
            return render_template("change_password.html")

        if len(new_pass) < 6:
            flash("New password must be at least 6 characters.", "error")
            return render_template("change_password.html")

        if new_pass != confirm:
            flash("New passwords do not match.", "error")
            return render_template("change_password.html")

        current_user.password = generate_password_hash(new_pass)
        db.session.commit()

        log_audit("change_password", "Password changed")
        flash("Password changed successfully.", "success")
        return redirect("/")

    return render_template("change_password.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        try:
            db.session.execute(db.text("SELECT metal_type FROM jewelry LIMIT 1"))
        except Exception:
            db.session.execute(
                db.text("ALTER TABLE jewelry ADD COLUMN metal_type VARCHAR(20) DEFAULT 'Gold'")
            )
            db.session.commit()

        try:
            db.session.execute(db.text("SELECT created_at FROM jewelry LIMIT 1"))
        except Exception:
            db.session.execute(
                db.text("ALTER TABLE jewelry ADD COLUMN created_at DATETIME")
            )
            db.session.commit()

        try:
            db.session.execute(db.text("SELECT updated_at FROM jewelry LIMIT 1"))
        except Exception:
            db.session.execute(
                db.text("ALTER TABLE jewelry ADD COLUMN updated_at DATETIME")
            )
            db.session.commit()

        for table in ["sale", "repair"]:
            try:
                db.session.execute(db.text(f"SELECT 1 FROM {table} LIMIT 1"))
            except Exception:
                pass

        if not Admin.query.filter_by(username="admin").first():
            admin = Admin(
                username="admin",
                password=generate_password_hash("balaji123"),
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin created (admin / balaji123)")

    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.environ.get("FLASK_PORT", 8000))
    app.run(debug=debug, port=port)
