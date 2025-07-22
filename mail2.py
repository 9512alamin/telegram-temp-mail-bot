import json
import urllib.request
import time

BOT_TOKEN = "7824259166:AAGzYngUNDWq_a4IDhweO_fXjph2NtZciMc"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
user_data = {}

def send_message(chat_id, text, buttons=None):
    url = API_URL + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if buttons:
        payload["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    headers = {"Content-Type":"application/json","User-Agent":"Mozilla/5.0"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            print("[✓] Message sent.")
    except Exception as e:
        print(f"[✗] HTTP error: {e}")

def get_updates(offset=None):
    url = API_URL + "getUpdates" + (f"?offset={offset}" if offset else "")
    try:
        with urllib.request.urlopen(url) as res:
            return json.loads(res.read())
    except:
        return {}

def handle_command(msg):
    chat = msg["chat"]["id"]
    text = msg.get("text","")
    if text == "/start":
        buttons = [
            [{"text":"📧 Generate Email","callback_data":"generate"}],
            [{"text":"📬 Inbox","callback_data":"inbox"}],
            [{"text":"🗑 Delete Email","callback_data":"delete"}],
            [{"text":"📊 Statistics","callback_data":"statistics"}],
        ]
        send_message(chat, "👋 Welcome! Choose:", buttons)

def handle_callback(cb):
    chat = cb["message"]["chat"]["id"]
    data = cb["data"]
    user = user_data.get(chat)
    if data=="generate":
        email,token = create_email()
        if email:
            user_data[chat]={"email":email,"token":token}
            send_message(chat,f"📧 Your email:\n`{email}`")
        else:
            send_message(chat,"❌ Failed to generate email.")
    # ... rest handle similarly ...

def create_email():
    url="https://api.internal.temp-mail.io/api/v3/email/new"
    data=json.dumps({"min_name_length":10,"max_name_length":10}).encode()
    headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"}
    req=urllib.request.Request(url,data=data,headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            r=json.loads(res.read())
            return r["email"],r["token"]
    except:
        return None,None

def get_inbox(email):
    url=f"https://api.internal.temp-mail.io/api/v3/email/{email}/messages"
    req=urllib.request.Request(url,headers={"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())
    except:
        return []

def main():
    last=None
    while True:
        ups=get_updates(last)
        for u in ups.get("result",[]):
            last=u["update_id"]+1
            if "message" in u: handle_command(u["message"])
            if "callback_query" in u: handle_callback(u["callback_query"])
        time.sleep(1)

if __name__=="__main__":
    main()
