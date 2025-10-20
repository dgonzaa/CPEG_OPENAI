from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
from dotenv import load_dotenv
from flask_cors import CORS
import os

# --- Load environment variables ---
load_dotenv()

# --- Setup paths ---
base_dir = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(base_dir, "templates")
static_path = os.path.join(base_dir, "static")

# --- Initialize Flask ---
app = Flask(__name__, template_folder=template_path, static_folder=static_path)
# temporary code 
print(">>> Flask static folder:", app.static_folder)
print(">>> Exists on disk?:", os.path.exists(app.static_folder))
print(">>> CSS path exists?:", os.path.exists(os.path.join(app.static_folder, "style.css")))

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# --- Database setup ---
db_path = os.path.join(base_dir, "instance", "users.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://cpeg_openai_db_user:1eNJf4ZSerINEkrLSTLABOibpsrgWK9k@dpg-d3rc9qu3jp1c738ropa0-a/cpeg_openai_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

# ---------------- STATIC + FRONTEND ROUTES ---------------- #

@app.route('/test-css')
def test_css():
    return send_from_directory('static', 'style.css')

@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({"message": "Backend connection successful!"})

@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    return send_from_directory('frontend', filename)

@app.route('/frontend')
def frontend_index():
    return send_from_directory('frontend', 'index.html')

# ---------------- STANDARD WEB ROUTES ---------------- #

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password."
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return "Username already exists."

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    user_id = session["user_id"]
    chat_history = ChatHistory.query.filter_by(user_id=user_id).all()

    if request.method == "POST":
        user_prompt = request.form['prompt']
        db.session.add(ChatHistory(user_id=user_id, role='user', content=user_prompt))
        db.session.commit()

        ai_response = ""
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a friendly AI assistant for engineering students."},
                    {"role": "user", "content": user_prompt}
                ]
            )
            ai_response = completion.choices[0].message.content
        except Exception as e:
            ai_response = f"Error: {str(e)}"

        db.session.add(ChatHistory(user_id=user_id, role='assistant', content=ai_response))
        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("dashboard.html", username=username, chat_history=chat_history)

# ---------------- API ROUTES (for frontend JS) ---------------- #

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username, password=password).first()
    if user:
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"message": "Invalid username or password."}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists."}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Registration successful!"}), 201

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    user_prompt = data.get('prompt')

    ai_response = ""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly AI assistant for engineering students."},
                {"role": "user", "content": user_prompt}
            ]
        )
        ai_response = completion.choices[0].message.content
    except Exception as e:
        ai_response = f"Error: {str(e)}"

    return jsonify({"response": ai_response})

# ---------------- RUN APP ---------------- #

if __name__ == '__main__':
    app.run(debug=True, port=5001)
