from datetime import date, datetime
from functools import wraps
from pathlib import Path
import os
import secrets

import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, flash, g, redirect, render_template, request, session, url_for, send_file, abort


BASE_DIR = Path(__file__).resolve().parent
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "1234")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "hotel")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "hotel-management-demo-key")

ROOM_RANGES = {
    "single": range(1, 51),
    "double": range(51, 101),
    "triple": range(101, 151),
    "quad": range(151, 201),
    "deluxe": range(201, 226),
    "suite": range(226, 251),
    "presidential": range(251, 261),
}
ROOM_CATALOG = {
    "single": {"guests": 1, "size": 22, "bed": "Queen bed", "rate": 1800, "image": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=88"},
    "double": {"guests": 2, "size": 30, "bed": "King bed", "rate": 2800, "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=88"},
    "triple": {"guests": 3, "size": 42, "bed": "King bed", "rate": 3900, "image": "https://images.unsplash.com/photo-1584132967334-10e028bd69f7?auto=format&fit=crop&w=1200&q=88"},
    "quad": {"guests": 4, "size": 58, "bed": "King bed", "rate": 5200, "image": "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=88"},
    "deluxe": {"guests": 2, "size": 38, "bed": "King bed", "rate": 9500, "image": "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=1200&q=88"},
    "suite": {"guests": 3, "size": 72, "bed": "California king", "rate": 14000, "image": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=1200&q=88"},
    "presidential": {"guests": 4, "size": 110, "bed": "Luxury king bed", "rate": 22000, "image": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=88"},
}
ROOM_RATES = {k: v["rate"] for k, v in ROOM_CATALOG.items()}
ROOM_GALLERIES = {
    "single": [
        ROOM_CATALOG["single"]["image"],
        "https://images.unsplash.com/photo-1540518614846-7eded433c457?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=700&q=88",
    ],
    "double": [
        ROOM_CATALOG["double"]["image"],
        "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=700&q=88",
    ],
    "triple": [
        ROOM_CATALOG["triple"]["image"],
        "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=700&q=88",
    ],
    "quad": [
        ROOM_CATALOG["quad"]["image"],
        "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1618220179428-22790b461013?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=700&q=88",
    ],
    "deluxe": [
        ROOM_CATALOG["deluxe"]["image"],
        "https://images.unsplash.com/photo-1590490359854-dfba19688d70?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1600566753051-f0b89df2dd90?auto=format&fit=crop&w=700&q=88",
    ],
    "suite": [
        ROOM_CATALOG["suite"]["image"],
        "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1615529162924-f8605388461d?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=700&q=88",
    ],
    "presidential": [
        ROOM_CATALOG["presidential"]["image"],
        "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1600210491892-03d54c0aaf87?auto=format&fit=crop&w=700&q=88",
        "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=700&q=88",
    ],
}
ROOM_DETAILS = {
    "single": {
        "amenities": ["Hairdryer", "Luxury toiletries", "Complimentary bottled water", "Fresh towels on request"],
        "facilities": ["Work desk", "Flat-screen TV", "Air conditioning", "High-speed Wi-Fi", "Mini-fridge", "Digital safe"],
        "features": ["Quiet single-bed layout", "City or garden view", "Daily housekeeping", "24-hour front desk"],
    },
    "double": {
        "amenities": ["Hairdryer", "Premium toiletries", "Tea and coffee station", "Complimentary bottled water"],
        "facilities": ["King bed", "Flat-screen TV", "Air conditioning", "High-speed Wi-Fi", "Mini-fridge", "Digital safe"],
        "features": ["Comfortable seating area", "Large windows", "Dedicated work desk", "Daily housekeeping"],
    },
    "triple": {
        "amenities": ["Family toiletries", "Hairdryer", "Tea and coffee station", "Three bath towel sets"],
        "facilities": ["King bed and extra bed", "Smart TV", "Air conditioning", "High-speed Wi-Fi", "Mini-fridge", "Digital safe"],
        "features": ["Spacious family layout", "Dining or lounge corner", "Large windows", "Flexible sleeping arrangement"],
    },
    "quad": {
        "amenities": ["Premium toiletries", "Hairdryer", "Tea and coffee station", "Complimentary welcome basket"],
        "facilities": ["King bed and twin beds", "Smart TV", "Air conditioning", "High-speed Wi-Fi", "Mini-fridge", "Digital safe"],
        "features": ["Large family living space", "Private balcony where applicable", "Dining table", "Priority housekeeping"],
    },
    "deluxe": {
        "amenities": ["Luxury toiletries", "Bathrobe and slippers", "Nespresso coffee machine", "Welcome fruit platter"],
        "facilities": ["Premium king bed", "55-inch Smart TV", "Climate control", "High-speed Wi-Fi", "Mini-bar", "Electronic safe"],
        "features": ["Panoramic city view", "Separate lounge chair", "Rain shower", "Evening turndown service"],
    },
    "suite": {
        "amenities": ["Luxury bath amenities", "Bathrobe and slippers", "Nespresso coffee machine", "Daily minibar refresh"],
        "facilities": ["California king bed", "Living room", "55-inch Smart TVs", "Premium Wi-Fi", "Walk-in wardrobe", "Electronic safe"],
        "features": ["Separate bedroom and lounge", "Private balcony", "Rain shower and soaking tub", "Complimentary breakfast"],
    },
    "presidential": {
        "amenities": ["Signature luxury toiletries", "Silk bathrobes and slippers", "Private butler service", "Daily gourmet welcome hamper"],
        "facilities": ["Luxury king bedroom", "Private living and dining room", "Home cinema system", "Premium Wi-Fi", "Full minibar", "Walk-in wardrobe"],
        "features": ["Private terrace with panoramic view", "Executive workspace", "Soaking tub and rainfall shower", "Complimentary airport transfer"],
    },
}


class MySQLDatabase:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()


def connect_mysql(database=MYSQL_DATABASE):
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=database,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def get_db():
    if "db" not in g:
        g.db = MySQLDatabase(connect_mysql())
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    server = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, autocommit=True)
    server.cursor().execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}`")
    server.close()
    db = MySQLDatabase(connect_mysql())
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS guest (
            guestid INT PRIMARY KEY NOT NULL,
            nameofguest VARCHAR(50),
            type_of_room VARCHAR(20),
            noofdays INT,
            cidate DATE,
            codate DATE,
            room_no INT,
            source_of_booking VARCHAR(10),
            netpay DECIMAL(12,2)
        );
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS staff (
            id INT PRIMARY KEY NOT NULL,
            name VARCHAR(50),
            dept VARCHAR(30),
            sal DECIMAL(12,2),
            hiredate DATE
        );
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS permanent_guest (
            permanent_guest_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            original_guest_id INT NULL,
            nameofguest VARCHAR(50),
            type_of_room VARCHAR(20),
            noofdays INT,
            cidate DATE,
            codate DATE,
            room_no INT,
            source_of_booking VARCHAR(10),
            netpay DECIMAL(12,2),
            booking_token VARCHAR(64) NULL,
            booking_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            checkout_at DATETIME NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'Booked',
            PRIMARY KEY (permanent_guest_id),
            UNIQUE KEY uq_permanent_guest_booking_token (booking_token),
            KEY idx_permanent_guest_original_id (original_guest_id)
        );
        """
    )
    db.execute(
        """
        INSERT INTO permanent_guest
            (original_guest_id, nameofguest, type_of_room, noofdays, cidate, codate,
             room_no, source_of_booking, netpay, booking_token, status)
        SELECT g.guestid, g.nameofguest, g.type_of_room, g.noofdays, g.cidate, g.codate,
               g.room_no, g.source_of_booking, g.netpay,
               CONCAT('legacy-', g.guestid), 'Booked'
        FROM guest AS g
        LEFT JOIN permanent_guest AS p
            ON p.booking_token = CONCAT('legacy-', g.guestid)
        WHERE p.permanent_guest_id IS NULL
        """
    )
    # --- Customer module tables ---
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_users (
            id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
            name          VARCHAR(100) NOT NULL,
            email         VARCHAR(150) NOT NULL UNIQUE,
            phone         VARCHAR(20)  DEFAULT NULL,
            address       TEXT         DEFAULT NULL,
            password_hash VARCHAR(255) NOT NULL,
            status        ENUM('active','inactive') NOT NULL DEFAULT 'active',
            created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_customer_email (email)
        );
        """
    )
    # Safely add customer_user_id to guest (idempotent via information_schema check)
    col_check = db.execute(
        """SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=%s AND TABLE_NAME='guest' AND COLUMN_NAME='customer_user_id'""",
        (MYSQL_DATABASE,)
    ).fetchone()["cnt"]
    if col_check == 0:
        db.execute("ALTER TABLE guest ADD COLUMN customer_user_id INT UNSIGNED NULL DEFAULT NULL")
    # Safely add customer_user_id to permanent_guest
    col_check2 = db.execute(
        """SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=%s AND TABLE_NAME='permanent_guest' AND COLUMN_NAME='customer_user_id'""",
        (MYSQL_DATABASE,)
    ).fetchone()["cnt"]
    if col_check2 == 0:
        db.execute("ALTER TABLE permanent_guest ADD COLUMN customer_user_id INT UNSIGNED NULL DEFAULT NULL")
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        # Customers must use their own /customer/* portal, not the staff workspace
        if session.get("role") == "Customer":
            return redirect(url_for("customer_dashboard"))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "Administrator":
            flash("Administrator access is required for this area.", "error")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)

    return wrapped_view


def customer_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "Customer":
            return redirect(url_for("customer_login"))
        return view(*args, **kwargs)

    return wrapped_view


def parse_dates(check_in_text, check_out_text):
    check_in = datetime.strptime(check_in_text, "%Y-%m-%d").date()
    check_out = datetime.strptime(check_out_text, "%Y-%m-%d").date()
    days = (check_out - check_in).days
    if days <= 0:
        raise ValueError("Check-out must be after check-in.")
    return check_in, check_out, days


def get_occupied_rooms(check_in=None, check_out=None):
    db = get_db()
    if check_in and check_out:
        ci_str = check_in.isoformat() if isinstance(check_in, (date, datetime)) else str(check_in)
        co_str = check_out.isoformat() if isinstance(check_out, (date, datetime)) else str(check_out)
        rows = db.execute(
            "SELECT room_no FROM guest WHERE cidate < %s AND codate > %s",
            (co_str, ci_str),
        ).fetchall()
    else:
        today_str = date.today().isoformat()
        rows = db.execute(
            "SELECT room_no FROM guest WHERE cidate <= %s AND codate > %s",
            (today_str, today_str),
        ).fetchall()
    return {row["room_no"] for row in rows}


def find_available_room(room_type, check_in=None, check_out=None):
    occupied = get_occupied_rooms(check_in, check_out)
    return next((room for room in ROOM_RANGES[room_type] if room not in occupied), None)


def available_rooms_by_type(check_in=None, check_out=None):
    occupied = get_occupied_rooms(check_in, check_out)
    return {room_type: [room for room in rooms if room not in occupied] for room_type, rooms in ROOM_RANGES.items()}


def next_id(table, column):
    allowed = {"guest": "guestid", "staff": "id"}
    if table not in allowed or column != allowed[table]:
        raise ValueError("Invalid table configuration")
    return get_db().execute(f"SELECT COALESCE(MAX({column}), 0) + 1 AS next_id FROM {table}").fetchone()["next_id"]


def new_booking_token():
    return secrets.token_urlsafe(32)


@app.context_processor
def inject_globals():
    return {"today": date.today().isoformat()}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = {
            "admin": ("admin123", "Administrator"),
            "staff": ("staff123", "Staff member"),
        }
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        if username in users and users[username][0] == password:
            session.clear()
            session["user"] = username
            session["role"] = users[username][1]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("welcome"))


@app.get("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("welcome"))


@app.get("/welcome")
def welcome():
    return render_template("welcome.html")


@app.get("/dashboard")
@login_required
def dashboard():
    db = get_db()
    guests = db.execute("SELECT * FROM guest ORDER BY guestid DESC").fetchall()
    occupied = get_occupied_rooms()
    stats = {
        "guests": len(guests),
        "occupied": len(occupied),
        "total_rooms": sum(len(room_range) for room_range in ROOM_RANGES.values()),
        "available": sum(len(room_range) for room_range in ROOM_RANGES.values()) - len(occupied),
        "revenue": sum(float(row["netpay"]) for row in guests),
    }
    return render_template("dashboard.html", guests=guests, stats=stats, active="dashboard")


@app.route("/guests/add", methods=["GET", "POST"])
@login_required
def add_guest():
    if request.method == "POST":
        try:
            booking_token = request.form.get("booking_token", "").strip()
            completed_bookings = session.get("completed_booking_tokens", {})
            if booking_token and booking_token in completed_bookings:
                return redirect(url_for("invoice", guest_id=int(completed_bookings[booking_token])))
            name = request.form["name"].strip()
            room_type = request.form["room_type"]
            source = request.form["source"]
            if not name or room_type not in ROOM_RANGES or source not in {"online", "offline"}:
                raise ValueError("Please complete all fields with valid values.")
            check_in, check_out, days = parse_dates(request.form["check_in"], request.form["check_out"])
            db = get_db()
            requested_room = request.form.get("room_no", "").strip()
            if requested_room:
                try:
                    room_no = int(requested_room)
                except ValueError as error:
                    raise ValueError("Please choose a valid room number.") from error
                if room_no not in ROOM_RANGES[room_type]:
                    raise ValueError(f"Room {room_no} does not belong to the {room_type} room range.")
                occupied = get_occupied_rooms(check_in, check_out)
                if room_no in occupied:
                    raise ValueError(f"Room {room_no} is already booked for dates {check_in} to {check_out}. Please choose another room.")
            else:
                room_no = find_available_room(room_type, check_in, check_out)
            if room_no is None:
                raise ValueError(f"No {room_type} rooms are available for dates {check_in} to {check_out}.")
            room_charge = ROOM_CATALOG[room_type]["rate"] * days
            total = room_charge * 1.18
            guest_id = next_id("guest", "guestid")
            db.execute(
                """INSERT INTO guest
                (guestid, nameofguest, type_of_room, noofdays, cidate, codate, room_no, source_of_booking, netpay)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (guest_id, name, room_type, days, check_in.isoformat(), check_out.isoformat(), room_no, source, total),
            )
            db.execute(
                """INSERT INTO permanent_guest
                (original_guest_id, nameofguest, type_of_room, noofdays, cidate, codate,
                 room_no, source_of_booking, netpay, booking_token, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Booked')""",
                (guest_id, name, room_type, days, check_in.isoformat(), check_out.isoformat(), room_no, source, total, booking_token or None),
            )
            db.commit()
            if booking_token:
                completed_bookings[booking_token] = guest_id
                session["completed_booking_tokens"] = completed_bookings
            flash(f"Booking created for {name}. Room {room_no} is assigned.", "success")
            return redirect(url_for("invoice", guest_id=guest_id))
        except (KeyError, ValueError) as error:
            flash(str(error), "error")
    
    ci_param = request.args.get("check_in")
    co_param = request.args.get("check_out")
    check_in_d, check_out_d = None, None
    if ci_param and co_param:
        try:
            check_in_d, check_out_d, _ = parse_dates(ci_param, co_param)
        except ValueError:
            pass
    booking_token = new_booking_token()
    return render_template("add_guest.html", active="add", room_options=available_rooms_by_type(check_in_d, check_out_d), room_rates=ROOM_RATES, booking_token=booking_token)


@app.get("/invoice/<int:guest_id>")
@login_required
def invoice(guest_id):
    guest = get_db().execute("SELECT * FROM guest WHERE guestid = %s", (guest_id,)).fetchone()
    if guest is None:
        flash("Guest booking was not found.", "error")
        return redirect(url_for("dashboard"))
    room_charge = ROOM_CATALOG[guest["type_of_room"]]["rate"] * guest["noofdays"]
    gst = room_charge * 0.18
    invoice_dir = BASE_DIR / "invoices"
    invoice_dir.mkdir(exist_ok=True)
    invoice_path = invoice_dir / f"invoice_{guest_id}.txt"
    invoice_path.write_text(
        "HOTELOS INVOICE\n"
        f"Guest ID: {guest['guestid']}\nGuest Name: {guest['nameofguest']}\n"
        f"Room: {guest['room_no']} ({guest['type_of_room']})\n"
        f"Stay: {guest['cidate']} to {guest['codate']} ({guest['noofdays']} days)\n"
        f"Room Charges: INR {room_charge:.2f}\nGST (18%): INR {gst:.2f}\n"
        f"Total: INR {guest['netpay']:.2f}\n",
        encoding="utf-8",
    )
    return render_template("invoice.html", guest=guest, room_charge=room_charge, gst=gst, invoice_path=invoice_path, active="invoice")


@app.get("/invoice/<int:guest_id>/download")
@login_required
def download_invoice(guest_id):
    invoice_dir = BASE_DIR / "invoices"
    invoice_path = invoice_dir / f"invoice_{guest_id}.txt"
    if not invoice_path.exists():
        guest = get_db().execute("SELECT * FROM guest WHERE guestid = %s", (guest_id,)).fetchone()
        if guest is None:
            flash("Invoice file not found.", "error")
            return redirect(url_for("dashboard"))
        room_charge = ROOM_CATALOG[guest["type_of_room"]]["rate"] * guest["noofdays"]
        gst = room_charge * 0.18
        invoice_dir.mkdir(exist_ok=True)
        invoice_path.write_text(
            "HOTELOS INVOICE\n"
            f"Guest ID: {guest['guestid']}\nGuest Name: {guest['nameofguest']}\n"
            f"Room: {guest['room_no']} ({guest['type_of_room']})\n"
            f"Stay: {guest['cidate']} to {guest['codate']} ({guest['noofdays']} days)\n"
            f"Room Charges: INR {room_charge:.2f}\nGST (18%): INR {gst:.2f}\n"
            f"Total: INR {guest['netpay']:.2f}\n",
            encoding="utf-8",
        )
    return send_file(invoice_path, as_attachment=True, download_name=f"invoice_{guest_id}.txt")


@app.get("/guests")
@login_required
def guests():
    search = request.args.get("search", "").strip()
    if search:
        like = f"%{search}%"
        records = get_db().execute(
            "SELECT * FROM guest WHERE nameofguest LIKE %s OR CAST(guestid AS CHAR) LIKE %s OR CAST(room_no AS CHAR) LIKE %s ORDER BY guestid DESC",
            (like, like, like),
        ).fetchall()
    else:
        records = get_db().execute("SELECT * FROM guest ORDER BY guestid DESC").fetchall()
    guest_stats = {
        "total": len(records),
        "online": sum(1 for record in records if record["source_of_booking"] == "online"),
        "offline": sum(1 for record in records if record["source_of_booking"] == "offline"),
        "revenue": sum(float(record["netpay"]) for record in records),
    }
    return render_template("guests.html", guests=records, search=search, guest_stats=guest_stats, active="guests")


@app.post("/guests/<int:guest_id>/delete")
@login_required
def delete_guest(guest_id):
    db = get_db()
    db.execute("DELETE FROM guest WHERE guestid = %s", (guest_id,))
    db.commit()
    flash("Guest record deleted and the room is available again.", "success")
    return redirect(url_for("guests"))


@app.route("/staff", methods=["GET", "POST"])
@admin_required
def staff():
    db = get_db()
    departments = {"cleaning": 2000, "food and beverages": 4000, "management": 6000, "manager": 7000, "front office": 3500, "security": 3000, "maintenance": 3500, "concierge": 4500, "kitchen": 5000, "spa and wellness": 5500}
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        dept = request.form.get("dept", "").strip().lower()
        hiredate = request.form.get("hiredate", "").strip()
        if not name or dept not in departments or not hiredate:
            flash("Enter a name, valid department, and hire date.", "error")
        else:
            staff_id = next_id("staff", "id")
            db.execute("INSERT INTO staff (id, name, dept, sal, hiredate) VALUES (%s, %s, %s, %s, %s)", (staff_id, name, dept, departments[dept], hiredate))
            db.commit()
            flash(f"Staff record added for {name}.", "success")
            return redirect(url_for("staff"))
    records = db.execute("SELECT * FROM staff ORDER BY id DESC").fetchall()
    staff_stats = {"total": len(records), "departments": len({record["dept"] for record in records}), "payroll": sum(float(record["sal"]) for record in records)}
    return render_template("staff.html", staff=records, departments=departments, staff_stats=staff_stats, active="staff")


@app.post("/staff/<int:staff_id>/delete")
@admin_required
def delete_staff(staff_id):
    db = get_db()
    db.execute("DELETE FROM staff WHERE id = %s", (staff_id,))
    db.commit()
    flash("Staff record deleted.", "success")
    return redirect(url_for("staff"))


@app.get("/reports")
@admin_required
def reports():
    db = get_db()
    room_counts = {room_type: db.execute("SELECT COUNT(*) AS count FROM guest WHERE type_of_room = %s", (room_type,)).fetchone()["count"] for room_type in ROOM_RANGES}
    source_counts = {source: db.execute("SELECT COUNT(*) AS count FROM guest WHERE source_of_booking = %s", (source,)).fetchone()["count"] for source in ("online", "offline")}
    departments = ("cleaning", "food and beverages", "management", "manager", "front office", "security", "maintenance", "concierge", "kitchen", "spa and wellness")
    dept_counts = {dept: db.execute("SELECT COUNT(*) AS count FROM staff WHERE dept = %s", (dept,)).fetchone()["count"] for dept in departments}
    total_rooms = sum(len(room_range) for room_range in ROOM_RANGES.values())
    total_guests = sum(room_counts.values())
    revenue = db.execute("SELECT COALESCE(SUM(netpay), 0) AS total FROM guest").fetchone()["total"]
    avg_stay = db.execute("SELECT COALESCE(AVG(noofdays), 0) AS average FROM guest").fetchone()["average"]
    report_stats = {"guests": total_guests, "revenue": float(revenue or 0), "occupancy": round(total_guests / total_rooms * 100) if total_rooms else 0, "avg_stay": round(float(avg_stay or 0), 1)}
    return render_template("reports.html", room_counts=room_counts, source_counts=source_counts, dept_counts=dept_counts, report_stats=report_stats, active="reports")


@app.post("/checkout/<int:guest_id>")
@login_required
def checkout(guest_id):
    db = get_db()
    guest = db.execute("SELECT nameofguest, room_no FROM guest WHERE guestid = %s", (guest_id,)).fetchone()
    if guest is None:
        flash("Guest booking was not found.", "error")
    else:
        db.execute(
            """UPDATE permanent_guest
            SET checkout_at = NOW(), status = 'Checked Out'
            WHERE original_guest_id = %s AND checkout_at IS NULL""",
            (guest_id,),
        )
        db.execute("DELETE FROM guest WHERE guestid = %s", (guest_id,))
        db.commit()
        flash(f"Checkout complete. Room {guest['room_no']} is now available.", "success")
    return redirect(url_for("dashboard"))


@app.get("/availability")
@login_required
def availability():
    occupied = get_occupied_rooms()
    rooms = []
    for room_type, room_range in ROOM_RANGES.items():
        available = [room for room in room_range if room not in occupied]
        rooms.append({"type": room_type, "total": len(room_range), "available": available, "occupied": len(room_range) - len(available)})
    room_images = {room_type: catalog["image"] for room_type, catalog in ROOM_CATALOG.items()}
    total_rooms = sum(room["total"] for room in rooms)
    occupied_rooms = sum(room["occupied"] for room in rooms)
    return render_template("availability.html", rooms=rooms, room_images=room_images,
                           total_rooms=total_rooms, occupied_rooms=occupied_rooms,
                           available_rooms=total_rooms - occupied_rooms, room_info=ROOM_CATALOG,
                           active="availability")


@app.get("/rooms/<room_type>")
@login_required
def room_detail(room_type):
    if room_type not in ROOM_RANGES:
        abort(404)
    occupied = get_occupied_rooms()
    catalog = ROOM_CATALOG[room_type]
    room_range = ROOM_RANGES[room_type]
    available = [room for room in room_range if room not in occupied]
    details = ROOM_DETAILS[room_type]
    gallery = ROOM_GALLERIES[room_type]
    return render_template("room_detail.html", room_type=room_type, catalog=catalog, gallery=gallery,
                           total=len(room_range), occupied=len(room_range) - len(available),
                           available=len(available), details=details, active="availability")


@app.get("/health")
def health():
    return {"status": "ok", "service": "hotel-management-web"}


# =============================================================
# CUSTOMER MODULE — routes prefixed /customer/
# =============================================================

@app.route("/customer/register", methods=["GET", "POST"])
def customer_register():
    if session.get("role") == "Customer":
        return redirect(url_for("customer_dashboard"))
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        phone    = request.form.get("phone", "").strip()
        address  = request.form.get("address", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        if not name or not email or not password:
            flash("Name, email, and password are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        else:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM customer_users WHERE email = %s", (email,)
            ).fetchone()
            if existing:
                flash("An account with this email already exists.", "error")
            else:
                pw_hash = generate_password_hash(password)
                db.execute(
                    """INSERT INTO customer_users (name, email, phone, address, password_hash)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (name, email, phone or None, address or None, pw_hash),
                )
                db.commit()
                flash("Account created! Please sign in.", "success")
                return redirect(url_for("customer_login"))
    return render_template("customer_register.html")


@app.route("/customer/login", methods=["GET", "POST"])
def customer_login():
    if session.get("role") == "Customer":
        return redirect(url_for("customer_dashboard"))
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        customer = db.execute(
            "SELECT * FROM customer_users WHERE email = %s AND status = 'active'", (email,)
        ).fetchone()
        if customer and check_password_hash(customer["password_hash"], password):
            session.clear()
            session["user"]        = customer["email"]
            session["role"]        = "Customer"
            session["customer_id"] = customer["id"]
            session["customer_name"] = customer["name"]
            return redirect(url_for("customer_dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("customer_login.html")


@app.get("/customer/logout")
def customer_logout():
    session.clear()
    return redirect(url_for("welcome"))


@app.get("/customer/dashboard")
@customer_required
def customer_dashboard():
    db = get_db()
    cid = session["customer_id"]
    bookings = db.execute(
        """SELECT p.*, g.guestid
           FROM permanent_guest p
           LEFT JOIN guest g ON g.guestid = p.original_guest_id AND g.customer_user_id = %s
           WHERE p.customer_user_id = %s
           ORDER BY p.booking_date DESC LIMIT 5""",
        (cid, cid),
    ).fetchall()
    active_count = db.execute(
        "SELECT COUNT(*) AS cnt FROM guest WHERE customer_user_id = %s", (cid,)
    ).fetchone()["cnt"]
    total_count = db.execute(
        "SELECT COUNT(*) AS cnt FROM permanent_guest WHERE customer_user_id = %s", (cid,)
    ).fetchone()["cnt"]
    return render_template(
        "customer_dashboard.html",
        bookings=bookings,
        active_count=active_count,
        total_count=total_count,
    )


@app.route("/customer/profile", methods=["GET", "POST"])
@customer_required
def customer_profile():
    db = get_db()
    cid = session["customer_id"]
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        phone   = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        if not name:
            flash("Name cannot be empty.", "error")
        else:
            db.execute(
                "UPDATE customer_users SET name=%s, phone=%s, address=%s WHERE id=%s",
                (name, phone or None, address or None, cid),
            )
            db.commit()
            session["customer_name"] = name
            flash("Profile updated successfully.", "success")
            return redirect(url_for("customer_profile"))
    customer = db.execute("SELECT * FROM customer_users WHERE id = %s", (cid,)).fetchone()
    return render_template("customer_profile.html", customer=customer)


@app.get("/customer/rooms")
@customer_required
def customer_rooms():
    occupied = get_occupied_rooms()
    rooms = []
    for room_type, room_range in ROOM_RANGES.items():
        available = [room for room in room_range if room not in occupied]
        rooms.append({
            "type": room_type,
            "total": len(room_range),
            "available": available,
            "occupied": len(room_range) - len(available),
        })
    room_images = {rt: cat["image"] for rt, cat in ROOM_CATALOG.items()}
    total_rooms = sum(r["total"] for r in rooms)
    occupied_count = sum(r["occupied"] for r in rooms)
    return render_template(
        "customer_rooms.html",
        rooms=rooms,
        room_images=room_images,
        room_info=ROOM_CATALOG,
        total_rooms=total_rooms,
        occupied_rooms=occupied_count,
        available_rooms=total_rooms - occupied_count,
    )


@app.route("/customer/book", methods=["GET", "POST"])
@customer_required
def customer_book():
    if request.method == "POST":
        try:
            booking_token = request.form.get("booking_token", "").strip()
            completed_bookings = session.get("completed_booking_tokens", {})
            if booking_token and booking_token in completed_bookings:
                return redirect(url_for("customer_invoice", guest_id=int(completed_bookings[booking_token])))
            cid       = session["customer_id"]
            cname     = session.get("customer_name", "")
            name      = request.form.get("name", "").strip() or cname
            room_type = request.form["room_type"]
            if not name or room_type not in ROOM_RANGES:
                raise ValueError("Please complete all required fields.")
            check_in, check_out, days = parse_dates(request.form["check_in"], request.form["check_out"])
            db = get_db()
            requested_room = request.form.get("room_no", "").strip()
            if requested_room:
                try:
                    room_no = int(requested_room)
                except ValueError as error:
                    raise ValueError("Please choose a valid room number.") from error
                if room_no not in ROOM_RANGES[room_type]:
                    raise ValueError(f"Room {room_no} does not belong to the {room_type} range.")
                occupied = get_occupied_rooms(check_in, check_out)
                if room_no in occupied:
                    raise ValueError(f"Room {room_no} is already booked for those dates.")
            else:
                room_no = find_available_room(room_type, check_in, check_out)
            if room_no is None:
                raise ValueError(f"No {room_type} rooms available for those dates.")
            room_charge = ROOM_CATALOG[room_type]["rate"] * days
            total       = room_charge * 1.18
            guest_id    = next_id("guest", "guestid")
            db.execute(
                """INSERT INTO guest
                   (guestid, nameofguest, type_of_room, noofdays, cidate, codate,
                    room_no, source_of_booking, netpay, customer_user_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'online', %s, %s)""",
                (guest_id, name, room_type, days,
                 check_in.isoformat(), check_out.isoformat(),
                 room_no, total, cid),
            )
            db.execute(
                """INSERT INTO permanent_guest
                   (original_guest_id, nameofguest, type_of_room, noofdays, cidate, codate,
                    room_no, source_of_booking, netpay, booking_token, status, customer_user_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'online', %s, %s, 'Booked', %s)""",
                (guest_id, name, room_type, days,
                 check_in.isoformat(), check_out.isoformat(),
                 room_no, total, booking_token or None, cid),
            )
            db.commit()
            if booking_token:
                completed_bookings[booking_token] = guest_id
                session["completed_booking_tokens"] = completed_bookings
            flash(f"Booking created! Room {room_no} assigned.", "success")
            return redirect(url_for("customer_invoice", guest_id=guest_id))
        except (KeyError, ValueError) as error:
            flash(str(error), "error")
    preselect = request.args.get("room_type", "")
    ci_param  = request.args.get("check_in")
    co_param  = request.args.get("check_out")
    check_in_d, check_out_d = None, None
    if ci_param and co_param:
        try:
            check_in_d, check_out_d, _ = parse_dates(ci_param, co_param)
        except ValueError:
            pass
    booking_token = new_booking_token()
    return render_template(
        "customer_book.html",
        room_options=available_rooms_by_type(check_in_d, check_out_d),
        room_rates=ROOM_RATES,
        booking_token=booking_token,
        preselect=preselect,
        customer_name=session.get("customer_name", ""),
    )


@app.get("/customer/bookings")
@customer_required
def customer_bookings():
    cid = session["customer_id"]
    records = get_db().execute(
        """SELECT * FROM permanent_guest
           WHERE customer_user_id = %s
           ORDER BY booking_date DESC""",
        (cid,),
    ).fetchall()
    return render_template("customer_bookings.html", bookings=records)


@app.get("/customer/bookings/<int:guest_id>")
@customer_required
def customer_booking_detail(guest_id):
    cid = session["customer_id"]
    # ownership check: must match customer_user_id in permanent_guest
    booking = get_db().execute(
        "SELECT * FROM permanent_guest WHERE original_guest_id = %s AND customer_user_id = %s",
        (guest_id, cid),
    ).fetchone()
    if booking is None:
        abort(403)
    return render_template("customer_booking_detail.html", booking=booking)


@app.get("/customer/bookings/<int:guest_id>/invoice")
@customer_required
def customer_invoice(guest_id):
    cid = session["customer_id"]
    # IDOR prevention: verify ownership in guest table first (active booking)
    guest = get_db().execute(
        "SELECT * FROM guest WHERE guestid = %s AND customer_user_id = %s",
        (guest_id, cid),
    ).fetchone()
    if guest is None:
        # fall back to permanent_guest history (already checked out)
        pg = get_db().execute(
            "SELECT * FROM permanent_guest WHERE original_guest_id = %s AND customer_user_id = %s",
            (guest_id, cid),
        ).fetchone()
        if pg is None:
            abort(403)
        # Build a guest-like dict from permanent_guest for rendering
        guest = {
            "guestid": pg["original_guest_id"],
            "nameofguest": pg["nameofguest"],
            "type_of_room": pg["type_of_room"],
            "noofdays": pg["noofdays"],
            "cidate": pg["cidate"],
            "codate": pg["codate"],
            "room_no": pg["room_no"],
            "netpay": pg["netpay"],
        }
    room_charge = ROOM_CATALOG[guest["type_of_room"]]["rate"] * guest["noofdays"]
    gst = room_charge * 0.18
    invoice_dir  = BASE_DIR / "invoices"
    invoice_dir.mkdir(exist_ok=True)
    invoice_path = invoice_dir / f"invoice_{guest_id}.txt"
    invoice_path.write_text(
        "HOTELOS INVOICE\n"
        f"Guest ID: {guest['guestid']}\nGuest Name: {guest['nameofguest']}\n"
        f"Room: {guest['room_no']} ({guest['type_of_room']})\n"
        f"Stay: {guest['cidate']} to {guest['codate']} ({guest['noofdays']} days)\n"
        f"Room Charges: INR {room_charge:.2f}\nGST (18%): INR {gst:.2f}\n"
        f"Total: INR {guest['netpay']:.2f}\n",
        encoding="utf-8",
    )
    return render_template(
        "customer_invoice.html",
        guest=guest,
        room_charge=room_charge,
        gst=gst,
        invoice_path=invoice_path,
    )


@app.get("/customer/bookings/<int:guest_id>/invoice/download")
@customer_required
def customer_invoice_download(guest_id):
    cid = session["customer_id"]
    # IDOR prevention
    owns = get_db().execute(
        "SELECT 1 FROM guest WHERE guestid=%s AND customer_user_id=%s", (guest_id, cid)
    ).fetchone()
    if not owns:
        owns = get_db().execute(
            "SELECT 1 FROM permanent_guest WHERE original_guest_id=%s AND customer_user_id=%s",
            (guest_id, cid),
        ).fetchone()
    if not owns:
        abort(403)
    invoice_dir  = BASE_DIR / "invoices"
    invoice_path = invoice_dir / f"invoice_{guest_id}.txt"
    if not invoice_path.exists():
        return redirect(url_for("customer_invoice", guest_id=guest_id))
    return send_file(invoice_path, as_attachment=True, download_name=f"invoice_{guest_id}.txt")


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=int(os.environ.get("PORT", "5001")))
