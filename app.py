from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
import os, requests, datetime
from flask import send_file
from fpdf import FPDF
from docx import Document
import io

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama3-8b-8192"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get("message")
    timestamp = datetime.datetime.now().strftime("%H:%M")

    if 'messages' not in session:
        session['messages'] = [{
            "role": "system",
            "content": (
                "You are a professional AI assistant. "
                "Format all code using Markdown with triple backticks and language tags like ```python. "
                "Explain code clearly after the block."
            )
        }]

    session['messages'].append({"role": "user", "content": user_msg})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"model": MODEL, "messages": session['messages']}

    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    data = res.json()

    if "choices" not in data:
        return jsonify({"reply": f"Error: {data.get('error', data)}", "time": timestamp})

    reply = data["choices"][0]["message"]["content"]
    session['messages'].append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply, "time": timestamp})

@app.route('/clear', methods=['POST'])
def clear():
    session.pop('messages', None)
    return jsonify({"reply": "Chat history cleared."})

@app.route('/export-pdf')
def export_pdf():
    messages = session.get('messages', [])
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for msg in messages:
        prefix = "You: " if msg['role'] == 'user' else "Bot: "
        pdf.multi_cell(0, 10, prefix + msg['content'])
    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='chat.pdf', mimetype='application/pdf')

@app.route('/export-docx')
def export_docx():
    messages = session.get('messages', [])
    doc = Document()
    for msg in messages:
        prefix = "You: " if msg['role'] == 'user' else "Bot: "
        doc.add_paragraph(prefix + msg['content'])
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='chat.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

if __name__ == "__main__":
    app.run(debug=True)
