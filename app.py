from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import os

app = Flask(__name__)
app.secret_key = "secret123"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///businesses.db")
db = SQLAlchemy(app)

from flask_dance.contrib.google import make_google_blueprint, google

google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    redirect_to="google_login",
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"]
)
app.register_blueprint(google_bp, url_prefix="/login")


# ── Models ────────────────────────────────────────────────────────────
class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    reviews  = db.relationship("Review", backref="author", lazy=True)

class Business(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    address  = db.Column(db.String(200), nullable=False)
    phone    = db.Column(db.String(20))
    reviews  = db.relationship("Review", backref="business", lazy=True)

    @property
    def avg_rating(self):
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

class Review(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    rating      = db.Column(db.Integer, nullable=False)
    comment     = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user_id     = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    business_id = db.Column(db.Integer, db.ForeignKey("business.id"), nullable=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── Icons ─────────────────────────────────────────────────────────────
ICONS = {
    "Ռեստորան": "🍽️",
    "Սրճարան": "☕",
    "Խանութ": "🛍️",
    "Վարսավիրանոց": "✂️",
    "Բժշկություն": "🏥",
    "Կրթություն": "📚",
    "Այլ": "🏢"
}

# ── Base template ─────────────────────────────────────────────────────
def base(title, content):
    user_nav = ""
    if "user_id" in session:
        user_nav = f"""
        <span class="text-white-50 me-3">👤 {session.get('username')}</span>
        <a href='/logout' class='btn btn-outline-light btn-sm'>Ելք</a>
        """
    else:
        user_nav = """
        <a href='/login' class='btn btn-outline-light btn-sm me-2'>Մուտք</a>
        <a href='/register' class='btn btn-light btn-sm'>Գրանցում</a>
        """

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="hy">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title} — Հայ Բիզնես</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ font-family: 'Inter', sans-serif; }}
            body {{ background: #f4f6fb; color: #1a1a2e; }}
            .navbar {{
                background: linear-gradient(135deg, #4361ee, #3a0ca3) !important;
                box-shadow: 0 2px 20px rgba(67,97,238,0.3);
                padding: 14px 24px;
            }}
            .navbar-brand {{ font-size: 1.3rem; font-weight: 700; }}
            .hero {{
                background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
                color: white;
                border-radius: 20px;
                padding: 52px 40px;
                margin-bottom: 32px;
                position: relative;
                overflow: hidden;
            }}
            .hero::before {{
                content: '';
                position: absolute;
                top: -50px; right: -50px;
                width: 300px; height: 300px;
                background: rgba(255,255,255,0.05);
                border-radius: 50%;
            }}
            .hero h1 {{ font-size: 2.2rem; font-weight: 700; margin-bottom: 8px; }}
            .hero p  {{ opacity: 0.85; font-size: 1.05rem; }}
            .search-bar {{
                background: white;
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.08);
                margin-bottom: 32px;
            }}
            .form-control, .form-select {{
                border: 1.5px solid #e8ecf4;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 0.9rem;
            }}
            .form-control:focus, .form-select:focus {{
                border-color: #4361ee;
                box-shadow: 0 0 0 3px rgba(67,97,238,0.12);
            }}
            .biz-card {{
                background: white;
                border: none;
                border-radius: 16px;
                box-shadow: 0 2px 16px rgba(0,0,0,0.06);
                transition: transform 0.2s, box-shadow 0.2s;
                height: 100%;
            }}
            .biz-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 8px 32px rgba(67,97,238,0.15);
            }}
            .biz-card-body {{ padding: 20px; }}
            .biz-icon {{
                width: 48px; height: 48px;
                background: #eff2ff;
                border-radius: 12px;
                display: flex; align-items: center; justify-content: center;
                font-size: 1.4rem;
                margin-bottom: 14px;
            }}
            .biz-name {{ font-size: 1.05rem; font-weight: 700; margin-bottom: 6px; }}
            .biz-info {{ font-size: 0.82rem; color: #6b7280; margin-bottom: 4px; }}
            .rating-badge {{
                background: #fff7ed;
                color: #d97706;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 0.8rem;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 14px;
            }}
            .cat-badge {{
                background: #eff2ff;
                color: #4361ee;
                border-radius: 8px;
                padding: 3px 10px;
                font-size: 0.75rem;
                font-weight: 600;
            }}
            .btn-primary {{
                background: linear-gradient(135deg, #4361ee, #3a0ca3);
                border: none;
                border-radius: 10px;
                font-weight: 600;
                padding: 9px 20px;
            }}
            .btn-primary:hover {{ opacity: 0.9; }}
            .btn-outline-primary {{
                border: 1.5px solid #4361ee;
                color: #4361ee;
                border-radius: 10px;
                font-weight: 600;
            }}
            .btn-outline-primary:hover {{ background: #4361ee; color: white; }}
            .auth-card {{
                background: white;
                border: none;
                border-radius: 20px;
                box-shadow: 0 8px 40px rgba(0,0,0,0.1);
                padding: 40px;
            }}
            .review-card {{
                background: white;
                border-radius: 14px;
                padding: 18px 20px;
                margin-bottom: 14px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.05);
            }}
            .detail-card {{
                background: white;
                border-radius: 16px;
                padding: 28px;
                box-shadow: 0 2px 16px rgba(0,0,0,0.06);
                margin-bottom: 24px;
            }}
            footer {{
                text-align: center;
                color: #9ca3af;
                font-size: 0.82rem;
                padding: 32px 0 16px;
            }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark px-4">
            <a class="navbar-brand" href="/">🏢 Հայ Բիզնես</a>
            <div>{user_nav}</div>
        </nav>
        <div class="container py-4">
            {content}
        </div>
        <footer>© 2026 Հայ Բիզնես · Երևան, Հայաստան</footer>
    </body>
    </html>
    """)

# ── Home ──────────────────────────────────────────────────────────────
@app.route("/")
def home():
    q          = request.args.get("q", "")
    category   = request.args.get("category", "")
    businesses = Business.query

    if q:
        businesses = businesses.filter(Business.name.ilike(f"%{q}%"))
    if category:
        businesses = businesses.filter_by(category=category)

    businesses = businesses.all()
    categories = [c[0] for c in db.session.query(Business.category).distinct().all()]

    icons = {
        "Ռեստորան": "🍽️", "Սրճարան": "☕", "Խանութ": "🛍️",
        "Վարսավիրանոց": "✂️", "Բժշկություն": "🏥",
        "Կրթություն": "📚", "Այլ": "🏢"
    }

    cards = ""
    for b in businesses:
        icon = icons.get(b.category, "🏢")
        rating_text = f"⭐ {b.avg_rating}/5" if b.avg_rating else "Դեռ review չկա"
        cards += f"""
        <div class="col-md-4 mb-4">
            <div class="biz-card">
                <div class="biz-card-body">
                    <div class="biz-icon">{icon}</div>
                    <div class="biz-name">{b.name}</div>
                    <span class="cat-badge d-inline-block mb-3">{b.category}</span>
                    <p class="biz-info">📍 {b.address}</p>
                    <p class="biz-info">📞 {b.phone or "—"}</p>
                    <div class="rating-badge">{rating_text}</div>
                    <a href="/business/{b.id}" class="btn btn-primary btn-sm w-100">Տեսնել →</a>
                </div>
            </div>
        </div>
        """

    cat_options = "".join(
        f'<option value="{c}" {"selected" if c == category else ""}>{c}</option>'
        for c in categories
    )

    add_btn = "<a href='/add_business' class='btn btn-light fw-bold mt-3'>+ Ավելացնել բիզնես</a>" if "user_id" in session else "<a href='/register' class='btn btn-light fw-bold mt-3'>Անվճար գրանցվել →</a>"

    content = f"""
    <div class="hero">
        <h1>🏙️ Հայ Բիզնես</h1>
        <p>Գտիր լավագույն բիզնեսները Հայաստանում, կարդա reviews, թողիր կարծիք</p>
        {add_btn}
    </div>
    <div class="search-bar">
        <form method="GET" class="row g-2 align-items-center">
            <div class="col-md-6">
                <input name="q" class="form-control" placeholder="Որոնել բիզնես..." value="{q}">
            </div>
            <div class="col-md-4">
                <select name="category" class="form-select">
                    <option value="">Բոլոր կատեգորիաները</option>
                    {cat_options}
                </select>
            </div>
            <div class="col-md-2">
                <button class="btn btn-primary w-100">Որոնել</button>
            </div>
        </form>
    </div>
    <div class="row">
        {"".join(cards) if cards else "<p class='text-muted'>Բիզնեսներ չեն գտնվել</p>"}
    </div>
    """
    return base("Գլխավոր", content)

# ── Register ──────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        confirm  = request.form["confirm"]
        if not username or not password:
            error = "Բոլոր դաշտերը պարտադիր են"
        elif len(username) < 3:
            error = "Օգտանունը պետք է լինի առնվազն 3 նիշ"
        elif len(password) < 6:
            error = "Գաղտնաբառերը պետք է լինեն առնվազն 6 նիշ"
        elif password != confirm:
            error = "Գաղտնաբառերը չեն համընկնում"
        elif User.query.filter_by(username=username).first():
            error = "Այս օգտանունն արդեն զբաղեցված է"
        else:
            user = User(username=username, password=hash_password(password))
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("home"))

    err_html = f'<div class="alert alert-danger rounded-3">{error}</div>' if error else ""
    content = f"""
    <div class="row justify-content-center mt-4">
        <div class="col-md-5">
            <div class="auth-card">
                <div class="text-center mb-4">
                    <div style="font-size:2.5rem">🏢</div>
                    <h4 class="fw-bold mt-2">Գրանցում</h4>
                    <p class="text-muted small">Ստեղցեք ձեր հաշիվը</p>
                </div>
                {err_html}
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label fw-500">Օգտանուն</label>
                        <input name="username" class="form-control" placeholder="username" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-500">Գաղտնաբառ</label>
                        <input name="password" type="password" class="form-control" placeholder="••••••••" required>
                    </div>
                    <div class="mb-4">
                        <label class="form-label fw-500">Հաստատել գաղտնաբառը</label>
                        <input name="confirm" type="password" class="form-control" placeholder="••••••••" required>
                    </div>
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">Գրանցվել</button>
                    </div>
                </form>
                <p class="text-center text-muted small mt-3">
                    Արդեն հաշիվ ունե՞ք — <a href="/login" style="color:#4361ee">Մուտք</a>

                </p>
            </div>
        </div>
    </div>
    """
    return base("Գրանցում", content)

# ── Login ─────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=hash_password(password)).first()
        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("home"))
        error = "Սխալ օգտանուն կամ գաղտնաբառ"

    err_html = f'<div class="alert alert-danger rounded-3">{error}</div>' if error else ""
    content = f"""
    <div class="row justify-content-center mt-4">
        <div class="col-md-5">
            <div class="auth-card">
                <div class="text-center mb-4">
                    <div style="font-size:2.5rem">👤</div>
                    <h4 class="fw-bold mt-2">Մուտք գործել</h4>
                    <p class="text-muted small">Բարի գալուստ!</p>
                </div>
                {err_html}
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label fw-500">Օգտանուն</label>
                        <input name="username" class="form-control" placeholder="username" required>
                    </div>
                    <div class="mb-4">
                        <label class="form-label fw-500">Գաղտնաբառ</label>
                        <input name="password" type="password" class="form-control" placeholder="••••••••" required>
                    </div>
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">Մուտք գործել</button>
                    </div>
                </form>
                <div class="text-center mt-3">
                    <a href="/login/google" class="btn btn-outline-danger w-100">
                        Google-ով մուտք գործել
                    </a>
                </div>
                <p class="text-center text-muted small mt-3">
                    Հաշիվ չունե՞ք — <a href="/register" style="color:#4361ee">Գրանցվել</a>
                </p>
            </div>
        </div>
    </div>
    """
    return base("Մուտք", content)

# ── Logout ────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ── Business detail ───────────────────────────────────────────────────
@app.route("/business/<int:id>")
def business(id):
    b = Business.query.get_or_404(id)

    reviews_html = ""
    for r in b.reviews:
        reviews_html += f"""
        <div class="review-card">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <strong>👤 {r.author.username}</strong>
                <span style="color:#d97706">{"⭐" * r.rating}</span>
            </div>
            <p class="mb-1">{r.comment}</p>
            <small class="text-muted">{r.created_at.strftime("%d.%m.%Y")}</small>
        </div>
        """

    if "user_id" in session:
        review_form = f"""
        <div class="detail-card">
            <h5 class="fw-bold mb-3">✍️ Թող կարծիք</h5>
            <form method="POST" action="/review/{b.id}">
                <div class="mb-3">
                    <label class="form-label">Գնահատական</label>
                    <select name="rating" class="form-select">
                        <option value="5">⭐⭐⭐⭐⭐ — Հիանալի</option>
                        <option value="4">⭐⭐⭐⭐ — Լավ</option>
                        <option value="3">⭐⭐⭐ — Միջին</option>
                        <option value="2">⭐⭐ — Վատ</option>
                        <option value="1">⭐ — Շատ վատ</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Մեկնաբանություն</label>
                    <textarea name="comment" class="form-control" rows="3" required
                        placeholder="Թող կարծիքդ..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Ուղարկել</button>
            </form>
        </div>
        """
    else:
        review_form = '<div class="alert alert-info rounded-3">Review թողնելու համար <a href="/login">Մուտք գործել</a></div>'

    icon = {"Ռեստորան": "🍽️", "Սրճարան": "☕", "Խանութ": "🛍️"}.get(b.category, "🏢")
    rating_text = f"⭐ {b.avg_rating}/5 ({len(b.reviews)} review)" if b.reviews else "Դեռ review չկա"

    content = f"""
    <a href="/" class="btn btn-outline-secondary btn-sm mb-4">← Հետ</a>
    <div class="detail-card">
        <div class="d-flex align-items-center gap-3 mb-3">
            <div class="biz-icon" style="width:56px;height:56px;font-size:1.8rem">{icon}</div>
            <div>
                <h3 class="fw-bold mb-1">{b.name}</h3>
                <span class="cat-badge">{b.category}</span>
            </div>
        </div>
        <p class="mb-2">📍 {b.address}</p>
        <p class="mb-2">📞 {b.phone or "—"}</p>
        <div class="rating-badge">{rating_text}</div>
    </div>
    {review_form}
    <h5 class="fw-bold mb-3">Reviews ({len(b.reviews)})</h5>
    {reviews_html or "<p class='text-muted'>Դեռ review չկա</p>"}
    """
    return base(b.name, content)

# ── Add review ────────────────────────────────────────────────────────
@app.route("/review/<int:business_id>", methods=["POST"])
def add_review(business_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    review = Review(
        rating=int(request.form["rating"]),
        comment=request.form["comment"],
        user_id=session["user_id"],
        business_id=business_id
    )
    db.session.add(review)
    db.session.commit()
    return redirect(url_for("business", id=business_id))

# ── Add business ──────────────────────────────────────────────────────
@app.route("/add_business", methods=["GET", "POST"])
def add_business():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        b = Business(
            name=request.form["name"],
            category=request.form["category"],
            address=request.form["address"],
            phone=request.form.get("phone", "")
        )
        db.session.add(b)
        db.session.commit()
        return redirect(url_for("business", id=b.id))

    content = """
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="auth-card">
                <h4 class="fw-bold mb-4">🏢 Ավելացնել բիզնես</h4>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Բիզնեսի անուն</label>
                        <input name="name" class="form-control" placeholder="օր՝. Coffee Room" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Կատեգորիա</label>
                        <select name="category" class="form-select">
                            <option>Ռեստորան</option>
                            <option>Սրճարան</option>
                            <option>Խանութ</option>
                            <option>Վարսավիրանոց</option>
                            <option>Բժշկություն</option>
                            <option>Կրթություն</option>
                            <option>Այլ</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Հասցե</label>
                        <input name="address" class="form-control" placeholder="օր՝. Abovyan 12, Yerevan" required>
                    </div>
                    <div class="mb-4">
                        <label class="form-label">Հեռախոս</label>
                        <input name="phone" class="form-control" placeholder="+374 XX XXX XXX">
                    </div>
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">Ավելացնել</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    """
    return base("Ավելացնել բիզնես", content)

# ── Init & run ────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)