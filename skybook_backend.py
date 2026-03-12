"""
SkyBook Backend — Flask API
Full-featured airline booking system backend
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json, os, uuid, random, string, hashlib, re
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "skybook-super-secret-jwt-key-2025"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

CORS(app, resources={r"/api/*": {"origins": "*"}})
jwt = JWTManager(app)

# ── IN-MEMORY DATABASES (replace with real DB in production) ─────────────────
DB_USERS = {}        # email -> user dict
DB_BOOKINGS = {}     # booking_id -> booking dict
DB_RESET_TOKENS = {} # token -> email
DB_REVIEWS = []      # list of reviews
DB_NOTIFICATIONS = {} # user_id -> list

# ── MOCK DATA ─────────────────────────────────────────────────────────────────
AIRPORTS = {
    "ISB": {"name": "Islamabad International Airport", "city": "Islamabad", "country": "Pakistan", "country_code": "PK", "timezone": "PKT"},
    "KHI": {"name": "Jinnah International Airport", "city": "Karachi", "country": "Pakistan", "country_code": "PK", "timezone": "PKT"},
    "LHE": {"name": "Allama Iqbal International Airport", "city": "Lahore", "country": "Pakistan", "country_code": "PK", "timezone": "PKT"},
    "PEW": {"name": "Bacha Khan International Airport", "city": "Peshawar", "country": "Pakistan", "country_code": "PK", "timezone": "PKT"},
    "DXB": {"name": "Dubai International Airport", "city": "Dubai", "country": "UAE", "country_code": "AE", "timezone": "GST"},
    "AUH": {"name": "Abu Dhabi International Airport", "city": "Abu Dhabi", "country": "UAE", "country_code": "AE", "timezone": "GST"},
    "DOH": {"name": "Hamad International Airport", "city": "Doha", "country": "Qatar", "country_code": "QA", "timezone": "AST"},
    "RUH": {"name": "King Khalid International Airport", "city": "Riyadh", "country": "Saudi Arabia", "country_code": "SA", "timezone": "AST"},
    "JED": {"name": "King Abdulaziz International Airport", "city": "Jeddah", "country": "Saudi Arabia", "country_code": "SA", "timezone": "AST"},
    "IST": {"name": "Istanbul Airport", "city": "Istanbul", "country": "Turkey", "country_code": "TR", "timezone": "TRT"},
    "LHR": {"name": "Heathrow Airport", "city": "London", "country": "UK", "country_code": "GB", "timezone": "GMT"},
    "CDG": {"name": "Charles de Gaulle Airport", "city": "Paris", "country": "France", "country_code": "FR", "timezone": "CET"},
    "FRA": {"name": "Frankfurt Airport", "city": "Frankfurt", "country": "Germany", "country_code": "DE", "timezone": "CET"},
    "JFK": {"name": "John F. Kennedy International Airport", "city": "New York", "country": "USA", "country_code": "US", "timezone": "EST"},
    "ORD": {"name": "O'Hare International Airport", "city": "Chicago", "country": "USA", "country_code": "US", "timezone": "CST"},
    "BOM": {"name": "Chhatrapati Shivaji Maharaj International Airport", "city": "Mumbai", "country": "India", "country_code": "IN", "timezone": "IST"},
    "DEL": {"name": "Indira Gandhi International Airport", "city": "Delhi", "country": "India", "country_code": "IN", "timezone": "IST"},
    "KUL": {"name": "Kuala Lumpur International Airport", "city": "Kuala Lumpur", "country": "Malaysia", "country_code": "MY", "timezone": "MYT"},
    "SIN": {"name": "Singapore Changi Airport", "city": "Singapore", "country": "Singapore", "country_code": "SG", "timezone": "SGT"},
    "BKK": {"name": "Suvarnabhumi Airport", "city": "Bangkok", "country": "Thailand", "country_code": "TH", "timezone": "ICT"},
    "NRT": {"name": "Narita International Airport", "city": "Tokyo", "country": "Japan", "country_code": "JP", "timezone": "JST"},
    "SYD": {"name": "Sydney Kingsford Smith Airport", "city": "Sydney", "country": "Australia", "country_code": "AU", "timezone": "AEDT"},
    "CAI": {"name": "Cairo International Airport", "city": "Cairo", "country": "Egypt", "country_code": "EG", "timezone": "EET"},
    "NBO": {"name": "Jomo Kenyatta International Airport", "city": "Nairobi", "country": "Kenya", "country_code": "KE", "timezone": "EAT"},
}

AIRLINES = {
    "PK": {"name": "Pakistan International Airlines", "code": "PK", "emoji": "🟢", "rating": 3.8, "alliance": "None"},
    "EK": {"name": "Emirates", "code": "EK", "emoji": "🔴", "rating": 4.7, "alliance": "None"},
    "QR": {"name": "Qatar Airways", "code": "QR", "emoji": "🟤", "rating": 4.6, "alliance": "Oneworld"},
    "TK": {"name": "Turkish Airlines", "code": "TK", "emoji": "🔵", "rating": 4.4, "alliance": "Star Alliance"},
    "EY": {"name": "Etihad Airways", "code": "EY", "emoji": "⚪", "rating": 4.5, "alliance": "None"},
    "FZ": {"name": "Flydubai", "code": "FZ", "emoji": "🟠", "rating": 4.1, "alliance": "None"},
    "SV": {"name": "Saudia", "code": "SV", "emoji": "🟢", "rating": 4.0, "alliance": "SkyTeam"},
    "BA": {"name": "British Airways", "code": "BA", "emoji": "🔵", "rating": 4.3, "alliance": "Oneworld"},
    "LH": {"name": "Lufthansa", "code": "LH", "emoji": "🟡", "rating": 4.4, "alliance": "Star Alliance"},
    "SQ": {"name": "Singapore Airlines", "code": "SQ", "emoji": "🟡", "rating": 4.8, "alliance": "Star Alliance"},
}

ROUTE_CONFIGS = [
    {"origin": "ISB", "dest": "DXB", "base_price": 189, "duration_min": 195, "airline": "EK", "stops": 0},
    {"origin": "ISB", "dest": "DXB", "base_price": 165, "duration_min": 210, "airline": "PK", "stops": 0},
    {"origin": "ISB", "dest": "DXB", "base_price": 178, "duration_min": 200, "airline": "FZ", "stops": 0},
    {"origin": "KHI", "dest": "LHR", "base_price": 520, "duration_min": 570, "airline": "PK", "stops": 1},
    {"origin": "KHI", "dest": "LHR", "base_price": 680, "duration_min": 540, "airline": "EK", "stops": 1},
    {"origin": "KHI", "dest": "LHR", "base_price": 890, "duration_min": 520, "airline": "QR", "stops": 0},
    {"origin": "LHE", "dest": "DOH", "base_price": 210, "duration_min": 240, "airline": "QR", "stops": 0},
    {"origin": "LHE", "dest": "DOH", "base_price": 195, "duration_min": 255, "airline": "PK", "stops": 0},
    {"origin": "ISB", "dest": "IST", "base_price": 340, "duration_min": 405, "airline": "TK", "stops": 0},
    {"origin": "ISB", "dest": "IST", "base_price": 310, "duration_min": 430, "airline": "PK", "stops": 1},
    {"origin": "KHI", "dest": "DXB", "base_price": 145, "duration_min": 165, "airline": "EK", "stops": 0},
    {"origin": "KHI", "dest": "DXB", "base_price": 130, "duration_min": 175, "airline": "FZ", "stops": 0},
    {"origin": "ISB", "dest": "JFK", "base_price": 890, "duration_min": 1110, "airline": "EK", "stops": 1},
    {"origin": "ISB", "dest": "JFK", "base_price": 980, "duration_min": 1080, "airline": "QR", "stops": 1},
    {"origin": "ISB", "dest": "LHR", "base_price": 490, "duration_min": 510, "airline": "PK", "stops": 0},
    {"origin": "ISB", "dest": "LHR", "base_price": 620, "duration_min": 490, "airline": "EK", "stops": 0},
    {"origin": "LHE", "dest": "DXB", "base_price": 175, "duration_min": 185, "airline": "FZ", "stops": 0},
    {"origin": "KHI", "dest": "DOH", "base_price": 220, "duration_min": 225, "airline": "QR", "stops": 0},
    {"origin": "ISB", "dest": "RUH", "base_price": 280, "duration_min": 285, "airline": "SV", "stops": 0},
    {"origin": "LHE", "dest": "IST", "base_price": 370, "duration_min": 420, "airline": "TK", "stops": 0},
    {"origin": "ISB", "dest": "KUL", "base_price": 450, "duration_min": 510, "airline": "SQ", "stops": 1},
    {"origin": "KHI", "dest": "BOM", "base_price": 120, "duration_min": 105, "airline": "EK", "stops": 0},
    {"origin": "ISB", "dest": "CDG", "base_price": 710, "duration_min": 600, "airline": "LH", "stops": 1},
    {"origin": "ISB", "dest": "NRT", "base_price": 1100, "duration_min": 720, "airline": "SQ", "stops": 1},
]

DEPARTURE_TIMES = ["01:30", "05:45", "07:15", "08:30", "09:00", "10:20", "11:45", "12:30", "13:15", "14:00", "15:30", "16:45", "17:20", "18:00", "19:30", "20:15", "21:45", "23:00"]

CLASSES = {
    "ECONOMY": {"multiplier": 1.0, "label": "Economy"},
    "BUSINESS": {"multiplier": 2.8, "label": "Business"},
    "FIRST": {"multiplier": 5.5, "label": "First Class"},
}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_pnr():
    return "SK" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_flight_number(airline_code: str) -> str:
    return f"{airline_code}{random.randint(100, 999)}"

def generate_flights(origin: str, dest: str, date: str, cabin: str = "ECONOMY", passengers: int = 1):
    flights = []
    matching = [r for r in ROUTE_CONFIGS if r["origin"] == origin and r["dest"] == dest]
    
    if not matching:
        # Generate generic flights if route not predefined
        for airline_code in random.sample(list(AIRLINES.keys()), min(3, len(AIRLINES))):
            matching.append({
                "origin": origin, "dest": dest,
                "base_price": random.randint(150, 900),
                "duration_min": random.randint(120, 720),
                "airline": airline_code,
                "stops": random.choice([0, 0, 1])
            })
    
    class_multiplier = CLASSES.get(cabin, CLASSES["ECONOMY"])["multiplier"]
    class_label = CLASSES.get(cabin, CLASSES["ECONOMY"])["label"]
    
    for route in matching:
        num_times = random.randint(1, 3)
        times = random.sample(DEPARTURE_TIMES, min(num_times, len(DEPARTURE_TIMES)))
        
        for dep_time in times:
            try:
                dep_dt = datetime.strptime(f"{date} {dep_time}", "%Y-%m-%d %H:%M")
            except:
                dep_dt = datetime.now() + timedelta(days=1)
            
            duration = route["duration_min"] + random.randint(-15, 30)
            arr_dt = dep_dt + timedelta(minutes=duration)
            
            base = route["base_price"] * class_multiplier * passengers
            tax_rate = random.uniform(0.08, 0.15)
            taxes = round(base * tax_rate, 2)
            total = round(base + taxes, 2)
            
            airline = AIRLINES.get(route["airline"], AIRLINES["PK"])
            flight_num = generate_flight_number(route["airline"])
            
            seats_available = random.randint(1, 50) if route["stops"] == 0 else random.randint(5, 80)
            
            flights.append({
                "id": str(uuid.uuid4()),
                "flight_number": flight_num,
                "airline_code": route["airline"],
                "airline_name": airline["name"],
                "airline_rating": airline["rating"],
                "airline_alliance": airline["alliance"],
                "origin": origin,
                "origin_city": AIRPORTS.get(origin, {}).get("city", origin),
                "origin_name": AIRPORTS.get(origin, {}).get("name", origin),
                "destination": dest,
                "destination_city": AIRPORTS.get(dest, {}).get("city", dest),
                "destination_name": AIRPORTS.get(dest, {}).get("name", dest),
                "departure_time": dep_dt.isoformat(),
                "arrival_time": arr_dt.isoformat(),
                "duration_minutes": duration,
                "duration_formatted": f"{duration // 60}h {duration % 60}m",
                "stops": route["stops"],
                "cabin_class": class_label,
                "cabin_code": cabin,
                "base_price": round(base, 2),
                "taxes": taxes,
                "total_price": total,
                "currency": "USD",
                "seats_available": seats_available,
                "baggage_allowance": "23kg" if cabin == "ECONOMY" else "32kg",
                "meal_included": cabin != "ECONOMY",
                "refundable": random.choice([True, False]),
                "wifi": cabin != "ECONOMY" or random.random() > 0.5,
                "entertainment": True,
                "on_time_performance": f"{random.randint(75, 98)}%",
            })
    
    # Sort by price
    flights.sort(key=lambda x: x["total_price"])
    return flights

# ── AUTH ROUTES ───────────────────────────────────────────────────────────────

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()
    
    if not email or not password or not full_name:
        return jsonify({"error": "Email, password and full name are required"}), 400
    
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({"error": "Invalid email address"}), 400
    
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    
    if email in DB_USERS:
        return jsonify({"error": "An account with this email already exists"}), 409
    
    user_id = str(uuid.uuid4())
    DB_USERS[email] = {
        "id": user_id,
        "email": email,
        "password_hash": hash_password(password),
        "full_name": full_name,
        "phone": phone,
        "created_at": datetime.now().isoformat(),
        "loyalty_miles": 500,  # Welcome bonus
        "tier": "Silver",
        "nationality": data.get("nationality", ""),
        "passport": data.get("passport", ""),
        "date_of_birth": data.get("date_of_birth", ""),
        "profile_complete": bool(phone),
        "email_verified": True,  # Simulated
        "total_flights": 0,
        "total_spent": 0,
        "preferred_class": "ECONOMY",
        "notifications_enabled": True,
    }
    DB_NOTIFICATIONS[user_id] = [{
        "id": str(uuid.uuid4()),
        "title": "Welcome to SkyBook! 🎉",
        "message": f"Welcome {full_name}! You've earned 500 bonus miles as a welcome gift. Start exploring amazing destinations!",
        "type": "success",
        "read": False,
        "created_at": datetime.now().isoformat()
    }]
    
    token = create_access_token(identity=user_id)
    user_data = {k: v for k, v in DB_USERS[email].items() if k != "password_hash"}
    
    return jsonify({
        "message": "Account created successfully! Welcome to SkyBook.",
        "token": token,
        "user": user_data
    }), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    user = DB_USERS.get(email)
    if not user or user["password_hash"] != hash_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    token = create_access_token(identity=user["id"])
    user_data = {k: v for k, v in user.items() if k != "password_hash"}
    
    return jsonify({
        "message": f"Welcome back, {user['full_name']}!",
        "token": token,
        "user": user_data
    })

@app.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email", "").lower().strip()
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    if email not in DB_USERS:
        # Security: don't reveal if email exists
        return jsonify({"message": "If this email is registered, you'll receive a reset link shortly."}), 200
    
    reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    DB_RESET_TOKENS[reset_token] = {
        "email": email,
        "expires": (datetime.now() + timedelta(hours=1)).isoformat(),
        "used": False
    }
    
    # In production, send real email. Here we simulate:
    reset_link = f"https://skybook.app/reset?token={reset_token}"
    print(f"\n📧 PASSWORD RESET EMAIL (simulated):")
    print(f"   To: {email}")
    print(f"   Subject: Reset your SkyBook password")
    print(f"   Reset Link: {reset_link}\n")
    
    return jsonify({
        "message": "Password reset email sent! Check your inbox.",
        "debug_token": reset_token  # Remove in production
    })

@app.route("/api/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    token = data.get("token", "")
    new_password = data.get("password", "")
    
    token_data = DB_RESET_TOKENS.get(token)
    if not token_data:
        return jsonify({"error": "Invalid or expired reset token"}), 400
    
    if token_data["used"]:
        return jsonify({"error": "Reset token already used"}), 400
    
    if datetime.fromisoformat(token_data["expires"]) < datetime.now():
        return jsonify({"error": "Reset token has expired"}), 400
    
    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    
    email = token_data["email"]
    DB_USERS[email]["password_hash"] = hash_password(new_password)
    DB_RESET_TOKENS[token]["used"] = True
    
    return jsonify({"message": "Password reset successfully! You can now log in."})

@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = next((u for u in DB_USERS.values() if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    user_data = {k: v for k, v in user.items() if k != "password_hash"}
    return jsonify(user_data)

@app.route("/api/auth/update-profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = next((u for u in DB_USERS.values() if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    allowed = ["full_name", "phone", "nationality", "passport", "date_of_birth", "preferred_class", "notifications_enabled"]
    for key in allowed:
        if key in data:
            user[key] = data[key]
    
    user_data = {k: v for k, v in user.items() if k != "password_hash"}
    return jsonify({"message": "Profile updated successfully!", "user": user_data})

# ── FLIGHT ROUTES ─────────────────────────────────────────────────────────────

@app.route("/api/flights/search", methods=["GET"])
def search_flights():
    origin = request.args.get("origin", "").upper()
    dest = request.args.get("destination", "").upper()
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    cabin = request.args.get("cabin", "ECONOMY").upper()
    passengers = int(request.args.get("passengers", 1))
    
    if not origin or not dest:
        return jsonify({"error": "Origin and destination are required"}), 400
    
    if origin == dest:
        return jsonify({"error": "Origin and destination cannot be the same"}), 400
    
    flights = generate_flights(origin, dest, date, cabin, passengers)
    
    return jsonify({
        "flights": flights,
        "count": len(flights),
        "origin": {**{"code": origin}, **AIRPORTS.get(origin, {"name": origin, "city": origin})},
        "destination": {**{"code": dest}, **AIRPORTS.get(dest, {"name": dest, "city": dest})},
        "date": date,
        "cabin": cabin,
        "passengers": passengers,
        "currency": "USD"
    })

@app.route("/api/flights/popular-routes", methods=["GET"])
def popular_routes():
    routes = [
        {"origin": "ISB", "dest": "DXB", "price_from": 165, "deals": 12, "tag": "🔥 Hot Deal"},
        {"origin": "KHI", "dest": "LHR", "price_from": 520, "deals": 7, "tag": "Popular"},
        {"origin": "LHE", "dest": "DOH", "price_from": 195, "deals": 9, "tag": "✨ Best Value"},
        {"origin": "ISB", "dest": "IST", "price_from": 310, "deals": 5, "tag": "Popular"},
        {"origin": "KHI", "dest": "DXB", "price_from": 130, "deals": 15, "tag": "🔥 Cheapest"},
        {"origin": "ISB", "dest": "JFK", "price_from": 890, "deals": 3, "tag": "Premium"},
        {"origin": "LHE", "dest": "DXB", "price_from": 175, "deals": 8, "tag": "Good Value"},
        {"origin": "ISB", "dest": "LHR", "price_from": 490, "deals": 6, "tag": "Popular"},
    ]
    for r in routes:
        r["origin_info"] = AIRPORTS.get(r["origin"], {})
        r["dest_info"] = AIRPORTS.get(r["dest"], {})
    return jsonify(routes)

@app.route("/api/flights/airports", methods=["GET"])
def get_airports():
    query = request.args.get("q", "").lower()
    results = []
    for code, info in AIRPORTS.items():
        if (query in code.lower() or query in info["city"].lower() or 
            query in info["name"].lower() or query in info["country"].lower()):
            results.append({"code": code, **info})
    return jsonify(results[:10])

# ── BOOKING ROUTES ────────────────────────────────────────────────────────────

@app.route("/api/bookings", methods=["POST"])
@jwt_required()
def create_booking():
    user_id = get_jwt_identity()
    user = next((u for u in DB_USERS.values() if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    booking_id = str(uuid.uuid4())
    pnr = generate_pnr()
    
    flight = data.get("flight", {})
    passengers = data.get("passengers", [])
    extras = data.get("extras", {})
    payment_method = data.get("payment_method", "card")
    seat = data.get("seat", "")
    
    # Calculate totals
    base_total = float(flight.get("total_price", 0))
    extras_cost = 0
    extras_prices = {"baggage": 45, "meal": 18, "insurance": 25, "lounge": 35, "fast_track": 15, "priority": 20}
    selected_extras = []
    for k, v in extras.items():
        if v and k in extras_prices:
            extras_cost += extras_prices[k]
            selected_extras.append(k)
    
    grand_total = base_total + extras_cost
    miles_earned = int(grand_total * 1.5)
    
    booking = {
        "id": booking_id,
        "pnr": pnr,
        "user_id": user_id,
        "status": "confirmed",
        "flight": flight,
        "passengers": passengers,
        "seat": seat,
        "extras": selected_extras,
        "extras_cost": extras_cost,
        "base_price": base_total,
        "grand_total": grand_total,
        "payment_method": payment_method,
        "currency": "USD",
        "miles_earned": miles_earned,
        "booked_at": datetime.now().isoformat(),
        "ticket_number": f"TKT{int(datetime.now().timestamp())}",
    }
    
    DB_BOOKINGS[booking_id] = booking
    
    # Update user stats
    user["loyalty_miles"] = user.get("loyalty_miles", 0) + miles_earned
    user["total_flights"] = user.get("total_flights", 0) + 1
    user["total_spent"] = user.get("total_spent", 0) + grand_total
    
    # Tier upgrade logic
    total_miles = user["loyalty_miles"]
    if total_miles >= 50000:
        user["tier"] = "Platinum"
    elif total_miles >= 25000:
        user["tier"] = "Gold"
    elif total_miles >= 10000:
        user["tier"] = "Silver"
    
    # Add notification
    notifs = DB_NOTIFICATIONS.get(user_id, [])
    notifs.insert(0, {
        "id": str(uuid.uuid4()),
        "title": "Booking Confirmed! ✈️",
        "message": f"Your flight {flight.get('flight_number', '')} from {flight.get('origin', '')} to {flight.get('destination', '')} is confirmed. PNR: {pnr}",
        "type": "success",
        "read": False,
        "created_at": datetime.now().isoformat()
    })
    DB_NOTIFICATIONS[user_id] = notifs
    
    return jsonify({
        "message": "Booking confirmed!",
        "booking": booking,
        "miles_earned": miles_earned,
        "new_total_miles": user["loyalty_miles"]
    }), 201

@app.route("/api/bookings", methods=["GET"])
@jwt_required()
def get_bookings():
    user_id = get_jwt_identity()
    user_bookings = [b for b in DB_BOOKINGS.values() if b["user_id"] == user_id]
    user_bookings.sort(key=lambda x: x["booked_at"], reverse=True)
    return jsonify(user_bookings)

@app.route("/api/bookings/<booking_id>", methods=["GET"])
@jwt_required()
def get_booking(booking_id):
    user_id = get_jwt_identity()
    booking = DB_BOOKINGS.get(booking_id)
    if not booking or booking["user_id"] != user_id:
        return jsonify({"error": "Booking not found"}), 404
    return jsonify(booking)

@app.route("/api/bookings/<booking_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_booking(booking_id):
    user_id = get_jwt_identity()
    booking = DB_BOOKINGS.get(booking_id)
    if not booking or booking["user_id"] != user_id:
        return jsonify({"error": "Booking not found"}), 404
    if booking["status"] == "cancelled":
        return jsonify({"error": "Booking already cancelled"}), 400
    
    booking["status"] = "cancelled"
    booking["cancelled_at"] = datetime.now().isoformat()
    refund = round(booking["grand_total"] * 0.85, 2)  # 85% refund
    
    return jsonify({"message": "Booking cancelled. Refund of $" + str(refund) + " will be processed in 5-7 business days.", "refund": refund})

# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────

@app.route("/api/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    notifs = DB_NOTIFICATIONS.get(user_id, [])
    return jsonify(notifs)

@app.route("/api/notifications/mark-read", methods=["POST"])
@jwt_required()
def mark_notifications_read():
    user_id = get_jwt_identity()
    notifs = DB_NOTIFICATIONS.get(user_id, [])
    for n in notifs:
        n["read"] = True
    DB_NOTIFICATIONS[user_id] = notifs
    return jsonify({"message": "All notifications marked as read"})

# ── REVIEWS ───────────────────────────────────────────────────────────────────

@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    airline = request.args.get("airline", "")
    filtered = [r for r in DB_REVIEWS if not airline or r.get("airline") == airline]
    return jsonify(filtered[-20:])

@app.route("/api/reviews", methods=["POST"])
@jwt_required()
def add_review():
    user_id = get_jwt_identity()
    user = next((u for u in DB_USERS.values() if u["id"] == user_id), None)
    data = request.get_json()
    
    review = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_name": user["full_name"] if user else "Anonymous",
        "airline": data.get("airline", ""),
        "rating": min(5, max(1, int(data.get("rating", 3)))),
        "title": data.get("title", ""),
        "comment": data.get("comment", ""),
        "route": data.get("route", ""),
        "cabin_class": data.get("cabin_class", "Economy"),
        "created_at": datetime.now().isoformat(),
        "helpful_count": 0,
    }
    DB_REVIEWS.append(review)
    return jsonify(review), 201

# ── DEALS & OFFERS ────────────────────────────────────────────────────────────

@app.route("/api/deals", methods=["GET"])
def get_deals():
    deals = [
        {"id": 1, "title": "Summer Sale", "discount": "30%", "origin": "ISB", "dest": "DXB", "price": 129, "expires": "2025-08-31", "code": "SUMMER30"},
        {"id": 2, "title": "Eid Special", "discount": "25%", "origin": "KHI", "dest": "LHR", "price": 389, "expires": "2025-06-30", "code": "EID25"},
        {"id": 3, "title": "Business Class Promo", "discount": "20%", "origin": "ISB", "dest": "IST", "price": 850, "expires": "2025-07-15", "code": "BIZ20"},
        {"id": 4, "title": "Weekend Getaway", "discount": "15%", "origin": "LHE", "dest": "DOH", "price": 175, "expires": "2025-06-15", "code": "WKND15"},
        {"id": 5, "title": "Student Discount", "discount": "20%", "origin": "ISB", "dest": "LHR", "price": 399, "expires": "2025-12-31", "code": "STUDENT20"},
        {"id": 6, "title": "Couple Deal", "discount": "10%", "origin": "ISB", "dest": "BKK", "price": 520, "expires": "2025-09-30", "code": "COUPLE10"},
    ]
    return jsonify(deals)

# ── LOYALTY / MILES ───────────────────────────────────────────────────────────

@app.route("/api/loyalty", methods=["GET"])
@jwt_required()
def get_loyalty():
    user_id = get_jwt_identity()
    user = next((u for u in DB_USERS.values() if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    tiers = {"Silver": 10000, "Gold": 25000, "Platinum": 50000}
    current_tier = user.get("tier", "Silver")
    next_tier_map = {"Silver": "Gold", "Gold": "Platinum", "Platinum": "Platinum"}
    next_tier = next_tier_map[current_tier]
    next_tier_miles = tiers.get(next_tier, tiers["Platinum"])
    
    return jsonify({
        "miles": user.get("loyalty_miles", 0),
        "tier": current_tier,
        "next_tier": next_tier,
        "miles_to_next": max(0, next_tier_miles - user.get("loyalty_miles", 0)),
        "total_flights": user.get("total_flights", 0),
        "total_spent": user.get("total_spent", 0),
        "rewards": [
            {"name": "Free Economy Upgrade", "cost": 5000, "available": user.get("loyalty_miles", 0) >= 5000},
            {"name": "Free Checked Bag", "cost": 2000, "available": user.get("loyalty_miles", 0) >= 2000},
            {"name": "Lounge Access", "cost": 8000, "available": user.get("loyalty_miles", 0) >= 8000},
            {"name": "Business Class Upgrade", "cost": 20000, "available": user.get("loyalty_miles", 0) >= 20000},
            {"name": "Free Flight (Short Haul)", "cost": 30000, "available": user.get("loyalty_miles", 0) >= 30000},
        ]
    })

# ── PAYMENT ───────────────────────────────────────────────────────────────────

@app.route("/api/payments/validate-coupon", methods=["POST"])
def validate_coupon():
    data = request.get_json()
    code = data.get("code", "").upper()
    amount = float(data.get("amount", 0))
    
    coupons = {
        "SUMMER30": {"discount": 0.30, "description": "Summer Sale 30% off"},
        "EID25": {"discount": 0.25, "description": "Eid Special 25% off"},
        "BIZ20": {"discount": 0.20, "description": "Business Class 20% off"},
        "WKND15": {"discount": 0.15, "description": "Weekend 15% off"},
        "STUDENT20": {"discount": 0.20, "description": "Student Discount 20% off"},
        "COUPLE10": {"discount": 0.10, "description": "Couple Deal 10% off"},
        "WELCOME10": {"discount": 0.10, "description": "Welcome bonus 10% off"},
    }
    
    coupon = coupons.get(code)
    if not coupon:
        return jsonify({"valid": False, "error": "Invalid promo code"}), 400
    
    discount_amount = round(amount * coupon["discount"], 2)
    return jsonify({
        "valid": True,
        "code": code,
        "discount_percent": int(coupon["discount"] * 100),
        "discount_amount": discount_amount,
        "new_total": round(amount - discount_amount, 2),
        "description": coupon["description"]
    })

# ── STATS / MISC ──────────────────────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
def get_stats():
    return jsonify({
        "total_airlines": len(AIRLINES),
        "total_destinations": len(AIRPORTS),
        "total_bookings_made": len(DB_BOOKINGS) + 18432,
        "happy_travelers": len(DB_USERS) + 89234,
        "avg_price_drop": "$43",
        "routes_served": 150,
    })

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "1.0.0", "timestamp": datetime.now().isoformat()})

# ── SEED DEMO USER ────────────────────────────────────────────────────────────
def seed_demo():
    demo_email = "demo@skybook.app"
    if demo_email not in DB_USERS:
        user_id = str(uuid.uuid4())
        DB_USERS[demo_email] = {
            "id": user_id, "email": demo_email,
            "password_hash": hash_password("Demo1234!"),
            "full_name": "Ahmed Khan", "phone": "+92 300 1234567",
            "created_at": datetime.now().isoformat(),
            "loyalty_miles": 12450, "tier": "Gold",
            "nationality": "Pakistani", "passport": "AB1234567",
            "date_of_birth": "1990-05-15", "profile_complete": True,
            "email_verified": True, "total_flights": 8, "total_spent": 3240,
            "preferred_class": "ECONOMY", "notifications_enabled": True,
        }
        DB_NOTIFICATIONS[user_id] = [
            {"id": str(uuid.uuid4()), "title": "Welcome Back! ✈️", "message": "Ready for your next adventure? Check out our latest deals!", "type": "info", "read": False, "created_at": datetime.now().isoformat()},
            {"id": str(uuid.uuid4()), "title": "Miles Expiring Soon", "message": "You have 2,450 miles expiring on Dec 31. Use them before they're gone!", "type": "warning", "read": False, "created_at": datetime.now().isoformat()},
        ]
        print(f"✅ Demo user seeded: {demo_email} / Demo1234!")

if __name__ == "__main__":
    seed_demo()
    print("\n🚀 SkyBook Backend running on http://localhost:5000")
    print("📋 Demo login: demo@skybook.app / Demo1234!")
    app.run(debug=True, port=5000, host="0.0.0.0")
