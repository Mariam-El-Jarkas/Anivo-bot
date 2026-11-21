from anivo.discord_client import send_news


if __name__ == "__main__":
    send_news(
        {
            "link": "https://github.com/Mariam-El-Jarkas/Anivo-bot",
            "image_url": "",
        },
        "اختبار ناجح: رسالة DM من بوت ANIVO.",
    )
    print("Test DM sent successfully.")
