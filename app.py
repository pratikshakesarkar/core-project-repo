from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mysqldb import MySQL
import json, hashlib, os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'studybuddy_secret_2024'

app.config['MYSQL_HOST']        = 'localhost'
app.config['MYSQL_USER']        = 'root'
app.config['MYSQL_PASSWORD']    = 'user123'
app.config['MYSQL_DB']          = 'study_buddy'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# ── Helpers ───────────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*a, **kw)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return redirect(url_for('dashboard'))
        return f(*a, **kw)
    return decorated

def ai_generate(prompt, max_tokens=800):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))
        msg = client.messages.create(
            model='claude-sonnet-4-5',
            max_tokens=max_tokens,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"[AI unavailable: {e}]"

# ── Index ─────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('dashboard'))

# ── Auth ──────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        d = request.get_json()
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s AND is_active=1",
                    (d['email'], hash_pw(d['password'])))
        user = cur.fetchone()
        if user:
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            session['email']    = user['email']
            redir = url_for('admin_dashboard') if user['role'] == 'admin' else url_for('dashboard')
            return jsonify({'ok': True, 'role': user['role'], 'redirect': redir})
        return jsonify({'ok': False, 'msg': 'Invalid credentials or account inactive'})
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        d = request.get_json()
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password, role) VALUES (%s,%s,%s,'user')",
                (d['username'], d['email'], hash_pw(d['password']))
            )
            mysql.connection.commit()
            return jsonify({'ok': True})
        except:
            return jsonify({'ok': False, 'msg': 'Email already registered'})
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── User Dashboard ────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM notes WHERE user_id=%s ORDER BY created_at DESC LIMIT 5",
                (session['user_id'],))
    notes = cur.fetchall()
    cur.execute("SELECT COUNT(*) as c FROM notes WHERE user_id=%s", (session['user_id'],))
    note_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM quiz_sessions WHERE user_id=%s", (session['user_id'],))
    quiz_count = cur.fetchone()['c']
    cur.execute("SELECT AVG(score) as avg FROM quiz_sessions WHERE user_id=%s", (session['user_id'],))
    row = cur.fetchone()
    avg_score = round(row['avg'] or 0, 1)
    return render_template('dashboard.html',
        notes=notes, note_count=note_count,
        quiz_count=quiz_count, avg_score=avg_score,
        username=session['username'], role=session['role'])

# ── Admin Dashboard ───────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='user'")
    user_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM notes")
    note_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM quizzes")
    quiz_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM quiz_sessions")
    session_count = cur.fetchone()['c']
    cur.execute("""
        SELECT u.id, u.username, u.email, u.created_at, u.is_active,
               COUNT(DISTINCT n.id) as notes, COUNT(DISTINCT qs.id) as quizzes
        FROM users u
        LEFT JOIN notes n ON n.user_id = u.id
        LEFT JOIN quiz_sessions qs ON qs.user_id = u.id
        WHERE u.role='user'
        GROUP BY u.id ORDER BY u.created_at DESC
    """)
    users = cur.fetchall()
    cur.execute("""
        SELECT u.username, qs.score, qs.taken_at, q.topic
        FROM quiz_sessions qs
        JOIN users u ON u.id = qs.user_id
        JOIN quizzes q ON q.id = qs.quiz_id
        ORDER BY qs.taken_at DESC LIMIT 10
    """)
    recent_sessions = cur.fetchall()
    return render_template('admin_dashboard.html',
        user_count=user_count, note_count=note_count,
        quiz_count=quiz_count, session_count=session_count,
        users=users, recent_sessions=recent_sessions,
        username=session['username'])

@app.route('/api/admin/users/<int:uid>/toggle', methods=['POST'])
@admin_required
def toggle_user(uid):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET is_active = NOT is_active WHERE id=%s AND role='user'", (uid,))
    mysql.connection.commit()
    return jsonify({'ok': True})

@app.route('/api/admin/users/<int:uid>', methods=['DELETE'])
@admin_required
def delete_user(uid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE id=%s AND role='user'", (uid,))
    mysql.connection.commit()
    return jsonify({'ok': True})

# ── Notes ─────────────────────────────────────────────────────
@app.route('/notes')
@login_required
def notes_page():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM notes WHERE user_id=%s ORDER BY created_at DESC",
                (session['user_id'],))
    return render_template('notes.html', notes=cur.fetchall(),
                           username=session['username'], role=session['role'])

@app.route('/api/notes', methods=['POST'])
@login_required
def create_note():
    d = request.get_json()
    topic   = d.get('topic', '').strip()
    content = d.get('content', '').strip()
    if not topic or not content:
        return jsonify({'ok': False, 'msg': 'Topic and content are required'})
    summary = ai_generate(
        f"Summarize these study notes on '{topic}' into clean bullet points (max 150 words):\n\n{content}"
    )
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO notes (user_id,topic,raw_content,summary) VALUES (%s,%s,%s,%s)",
                (session['user_id'], topic, content, summary))
    mysql.connection.commit()
    return jsonify({'ok': True, 'summary': summary})

@app.route('/api/notes/<int:nid>', methods=['DELETE'])
@login_required
def delete_note(nid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM notes WHERE id=%s AND user_id=%s", (nid, session['user_id']))
    mysql.connection.commit()
    return jsonify({'ok': True})

# ── Quiz ──────────────────────────────────────────────────────
@app.route('/quiz')
@login_required
def quiz_page():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM quizzes WHERE user_id=%s ORDER BY created_at DESC",
                (session['user_id'],))
    return render_template('quiz.html', quizzes=cur.fetchall(),
                           username=session['username'], role=session['role'])

@app.route('/api/quiz/generate', methods=['POST'])
@login_required
def generate_quiz():
    d = request.get_json()
    topic = d.get('topic', '').strip()
    num   = min(int(d.get('num_questions', 5)), 10)
    diff  = d.get('difficulty', 'medium')
    if not topic:
        return jsonify({'ok': False, 'msg': 'Topic is required'})
    prompt = (
        f"Generate {num} multiple-choice questions on '{topic}' at {diff} difficulty. "
        "Return ONLY valid JSON, no markdown fences:\n"
        '{"questions":[{"question":"...","options":["A) ...","B) ...","C) ...","D) ..."],"answer":"A","explanation":"..."}]}'
    )
    raw = ai_generate(prompt, max_tokens=2000)
    if raw.startswith('[AI unavailable'):
        return jsonify({'ok': False, 'msg': raw})
    if '```' in raw:
        raw = raw.split('```')[1]
        if raw.startswith('json'): raw = raw[4:]
    try:
        data = json.loads(raw.strip())
    except:
        return jsonify({'ok': False, 'msg': 'Failed to parse quiz. Try again.'})
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO quizzes (user_id,topic,difficulty,questions) VALUES (%s,%s,%s,%s)",
                (session['user_id'], topic, diff, json.dumps(data['questions'])))
    mysql.connection.commit()
    return jsonify({'ok': True, 'quiz_id': cur.lastrowid, 'questions': data['questions']})

@app.route('/api/quiz/<int:qid>/submit', methods=['POST'])
@login_required
def submit_quiz(qid):
    d = request.get_json()
    answers = d.get('answers', {})
    cur = mysql.connection.cursor()
    cur.execute("SELECT questions FROM quizzes WHERE id=%s AND user_id=%s", (qid, session['user_id']))
    row = cur.fetchone()
    if not row:
        return jsonify({'ok': False, 'msg': 'Quiz not found'})
    questions = json.loads(row['questions'])
    correct = sum(1 for i, q in enumerate(questions)
                  if answers.get(str(i), '').upper() == q['answer'].upper())
    score = round((correct / len(questions)) * 100)
    cur.execute("INSERT INTO quiz_sessions (user_id,quiz_id,score,answers) VALUES (%s,%s,%s,%s)",
                (session['user_id'], qid, score, json.dumps(answers)))
    mysql.connection.commit()
    return jsonify({'ok': True, 'score': score, 'correct': correct, 'total': len(questions)})

# ── Profile ───────────────────────────────────────────────────
@app.route('/profile')
@login_required
def profile():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    return render_template('profile.html', user=user,
                           username=session['username'], role=session['role'])

@app.route('/api/profile', methods=['POST'])
@login_required
def update_profile():
    d = request.get_json()
    cur = mysql.connection.cursor()
    if d.get('new_password'):
        cur.execute("UPDATE users SET username=%s, password=%s WHERE id=%s",
                    (d['username'], hash_pw(d['new_password']), session['user_id']))
    else:
        cur.execute("UPDATE users SET username=%s WHERE id=%s",
                    (d['username'], session['user_id']))
    mysql.connection.commit()
    session['username'] = d['username']
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True)

# ── Jinja2 filter ─────────────────────────────────────────────
import json as _json
@app.template_filter('from_json')
def from_json_filter(value):
    try: return _json.loads(value)
    except: return []
