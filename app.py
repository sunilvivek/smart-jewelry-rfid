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


@app.route("/sold/<int:id>", methods=["POST"])
@login_required
def mark_sold(id):
    item = db.session.get(Jewelry, id)
    if not item:
        flash("Item not found.", "error")
        return redirect("/inventory")

    item.status = "Sold"
    item.updated_at = datetime.utcnow()
    db.session.commit()

    log_audit("mark_sold", f"Marked {item.ornament_name} (RFID:{item.rfid_id}) as Sold", id)
    flash(f"{item.ornament_name} marked as sold.", "success")
    return redirect("/inventory")


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
    return render_template("bill.html", item=item)


@app.route("/sales")
@login_required
def sales_history():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    pagination = Jewelry.query.filter_by(status="Sold").order_by(Jewelry.updated_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("sales.html", items=pagination.items, pagination=pagination)


@app.route("/audit")
@login_required
def audit_log():
    page = request.args.get("page", 1, type=int)
    per_page = 30
    pagination = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("audit.html", logs=pagination.items, pagination=pagination)


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
