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
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT") # Comma-separated list
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
    last_topic = "None (This is the very first email)"
    if past_topics:
        last_topic = past_topics[-1]['topic']

    recent_history_str = ", ".join([h['topic'] for h in past_topics[-10:]])
    
    prompt = f"""
    You are a Mentor for a 20-year-old student in India. You are teaching a "Zero to Hero" Finance Course via daily emails.
    
    Current State:
    - The LAST topic you taught was: "{last_topic}".
    - Recent topics covered: [{recent_history_str}].

    Your Goal:
    Determine the NEXT logical topic in the sequence. Do not skip steps.

    The Syllabus Roadmap (Follow this order loosely):
    1. Foundations (Inflation in India, Power of Compounding, Assets vs Liabilities, Real vs Nominal Returns, Time Value of Money, Opportunity Cost, Budgeting, Net Worth, Emergency Fund Basics, Good Debt vs Bad Debt, Behavioural Finance Basics)
    2. Banking Basics (Savings Account, FD, RD, Sweep Accounts, NEFT/RTGS/IMPS/UPI Differences, How to Read a Bank Statement, Debit vs Credit Card, UPI Safety, Avoiding Online Frauds)
    3. Government Schemes (PPF, EPF, NPS, Sukanya Samriddhi Yojana, PMVVY, Post Office Schemes, Senior Citizen Savings Scheme, How These Schemes Help Long-Term Wealth)
    4. Insurance (Term Insurance, Endowment vs ULIP, Health Insurance Basics, Cashless vs Reimbursement, Personal Accident Insurance, Motor Insurance Basics, Why Insurance Before Investments)
    5. Taxes in India (Old vs New Regime, Tax Slabs, 80C Deductions, 80D, TDS on Salary/FD/MF, Form 16, 26AS, AIS, Capital Gains Tax on Stocks & MF, Basics of Filing ITR)
    6. Mutual Funds (SIP, NAV, Direct vs Regular Funds, Equity Funds: Large/Mid/Small-Cap, Debt Funds: Liquid/Gilt/Corporate Bond, Hybrid Funds, ELSS, Expense Ratio, Index Funds: Nifty 50/Sensex)
    7. Stock Market Basics (Nifty/Sensex, NSE/BSE, Demat + Trading Account, Brokers (Zerodha/Groww), Market vs Limit Orders, Stop-Loss, IPO Basics, Dividends, Long-Term vs Short-Term Mindset)
    8. Fundamental Analysis (P/E Ratio, P/B Ratio, ROE, ROCE, Debt-to-Equity, Operating Margin, Reading Balance Sheets, Cash Flow Statements, Income Statement Basics, Moats, Promoter Holding, Market Share)
    9. Advanced (Technical Analysis Basics, Support & Resistance, Moving Averages, Intro to Futures & Options, Why F&O is Risky, Basics of Crypto, Behavioural Biases, Credit Score & CIBIL Awareness).

    Constraints:
    1. Context: STRICTLY INDIAN. Use ₹ (Rupees), Lakhs/Crores. Mention Indian entities (SEBI, RBI, HDFC, Reliance).
    2. Tone: Exciting, relatable for a 20-year-old Gen Z Indian. Use analogies.
    3. Length: 800-1200 words.
    4. Output: VALID JSON ONLY.

    JSON Structure:
    {{
      "topic": "Specific Topic Name",
      "subject": "Catchy Subject Line",
      "html_body": "HTML content. Use <h2>, <p>, <ul>.",
      "chart_config": {{ 
          "type": "bar", 
          "data": {{ "labels": ["A","B"], "datasets": [{{ "label": "Example", "data": [10, 20] }}] }},
          "options": {{ "title": {{ "display": true, "text": "Chart Title" }} }}
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
    
    # PRIVACY CONFIGURATION:
    # 1. Set the visible 'To' header to the sender (YOU).
    #    This way, recipients see "To: me@gmail.com" instead of a giant list of strangers.
    msg['To'] = EMAIL_SENDER 
    
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        
        # 2. Actual Delivery List
        # Even though the header says "To: Sender", we tell the server 
        # to deliver it to everyone in this list. This acts as a BCC.
        recipient_list = [email.strip() for email in to_email.split(',')]
        
        server.sendmail(EMAIL_SENDER, recipient_list, text)
        server.quit()
        print(f"Email sent (BCC Mode) successfully to {len(recipient_list)} recipients.")
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
