import os
import json
import smtplib
import requests
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

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
    """Loads the history of past topics to prevent duplicates."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Warning: history.json was corrupted. Starting fresh.")
                return [] 
    return []

def save_history(topic, history):
    """Saves the new topic to the history file."""
    history.append({"date": datetime.now().strftime("%Y-%m-%d"), "topic": topic})
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def clean_json_response(text):
    """
    Crucial Fix: LLMs often wrap JSON in Markdown code blocks (```json ... ```).
    This function strips those out to ensure valid JSON parsing.
    """
    text = text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
    
    return text.strip()

def get_content_from_llm(past_topics):
    """
    Generates the content. Uses gemini-2.5-flash for speed and free-tier allowance.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # We send only the last 30 topics to keep the prompt size efficient
    past_topics_str = ", ".join([h['topic'] for h in past_topics[-30:]])
    
    prompt = f"""
    You are a financial educator. Write a daily email teaching one specific beginner finance concept.
    
    Constraint Checklist:
    1. Topic must be UNIQUE and NOT in this list: [{past_topics_str}].
    2. Length: 800-1200 words.
    3. Tone: Beginner-friendly, encouraging.
    4. Output: VALID JSON ONLY. No preamble.
    
    JSON Structure required:
    {{
      "topic": "Short Topic Name",
      "subject": "Catchy Email Subject",
      "html_body": "The full article in HTML format (use <h2>, <p>, <ul>, <li>). Do not use <html> or <body> tags. Style with inline CSS.",
      "chart_config": {{ 
          "type": "bar", 
          "data": {{ "labels": ["A","B"], "datasets": [{{ "label": "Example", "data": [10, 20] }}] }},
          "options": {{ "title": {{ "display": true, "text": "Chart Title" }} }}
      }}
    }}
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        cleaned_text = clean_json_response(response.text)
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Error generating content from Gemini: {e}")
        return None

def get_chart_url(chart_config):
    """
    Generates a chart image URL using QuickChart.io.
    """
    url = "[https://quickchart.io/chart/create](https://quickchart.io/chart/create)"
    payload = {
        "chart": chart_config,
        "width": 600,
        "height": 400,
        "backgroundColor": "white",
        "format": "png"
    }
    
    try:
        # We use a POST request to handle large config objects
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get('url')
    except Exception as e:
        print(f"Error generating chart: {e}")
        return None # Return None so email sends without chart rather than failing

def send_email(subject, html_content, to_email):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        
        # Handle multiple recipients if comma-separated
        recipients = to_email.split(',')
        server.sendmail(EMAIL_SENDER, recipients, text)
        
        server.quit()
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise e

def main():
    print(f"--- Starting Daily Finance Mailer at {datetime.now()} ---")
    
    # 1. Load History
    history = load_history()
    
    # 2. Generate Content
    print("Querying Gemini...")
    content_data = get_content_from_llm(history)
    
    if not content_data:
        print("Failed to generate content. Exiting.")
        exit(1) # Exit with error code so GitHub Actions marks it as failed
        
    topic = content_data.get('topic', 'Finance Topic')
    print(f"Generated Topic: {topic}")
    
    # 3. Generate Chart URL (Safe Mode)
    print("Generating Chart...")
    chart_url = None
    if 'chart_config' in content_data:
        chart_url = get_chart_url(content_data['chart_config'])
    
    # 4. Assemble HTML
    chart_html = ""
    if chart_url:
        chart_html = f"""
        <div style="margin: 20px 0; text-align: center;">
            <img src="{chart_url}" alt="{topic} Chart" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px;">
        </div>
        """
    
    final_html = f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #ffffff; padding: 20px; border: 1px solid #e1e1e1; border-radius: 8px;">
            <div style="border-bottom: 2px solid #4CAF50; padding-bottom: 10px; margin-bottom: 20px;">
                <h1 style="color: #2E7D32; margin: 0; font-size: 24px;">📈 Daily Finance Byte</h1>
                <p style="color: #666; font-size: 14px; margin: 5px 0 0 0;">{datetime.now().strftime("%B %d, %Y")}</p>
            </div>
            
            {chart_html}
            
            <div style="font-size: 16px;">
                {content_data.get('html_body', '<p>Error: No body content generated.</p>')}
            </div>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="font-size: 12px; color: #999; text-align: center;">
                Automated by Gemini & GitHub Actions
            </p>
        </div>
    </body>
    </html>
    """
    
    # 5. Send Email
    print("Sending Email...")
    send_email(content_data.get('subject', f"Daily Finance: {topic}"), final_html, EMAIL_RECIPIENT)
    
    # 6. Save History
    save_history(topic, history)
    print("Success. Workflow completed.")

if __name__ == "__main__":

    main()
