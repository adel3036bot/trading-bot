import requests

from config import BOT_TOKEN, CHAT_ID


# ==================================================
# SEND TEXT MESSAGE
# ==================================================

def send_telegram_message(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {

        "chat_id": CHAT_ID,

        "text": message,

        "parse_mode": "HTML"

    }

    try:

        response = requests.post(

            url,

            data=data,

            timeout=20

        )

        if response.status_code == 200:

            print("✅ TELEGRAM MESSAGE SENT")

        else:

            print("❌ TELEGRAM ERROR")
            print(response.text)

    except Exception as e:

        print("❌ TELEGRAM ERROR")
        print(e)


# ==================================================
# SEND PHOTO
# ==================================================

def send_telegram_photo(photo_path, caption=""):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    try:

        with open(photo_path, "rb") as photo:

            files = {

                "photo": photo

            }

            data = {

                "chat_id": CHAT_ID,

                "caption": caption

            }

            response = requests.post(

                url,

                files=files,

                data=data,

                timeout=30

            )

        if response.status_code == 200:

            print("✅ PHOTO SENT")

        else:

            print("❌ PHOTO ERROR")
            print(response.text)

    except Exception as e:

        print("❌ PHOTO ERROR")
        print(e)


# ==================================================
# SEND DOCUMENT
# ==================================================

def send_telegram_document(file_path):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

    try:

        with open(file_path, "rb") as file:

            files = {

                "document": file

            }

            data = {

                "chat_id": CHAT_ID

            }

            response = requests.post(

                url,

                files=files,

                data=data,

                timeout=30

            )

        if response.status_code == 200:

            print("✅ DOCUMENT SENT")

        else:

            print("❌ DOCUMENT ERROR")
            print(response.text)

    except Exception as e:

        print("❌ DOCUMENT ERROR")
        print(e)


        