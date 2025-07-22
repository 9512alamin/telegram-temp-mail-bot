import json
import urllib.request
import time
import os

BOT_TOKEN = "7824259166:AAGzYngUNDWq_a4IDhweO_fXjph2NtZciMc"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
user_data = {}

def save_user_data():
    with open("users.json", "w") as f:
        json.dump(user_data, f)

def load_user_data():
    global user_data
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            user_data = json.load(f)

def send_message(chat_id, text, buttons=None):
    url = API_URL + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    if buttons:
        keyboard = [[{"text": b, "callback_data": b.lower()}] for b in buttons]
        payload["reply_markup"] = json.dumps({"inline_keyboard": keyboard})

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

def create_email():
    res = urllib.request.urlopen("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
    return json.loads(res.read())[0]

def get_inbox(email):
    login, domain = email.split("@")
    url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
    res = urllib.request.urlopen(url)
    return json.loads(res.read())

def delete_email(email):
    login, domain = email.split("@")
    url = f"https://www.1secmail.com/mailbox/?action=deleteMailbox&login={login}&domain={domain}"
    try:
        urllib.request.urlopen(url)
        return True
    except:
        return False

def get_stats():
    url = "https://www.1secmail.com/api/v1/?action=getDomainStats"
    try:
        res = urllib.request.urlopen(url)
        return json.loads(res.read())
    except:
        return {}

def handle_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    data = callback["data"]
    user = user_data.get(str(chat_id))

    if data == "generate email":
        email = create_email()
        user_data[str(chat_id)] = {"email": email}
        save_user_data()
        send_message(chat_id, f"✅ Your Temp Email:\n`{email}`", ["Inbox", "Delete Email", "Statistics"])

    elif data == "inbox":
        if not user:
            send_message(chat_id, "❌ First use *Generate Email*", ["Generate Email"])
            return

        inbox = get_inbox(user["email"])
        if inbox:
            for msg in inbox:
                subject = msg.get("subject", "No Subject")
                from_addr = msg.get("from", "Unknown")
                send_message(chat_id, f"📩 *Subject:* `{subject}`\n👤 *From:* `{from_addr}`")
        else:
            send_message(chat_id, "📭 Inbox is empty.")

    elif data == "delete email":
        if not user:
            send_message(chat_id, "❌ First use *Generate Email*", ["Generate Email"])
            return

        success = delete_email(user["email"])
        if success:
            del user_data[str(chat_id)]
            save_user_data()
            send_message(chat_id, "🗑️ Temp email deleted successfully.", ["Generate Email"])
        else:
            send_message(chat_id, "⚠️ Failed to delete email.")

    elif data == "statistics":
        stats = get_stats()
        if stats:
            total = stats.get("total", "N/A")
            today = stats.get("total_today", "N/A")
            domains = stats.get("domains", [])
            msg = f"📊 *Domain Stats:*\n📥 Total Emails: `{total}`\n📅 Today: `{today}`\n🟡 Domains: `{', '.join(domains)}`"
            send_message(chat_id, msg)
        else:
            send_message(chat_id, "⚠️ Couldn't fetch stats.")

def main():
    load_user_data()
    offset = 0
    while True:
        try:
            url = API_URL + f"getUpdates?timeout=100&offset={offset}"
            res = urllib.request.urlopen(url)
            updates = json.loads(res.read())

            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"].get("text", "")
                    if text == "/start":
                        send_message(chat_id, "👋 Welcome to TempMail Bot!", ["Generate Email"])
                elif "callback_query" in update:
                    handle_callback(update["callback_query"])

        except Exception as e:
            print("Error:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
