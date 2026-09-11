import os
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, abort

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

# Single source of truth for every template: its display name and which
# structural layout it uses. Add a new template by adding one line here —
# everything else (homepage cards, routes, previews) is generated from it.
TEMPLATES = {
    'modern':       {'label': 'Modern',       'layout': 'sidebar'},
    'creative':     {'label': 'Creative',     'layout': 'sidebar'},
    'professional': {'label': 'Professional', 'layout': 'centered'},
    'corporate':    {'label': 'Corporate',    'layout': 'centered'},
    'minimal':      {'label': 'Minimal',      'layout': 'minimal'},
    'student':      {'label': 'Student',      'layout': 'minimal'},
}

FIELDS = ['fullname', 'email', 'phone', 'location', 'linkedin', 'summary',
          'education', 'skills', 'projects', 'experience', 'certifications']


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(f'''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template TEXT NOT NULL,
            {", ".join(f + " TEXT" for f in FIELDS)},
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def row_to_data(row):
    data = {f: (row[f] or '') for f in FIELDS}
    data['skills_list'] = [s.strip() for s in data['skills'].split(',') if s.strip()]
    return data


@app.route('/')
def home():
    return render_template('index.html', templates=TEMPLATES)


@app.route('/preview-template/<template_name>')
def preview_template(template_name):
    if template_name not in TEMPLATES:
        abort(404)
    image_path = url_for('static', filename=f'images/{template_name}-template.png')
    return render_template(
        'template-preview.html',
        template_name=template_name,
        label=TEMPLATES[template_name]['label'],
        image_path=image_path,
    )


@app.route('/form/<template_name>')
def form(template_name):
    if template_name not in TEMPLATES:
        abort(404)

    resume = None
    resume_id = request.args.get('id')
    if resume_id:
        conn = get_db()
        row = conn.execute('SELECT * FROM resumes WHERE id=?', (resume_id,)).fetchone()
        conn.close()
        if row:
            resume = dict(row)

    return render_template(
        'form.html',
        template_name=template_name,
        label=TEMPLATES[template_name]['label'],
        layout=TEMPLATES[template_name]['layout'],
        resume=resume,
        resume_id=resume_id,
    )


@app.route('/generate/<template_name>', methods=['POST'])
def generate_resume(template_name):
    if template_name not in TEMPLATES:
        abort(404)

    values = {f: request.form.get(f, '').strip() for f in FIELDS}
    resume_id = request.form.get('resume_id')
    now = datetime.utcnow().isoformat()

    conn = get_db()
    if resume_id:
        set_clause = ", ".join(f"{f}=?" for f in FIELDS)
        conn.execute(
            f'UPDATE resumes SET template=?, {set_clause}, updated_at=? WHERE id=?',
            (template_name, *values.values(), now, resume_id),
        )
        conn.commit()
        rid = int(resume_id)
    else:
        cols = ", ".join(FIELDS)
        placeholders = ", ".join(["?"] * len(FIELDS))
        cur = conn.execute(
            f'INSERT INTO resumes (template, {cols}, created_at, updated_at) '
            f'VALUES (?, {placeholders}, ?, ?)',
            (template_name, *values.values(), now, now),
        )
        conn.commit()
        rid = cur.lastrowid
    conn.close()

    data = {**values, 'skills_list': [s.strip() for s in values['skills'].split(',') if s.strip()]}

    return render_template(
        'resume.html',
        data=data,
        theme=template_name,
        layout=TEMPLATES[template_name]['layout'],
        template_name=template_name,
        label=TEMPLATES[template_name]['label'],
        resume_id=rid,
    )


@app.route('/resumes')
def resumes():
    conn = get_db()
    rows = conn.execute('SELECT * FROM resumes ORDER BY updated_at DESC').fetchall()
    conn.close()
    return render_template('resumes.html', resumes=rows, templates=TEMPLATES)


@app.route('/resume/<int:resume_id>')
def view_resume(resume_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM resumes WHERE id=?', (resume_id,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    template_name = row['template']
    return render_template(
        'resume.html',
        data=row_to_data(row),
        theme=template_name,
        layout=TEMPLATES[template_name]['layout'],
        template_name=template_name,
        label=TEMPLATES[template_name]['label'],
        resume_id=resume_id,
    )


@app.route('/delete/<int:resume_id>', methods=['POST'])
def delete_resume(resume_id):
    conn = get_db()
    conn.execute('DELETE FROM resumes WHERE id=?', (resume_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('resumes'))


init_db()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)