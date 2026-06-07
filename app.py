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

ICONS = {
    "Ռեստորան": "🍽️",
    "Սրճարան": "☕",
    "Խանութ": "🛍️",
    "Վարսավիրանոց": "✂️",
    "Բժշկություն": "🏥",
    "Կրթություն": "📚",
    "Այլ": "🏢"
}

CAT_COLORS = {
    "Ռեստորան":    ("#fff1ee", "#c0392b"),
    "Սրճարան":     ("#fef9ee", "#b7791f"),
    "Խանութ":      ("#eef4ff", "#2563eb"),
    "Վարսավիրանոց":("#f4eeff", "#7c3aed"),
    "Բժշկություն": ("#eefbf3", "#16a34a"),
    "Կրթություն":  ("#fff8ee", "#d97706"),
    "Այլ":         ("#f3f4f6", "#6b7280"),
}

# ── Base template ─────────────────────────────────────────────────────
def base(title, content):
    if "user_id" in session:
        user_nav = f"""
        <div class="nav-user">
            <span class="nav-username">👤 {session.get('username')}</span>
            <a href="/logout" class="btn-nav-outline">Ելք</a>
        </div>
        """
    else:
        user_nav = """
        <div class="nav-user">
            <a href="/login" class="btn-nav-outline">Մուտք</a>
            <a href="/register" class="btn-nav-solid">Գրանցում</a>
        </div>
        """

    return render_template_string(f"""
<!DOCTYPE html>
<html lang="hy">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} — Հայ Բիզնես</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;1,500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

        :root {{
            --red:      #C0392B;
            --red-dark: #922b21;
            --navy:     #1a1a2e;
            --navy2:    #16213e;
            --navy3:    #0f3460;
            --gold:     #e8c4a0;
            --bg:       #f7f5f2;
            --white:    #ffffff;
            --border:   #e8e4df;
            --text:     #1a1a1a;
            --muted:    #6b6b6b;
            --radius:   12px;
        }}

        body {{
            font-family: 'DM Sans', sans-serif;
            background: var(--bg);
            color: var(--text);
            font-size: 15px;
            line-height: 1.6;
        }}

        /* ── Navbar ── */
        .navbar {{
            background: var(--white);
            border-bottom: 1px solid var(--border);
            padding: 0 40px;
            height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .navbar-logo {{
            font-family: 'Playfair Display', serif;
            font-size: 22px;
            font-weight: 600;
            color: var(--navy);
            text-decoration: none;
            letter-spacing: -0.3px;
        }}
        .navbar-logo span {{ color: var(--red); }}
        .navbar-links {{
            display: flex;
            gap: 32px;
            list-style: none;
        }}
        .navbar-links a {{
            text-decoration: none;
            color: var(--muted);
            font-size: 14px;
            font-weight: 400;
            transition: color 0.15s;
        }}
        .navbar-links a:hover {{ color: var(--text); }}
        .nav-user {{ display: flex; align-items: center; gap: 12px; }}
        .nav-username {{ font-size: 13px; color: var(--muted); }}
        .btn-nav-outline {{
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 7px 16px;
            transition: background 0.15s;
        }}
        .btn-nav-outline:hover {{ background: var(--bg); }}
        .btn-nav-solid {{
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            color: var(--white);
            background: var(--red);
            border-radius: 8px;
            padding: 7px 16px;
            transition: background 0.15s;
        }}
        .btn-nav-solid:hover {{ background: var(--red-dark); }}

        /* ── Hero ── */
        .hero {{
            background: linear-gradient(135deg, var(--navy) 0%, var(--navy2) 50%, var(--navy3) 100%);
            padding: 72px 40px 64px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .hero::before {{
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(ellipse at 70% 50%, rgba(192,57,43,0.12) 0%, transparent 60%);
        }}
        .hero-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            color: rgba(255,255,255,0.7);
            border-radius: 20px;
            font-size: 12px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            padding: 5px 16px;
            margin-bottom: 24px;
        }}
        .hero h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 52px;
            font-weight: 600;
            color: #fff;
            line-height: 1.1;
            margin-bottom: 16px;
            position: relative;
        }}
        .hero h1 em {{
            font-style: italic;
            color: var(--gold);
        }}
        .hero-sub {{
            color: rgba(255,255,255,0.55);
            font-size: 16px;
            font-weight: 300;
            margin-bottom: 40px;
            position: relative;
        }}

        /* ── Search ── */
        .search-wrap {{
            display: flex;
            gap: 0;
            max-width: 560px;
            margin: 0 auto 20px;
            background: #fff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 12px 40px rgba(0,0,0,0.25);
            position: relative;
        }}
        .search-wrap input {{
            flex: 1;
            border: none;
            padding: 16px 20px;
            font-size: 14px;
            font-family: 'DM Sans', sans-serif;
            outline: none;
            color: #222;
        }}
        .search-wrap select {{
            border: none;
            border-left: 1px solid #eee;
            padding: 16px 14px;
            font-size: 13px;
            color: #555;
            outline: none;
            background: #fff;
            font-family: 'DM Sans', sans-serif;
            cursor: pointer;
        }}
        .search-wrap button {{
            background: var(--red);
            color: #fff;
            border: none;
            padding: 16px 24px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            font-family: 'DM Sans', sans-serif;
            transition: background 0.15s;
        }}
        .search-wrap button:hover {{ background: var(--red-dark); }}

        .hero-cats {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: center;
            position: relative;
        }}
        .hero-cat {{
            background: rgba(255,255,255,0.07);
            color: rgba(255,255,255,0.65);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 12px;
            text-decoration: none;
            transition: background 0.15s;
        }}
        .hero-cat:hover {{ background: rgba(255,255,255,0.14); color: #fff; }}

        /* ── Stats bar ── */
        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            background: var(--white);
            border-bottom: 1px solid var(--border);
        }}
        .stat-item {{
            padding: 28px 20px;
            text-align: center;
            border-right: 1px solid var(--border);
        }}
        .stat-item:last-child {{ border-right: none; }}
        .stat-num {{
            font-family: 'Playfair Display', serif;
            font-size: 34px;
            font-weight: 600;
            color: var(--red);
            line-height: 1;
        }}
        .stat-lbl {{
            font-size: 12px;
            color: var(--muted);
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* ── Container ── */
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 48px 40px;
        }}
        .section-header {{
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            margin-bottom: 28px;
        }}
        .section-title {{
            font-family: 'Playfair Display', serif;
            font-size: 26px;
            font-weight: 600;
        }}
        .section-link {{
            font-size: 13px;
            color: var(--red);
            text-decoration: none;
        }}

        /* ── Business cards ── */
        .biz-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }}
        .biz-card {{
            background: var(--white);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            text-decoration: none;
            color: inherit;
            display: block;
            transition: transform 0.18s, box-shadow 0.18s;
        }}
        .biz-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 32px rgba(0,0,0,0.1);
        }}
        .biz-card-top {{
            height: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            position: relative;
        }}
        .biz-card-body {{ padding: 18px 20px 20px; }}
        .biz-cat-pill {{
            display: inline-block;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 500;
            padding: 3px 10px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .biz-name {{
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 6px;
        }}
        .biz-info {{
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 3px;
        }}
        .biz-rating {{
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
        }}
        .stars {{ color: #f59e0b; font-size: 13px; }}
        .rating-text {{ font-size: 12px; color: var(--muted); }}
        .biz-btn {{
            display: block;
            margin-top: 14px;
            background: var(--navy);
            color: #fff;
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            text-decoration: none;
            transition: background 0.15s;
        }}
        .biz-btn:hover {{ background: var(--navy3); }}

        /* ── CTA banner ── */
        .cta-banner {{
            background: var(--navy3);
            border-radius: 16px;
            padding: 36px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 48px;
            gap: 20px;
        }}
        .cta-banner h3 {{
            font-family: 'Playfair Display', serif;
            font-size: 22px;
            color: #fff;
            margin-bottom: 6px;
        }}
        .cta-banner p {{ font-size: 14px; color: rgba(255,255,255,0.55); }}
        .cta-btn {{
            background: var(--red);
            color: #fff;
            border: none;
            border-radius: 10px;
            padding: 13px 28px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            white-space: nowrap;
            font-family: 'DM Sans', sans-serif;
            transition: background 0.15s;
        }}
        .cta-btn:hover {{ background: var(--red-dark); color: #fff; }}

        /* ── Auth forms ── */
        .auth-wrap {{
            max-width: 440px;
            margin: 48px auto;
        }}
        .auth-card {{
            background: var(--white);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 44px 40px;
        }}
        .auth-icon {{
            width: 56px; height: 56px;
            background: #fff1ee;
            border-radius: 14px;
            display: flex; align-items: center; justify-content: center;
            font-size: 26px;
            margin: 0 auto 20px;
        }}
        .auth-title {{
            font-family: 'Playfair Display', serif;
            font-size: 24px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 6px;
        }}
        .auth-sub {{
            font-size: 14px;
            color: var(--muted);
            text-align: center;
            margin-bottom: 28px;
        }}

        /* ── Form elements ── */
        .form-group {{ margin-bottom: 18px; }}
        .form-label {{
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 6px;
            color: var(--text);
        }}
        .form-input, .form-select, .form-textarea {{
            width: 100%;
            border: 1px solid var(--border);
            border-radius: 9px;
            padding: 11px 14px;
            font-size: 14px;
            font-family: 'DM Sans', sans-serif;
            outline: none;
            color: var(--text);
            background: #fff;
            transition: border-color 0.15s, box-shadow 0.15s;
        }}
        .form-input:focus, .form-select:focus, .form-textarea:focus {{
            border-color: var(--red);
            box-shadow: 0 0 0 3px rgba(192,57,43,0.08);
        }}
        .form-textarea {{ resize: vertical; min-height: 100px; }}
        .btn-submit {{
            width: 100%;
            background: var(--red);
            color: #fff;
            border: none;
            border-radius: 10px;
            padding: 13px;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            font-family: 'DM Sans', sans-serif;
            transition: background 0.15s;
        }}
        .btn-submit:hover {{ background: var(--red-dark); }}
        .btn-google {{
            width: 100%;
            background: #fff;
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            font-family: 'DM Sans', sans-serif;
            text-decoration: none;
            display: block;
            text-align: center;
            margin-top: 12px;
            transition: background 0.15s;
        }}
        .btn-google:hover {{ background: var(--bg); }}
        .auth-footer {{
            text-align: center;
            font-size: 13px;
            color: var(--muted);
            margin-top: 20px;
        }}
        .auth-footer a {{ color: var(--red); text-decoration: none; }}
        .divider {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 16px 0;
            color: var(--muted);
            font-size: 12px;
        }}
        .divider::before, .divider::after {{
            content: '';
            flex: 1;
            height: 1px;
            background: var(--border);
        }}

        /* ── Alert ── */
        .alert-error {{
            background: #fff1ee;
            border: 1px solid #f5c6be;
            color: #922b21;
            border-radius: 9px;
            padding: 12px 16px;
            font-size: 13px;
            margin-bottom: 20px;
        }}
        .alert-info {{
            background: #eef4ff;
            border: 1px solid #c3d4f8;
            color: #1d4ed8;
            border-radius: 9px;
            padding: 12px 16px;
            font-size: 13px;
            margin-bottom: 20px;
        }}
        .alert-info a {{ color: #1d4ed8; }}

        /* ── Detail page ── */
        .detail-header {{
            background: var(--white);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            display: flex;
            align-items: flex-start;
            gap: 20px;
        }}
        .detail-icon {{
            width: 64px; height: 64px;
            border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-size: 30px;
            flex-shrink: 0;
        }}
        .detail-meta {{ flex: 1; }}
        .detail-name {{
            font-family: 'Playfair Display', serif;
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .detail-info {{ font-size: 14px; color: var(--muted); margin-bottom: 4px; }}
        .detail-rating {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #fff7ed;
            border: 1px solid #fde68a;
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 14px;
            font-weight: 500;
            color: #92400e;
            margin-top: 10px;
        }}

        .review-form-card {{
            background: var(--white);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px 32px;
            margin-bottom: 24px;
        }}
        .review-form-title {{
            font-size: 17px;
            font-weight: 500;
            margin-bottom: 20px;
        }}

        .review-item {{
            background: var(--white);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 12px;
        }}
        .review-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .review-author {{ font-weight: 500; font-size: 14px; }}
        .review-date {{ font-size: 12px; color: var(--muted); }}
        .review-comment {{ font-size: 14px; color: var(--muted); line-height: 1.6; }}

        .btn-back {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: var(--muted);
            text-decoration: none;
            margin-bottom: 24px;
            transition: color 0.15s;
        }}
        .btn-back:hover {{ color: var(--text); }}

        .reviews-title {{
            font-family: 'Playfair Display', serif;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
        }}

        .no-results {{
            text-align: center;
            padding: 60px 20px;
            color: var(--muted);
            font-size: 15px;
        }}

        /* ── Footer ── */
        footer {{
            border-top: 1px solid var(--border);
            background: var(--white);
            text-align: center;
            color: var(--muted);
            font-size: 13px;
            padding: 24px 40px;
        }}
    </style>
</head>
<body>

<nav class="navbar">
    <a class="navbar-logo" href="/">Հայ<span>Բիզնես</span></a>
    <ul class="navbar-links">
        <li><a href="/">Բիզնեսներ</a></li>
        <li><a href="/?category=Ռեստորան">Ռեստորաններ</a></li>
        <li><a href="/add_business">Ավելացնել</a></li>
    </ul>
    {user_nav}
</nav>

{content}

<footer>© 2026 ՀայԲիզնես · Երևան, Հայաստան</footer>
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
    total_biz  = Business.query.count()
    all_reviews = Review.query.all()
    avg_overall = round(sum(r.rating for r in all_reviews) / len(all_reviews), 1) if all_reviews else "—"

    cat_options = "".join(
        f'<option value="{c}" {"selected" if c == category else ""}>{c}</option>'
        for c in ["Ռեստորան","Սրճարան","Խանութ","Վարսավիրանոց","Բժշկություն","Կրթություն","Այլ"]
    )

    cat_links = "".join(
        f'<a href="/?category={c}" class="hero-cat">{ICONS.get(c,"")} {c}</a>'
        for c in ["Ռեստորան","Սրճարան","Խանութ","Վարսավիրանոց","Բժշկություն","Կրթություն"]
    )

    cards = ""
    for b in businesses:
        icon = ICONS.get(b.category, "🏢")
        bg, col = CAT_COLORS.get(b.category, ("#f3f4f6","#6b7280"))
        stars_count = int(round(b.avg_rating))
        stars = "★" * stars_count + "☆" * (5 - stars_count) if b.avg_rating else "☆☆☆☆☆"
        rating_html = f'<span class="stars">{stars}</span><span class="rating-text">{b.avg_rating}/5 ({len(b.reviews)})</span>' if b.reviews else '<span class="rating-text">Դեռ review չկա</span>'

        cards += f"""
        <div class="biz-card" style="cursor:pointer" onclick="location.href='/business/{b.id}'">
            <div class="biz-card-top" style="background:{bg};">{icon}</div>
            <div class="biz-card-body">
                <span class="biz-cat-pill" style="background:{bg};color:{col};">{b.category}</span>
                <div class="biz-name">{b.name}</div>
                <div class="biz-info">📍 {b.address}</div>
                <div class="biz-info">📞 {b.phone or "—"}</div>
                <div class="biz-rating">{rating_html}</div>
                <a href="/business/{b.id}" class="biz-btn">Մանրամասներ →</a>
            </div>
        </div>
        """

    cta_link = "/add_business" if "user_id" in session else "/register"
    cta_text = "Ավելացնել բիզնես" if "user_id" in session else "Անվճար գրանցվել →"

    content = f"""
<div class="hero">
    <div class="hero-badge">🇦🇲 Հայաստանի բիզնես ցանցը</div>
    <h1>Գտեք լավագույն<br><em>բիզնեսները Հայաստանում</em></h1>
    <p class="hero-sub">Ռեստորաններ, սրճարաններ, կլինիկաներ — բոլորն այստեղ</p>
    <form method="GET" class="search-wrap">
        <input name="q" placeholder="Փնտրեք բիզնես..." value="{q}">
        <select name="category">
            <option value="">Բոլոր կատեգ.</option>
            {cat_options}
        </select>
        <button type="submit">Փնտրել</button>
    </form>
    <div class="hero-cats">{cat_links}</div>
</div>

<div class="stats-bar">
    <div class="stat-item">
        <div class="stat-num">{total_biz}</div>
        <div class="stat-lbl">Բիզնեսներ</div>
    </div>
    <div class="stat-item">
        <div class="stat-num">7</div>
        <div class="stat-lbl">Կատեգորիա</div>
    </div>
    <div class="stat-item">
        <div class="stat-num">{'⭐ ' + str(avg_overall) if avg_overall != '—' else '—'}</div>
        <div class="stat-lbl">Միջին գնահատական</div>
    </div>
</div>

<div class="container">
    <div class="section-header">
        <h2 class="section-title">{'Որոնման արդյունքներ' if q or category else 'Բոլոր բիզնեսները'}</h2>
        <span style="font-size:13px;color:var(--muted);">{len(businesses)} հատ</span>
    </div>

    {"<div class='biz-grid'>" + cards + "</div>" if cards else "<div class='no-results'>🔍 Բիզնեսներ չեն գտնվել</div>"}

    <div class="cta-banner">
        <div>
            <h3>Ունե՞ք բիզնես Հայաստանում</h3>
            <p>Ավելացրեք ձեր բիզնեսը անվճար — հաճախորդներ կգտնեք ավելի արագ</p>
        </div>
        <a href="{cta_link}" class="cta-btn">+ {cta_text}</a>
    </div>
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
            error = "Գաղտնաբառը պետք է լինի առնվազն 6 նիշ"
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

    err_html = f'<div class="alert-error">{error}</div>' if error else ""
    content = f"""
<div class="auth-wrap">
    <div class="auth-card">
        <div class="auth-icon">🏢</div>
        <div class="auth-title">Գրանցում</div>
        <div class="auth-sub">Ստեղծեք ձեր անվճար հաշիվը</div>
        {err_html}
        <form method="POST">
            <div class="form-group">
                <label class="form-label">Օգտանուն</label>
                <input name="username" class="form-input" placeholder="username" required>
            </div>
            <div class="form-group">
                <label class="form-label">Գաղտնաբառ</label>
                <input name="password" type="password" class="form-input" placeholder="••••••••" required>
            </div>
            <div class="form-group">
                <label class="form-label">Հաստատել գաղտնաբառը</label>
                <input name="confirm" type="password" class="form-input" placeholder="••••••••" required>
            </div>
            <button type="submit" class="btn-submit">Գրանցվել</button>
        </form>
        <p class="auth-footer">Արդեն հաշիվ ունե՞ք — <a href="/login">Մուտք գործել</a></p>
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

    err_html = f'<div class="alert-error">{error}</div>' if error else ""
    content = f"""
<div class="auth-wrap">
    <div class="auth-card">
        <div class="auth-icon">👤</div>
        <div class="auth-title">Բարի գալուստ</div>
        <div class="auth-sub">Մուտք գործեք ձեր հաշիվ</div>
        {err_html}
        <form method="POST">
            <div class="form-group">
                <label class="form-label">Օգտանուն</label>
                <input name="username" class="form-input" placeholder="username" required>
            </div>
            <div class="form-group">
                <label class="form-label">Գաղտնաբառ</label>
                <input name="password" type="password" class="form-input" placeholder="••••••••" required>
            </div>
            <button type="submit" class="btn-submit">Մուտք գործել</button>
        </form>
        <div class="divider">կամ</div>
        <a href="/login/google" class="btn-google">🔵 Google-ով մուտք գործել</a>
        <p class="auth-footer">Հաշիվ չունե՞ք — <a href="/register">Գրանցվել</a></p>
    </div>
</div>
"""
    return base("Մուտք", content)


@app.route("/google_login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    info = resp.json()
    email = info["email"]
    name  = info.get("name", email.split("@")[0])
    user = User.query.filter_by(username=email).first()
    if not user:
        user = User(username=email, password=hash_password(os.urandom(16).hex()))
        db.session.add(user)
        db.session.commit()
    session["user_id"] = user.id
    session["username"] = name
    return redirect(url_for("home"))


# ── Logout ────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ── Business detail ───────────────────────────────────────────────────
@app.route("/business/<int:id>")
def business(id):
    b = Business.query.get_or_404(id)
    icon = ICONS.get(b.category, "🏢")
    bg, col = CAT_COLORS.get(b.category, ("#f3f4f6","#6b7280"))

    stars_count = int(round(b.avg_rating))
    stars = "★" * stars_count + "☆" * (5 - stars_count) if b.avg_rating else "☆☆☆☆☆"
    rating_html = f'<span style="color:#f59e0b">{stars}</span> {b.avg_rating}/5 · {len(b.reviews)} review' if b.reviews else "Դեռ review չկա"

    reviews_html = ""
    for r in b.reviews:
        r_stars = "★" * r.rating + "☆" * (5 - r.rating)
        reviews_html += f"""
        <div class="review-item">
            <div class="review-header">
                <span class="review-author">👤 {r.author.username}</span>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="color:#f59e0b;font-size:13px">{r_stars}</span>
                    <span class="review-date">{r.created_at.strftime("%d.%m.%Y")}</span>
                </div>
            </div>
            <p class="review-comment">{r.comment}</p>
        </div>
        """

    if "user_id" in session:
        review_form = f"""
        <div class="review-form-card">
            <div class="review-form-title">✍️ Թողեք կարծիք</div>
            <form method="POST" action="/review/{b.id}">
                <div class="form-group">
                    <label class="form-label">Գնահատական</label>
                    <select name="rating" class="form-select">
                        <option value="5">⭐⭐⭐⭐⭐ Հիանալի</option>
                        <option value="4">⭐⭐⭐⭐ Լավ</option>
                        <option value="3">⭐⭐⭐ Միջին</option>
                        <option value="2">⭐⭐ Վատ</option>
                        <option value="1">⭐ Շատ վատ</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Մեկնաբանություն</label>
                    <textarea name="comment" class="form-textarea" required placeholder="Կիսվեք ձեր փորձով..."></textarea>
                </div>
                <button type="submit" class="btn-submit" style="width:auto;padding:11px 28px;">Ուղարկել կարծիքը</button>
            </form>
        </div>
        """
    else:
        review_form = f'<div class="alert-info">Review թողնելու համար <a href="/login">մուտք գործեք</a></div>'

    content = f"""
<div class="container">
    <a href="/" class="btn-back">← Հետ</a>
    <div class="detail-header">
        <div class="detail-icon" style="background:{bg};">{icon}</div>
        <div class="detail-meta">
            <span class="biz-cat-pill" style="background:{bg};color:{col};display:inline-block;border-radius:6px;font-size:11px;font-weight:500;padding:3px 10px;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px;">{b.category}</span>
            <div class="detail-name">{b.name}</div>
            <div class="detail-info">📍 {b.address}</div>
            <div class="detail-info">📞 {b.phone or "—"}</div>
            <div class="detail-rating">{rating_html}</div>
        </div>
    </div>

    {review_form}

    <div class="reviews-title">Կարծիքներ ({len(b.reviews)})</div>
    {reviews_html if reviews_html else '<p style="color:var(--muted);font-size:14px;">Դեռ կարծիք չկա — եղիր առաջինը!</p>'}
</div>
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
<div class="auth-wrap" style="max-width:520px;">
    <div class="auth-card">
        <div class="auth-icon">🏢</div>
        <div class="auth-title">Ավելացնել բիզնես</div>
        <div class="auth-sub">Անվճար — 2 րոպեում</div>
        <form method="POST">
            <div class="form-group">
                <label class="form-label">Բիզնեսի անուն</label>
                <input name="name" class="form-input" placeholder="օր.՝ Coffee Room" required>
            </div>
            <div class="form-group">
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
            <div class="form-group">
                <label class="form-label">Հասցե</label>
                <input name="address" class="form-input" placeholder="օր.՝ Աբովյան 12, Երևան" required>
            </div>
            <div class="form-group">
                <label class="form-label">Հեռախոս</label>
                <input name="phone" class="form-input" placeholder="+374 XX XXX XXX">
            </div>
            <button type="submit" class="btn-submit">Ավելացնել բիզնես</button>
        </form>
    </div>
</div>
"""
    return base("Ավելացնել բիզնես", content)


# ── Init & run ────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)