import os
import json
import smtplib
import requests
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time

# --- Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT")
HISTORY_FILE = "history.json"

# Configure Gemini
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

def load_history():
    """Loads the history of past topics."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] 
    return []

def save_history(topic, history):
    """Saves the new topic to the history file."""
    history.append({"date": datetime.now().strftime("%Y-%m-%d"), "topic": topic})
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def clean_json_response(text):
    """Strips markdown code blocks to ensure valid JSON."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def get_content_from_llm(past_topics):
    """
    Generates content based on a sequential Indian Finance Curriculum.
    """
    # Get the most recent topic to determine the next step
    last_topic = "None (This is the very first email)"
    if past_topics:
        last_topic = past_topics[-1]['topic']

    # We send the last 10 topics to ensure we don't loop back too soon
    recent_history_str = ", ".join([h['topic'] for h in past_topics[-10:]])
    
    prompt = f"""
    You are a Mentor for a 20-year-old student in India. You are teaching a "Zero to Hero" Finance Course via daily emails.
    
    Current State:
    - The LAST topic you taught was: "{last_topic}".
    - Recent topics covered: [{recent_history_str}].

    Your Goal:
    Determine the NEXT logical topic in the sequence. Do not skip steps. If the last topic was "Savings Accounts", the next should be "Fixed Deposits (FDs)" or "Recurring Deposits (RDs)", not "Option Trading".

    The Syllabus Roadmap (Follow this order loosely):
    1. Foundations (Inflation in India, Power of Compounding, Assets vs Liabilities)
    2. Banking Basics (Savings, FD, RD, UPI safety)
    3. Government Schemes (PPF, EPF, Sukanya Samriddhi)
    4. Insurance (Term vs Endowment, Health Insurance basics)
    5. Taxes in India (Old vs New Regime, 80C, TDS)
    6. Mutual Funds (SIPs, NAV, Equity vs Debt funds)
    7. Stock Market Basics (Nifty/Sensex, Demat accounts, IPOs)
    8. Fundamental Analysis (P/E Ratio, ROE, Reading Balance Sheets)
    9. Advanced (Technical Analysis, F&O intro).

    Constraints:
    1. Context: STRICTLY INDIAN. Use ₹ (Rupees), Lakhs/Crores. Mention Indian entities (SEBI, RBI, HDFC, Reliance).
    2. Tone: Exciting, relatable for a 20-year-old Gen Z Indian. Use analogies.
    3. Length: 800-1200 words.
    4. Output: VALID JSON ONLY.

    JSON Structure:
    {{
      "topic": "Specific Topic Name",
      "subject": "Catchy Subject Line (e.g., '🚀 Why your Savings Account is losing money')",
      "html_body": "HTML content. Use <h2>, <p>, <ul>. Use Indian examples.",
      "chart_config": {{ 
          "type": "bar", 
          "data": {{ ...Chart.js data relevant to the topic... }},
          "options": {{ ... }}
      }}
    }}
    """

    models_to_try = ['gemini-2.5-flash']

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(clean_json_response(response.text))
        except Exception:
            continue
            
    return None

def get_chart_url(chart_config):
    url = "[https://quickchart.io/chart/create](https://quickchart.io/chart/create)"
    payload = {"chart": chart_config, "width": 600, "height": 400, "backgroundColor": "white"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get('url')
    except:
        return None

def send_email(subject, html_content, to_email):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email # Setup for display
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        
        # SPLIT MULTIPLE EMAILS HERE
        recipient_list = [email.strip() for email in to_email.split(',')]
        
        server.sendmail(EMAIL_SENDER, recipient_list, text)
        server.quit()
        print(f"Email sent successfully to: {recipient_list}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise e

def main():
    history = load_history()
    content_data = get_content_from_llm(history)
    
    if not content_data:
        print("Failed to generate content.")
        exit(1)
        
    topic = content_data.get('topic', 'Finance Topic')
    chart_url = None
    if 'chart_config' in content_data:
        chart_url = get_chart_url(content_data['chart_config'])
    
    chart_html = ""
    if chart_url:
        chart_html = f'<div style="text-align:center;"><img src="{chart_url}" style="max-width:100%; border-radius:8px;"></div>'
    
    final_html = f"""
    <html>
    <body style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; line-height: 1.6; color: #333;">
        <div style="background: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h1 style="color: #d35400;">🇮🇳 Daily Finance Byte</h1>
            <p style="color: #7f8c8d; font-size: 0.9em;">{datetime.now().strftime("%d %B, %Y")}</p>
            <hr style="border: 0; border-top: 1px solid #eee;">
            {chart_html}
            {content_data.get('html_body')}
            <hr style="border: 0; border-top: 1px solid #eee;">
            <p style="font-size: 0.8em; color: #999; text-align: center;">Generated by AI for Indian Markets.</p>
        </div>
    </body>
    </html>
    """
    
    send_email(content_data.get('subject'), final_html, EMAIL_RECIPIENT)
    save_history(topic, history)

if __name__ == "__main__":
    main()
