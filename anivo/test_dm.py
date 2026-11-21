import os
from anivo.discord_client import send_dm

def main():
    if not os.getenv("DISCORD_BOT_TOKEN") or not os.getenv("DISCORD_USER_ID"):
        raise SystemExit("Missing DISCORD_BOT_TOKEN or DISCORD_USER_ID.")
    send_dm("🌸 ANIVO || انيفو\n\nتم الاتصال بنجاح! هذه رسالة اختبار من ANIVO.")
    print("Test DM sent successfully.")

if __name__ == "__main__":
    main()
