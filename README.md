# AI Study Buddy — Hackathon Project

**Stack:** HTML · CSS (custom) · Tailwind-inspired · Flask · MySQL · Claude AI

---

## Project Structure
```
ai_study_buddy/
├── app.py                  ← Flask backend (all routes)
├── schema.sql              ← MySQL database schema + admin seed
├── requirements.txt
├── static/
│   ├── css/main.css        ← Full design system (dark + light mode)
│   └── js/main.js          ← Theme toggle, toasts, helpers
└── templates/
    ├── base.html           ← Shared sidebar layout
    ├── login.html          ← Login (role-aware tabs)
    ├── register.html       ← Student registration
    ├── dashboard.html      ← User home
    ├── admin_dashboard.html← Admin panel
    ├── notes.html          ← AI note summarizer
    ├── quiz.html           ← AI quiz generator
    └── profile.html        ← Account settings
```

---

## Setup (5 steps)

### 1. Create & seed the database
```bash
mysql -u user -p passkey < schema.sql
```

### 2. Install Python packages
```bash
pip install -r requirements.txt
```

### 3. Set your Anthropic API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Run the app
```bash
python app.py
```
Visit → http://localhost:5000

---

## 🔐 Role-Based Access

| Role  | Access                                      | Default credentials                |
|-------|---------------------------------------------|------------------------------------|
| Admin | Admin dashboard, manage/disable/delete users| admin@studybuddy.com / Admin@123   |
| User  | Dashboard, notes, quizzes, profile          | Register at /register              |

> ⚠️ Change the admin password immediately after first login!

---

## 🌙 Dark / Light Mode
- Toggle button in every page's top-right corner
- Preference saved to `localStorage` — persists across sessions
- Zero flash on page load (theme applied before render via inline script)

---

## ✨ Features

### Student
- **AI Note Summarizer** — paste raw notes → Claude returns clean bullet-point summary
- **AI Quiz Generator** — choose topic, count (3/5/10), difficulty (easy/medium/hard)
- **Instant scoring** — submit quiz, see correct/wrong answers with explanations
- **Progress stats** — note count, quiz count, average score on dashboard

### Admin
- **Overview stats** — total users, notes, quizzes, attempts
- **User management** — search, enable/disable, delete students
- **Activity feed** — recent quiz sessions with scores

---

## 🎨 Design Highlights
- Custom CSS design system — no Tailwind CDN dependency
- CSS variables for instant theme switching
- Persistent sidebar with role badge
- Score ring animation on quiz completion
- Toast notifications
- Responsive tables with hover states
