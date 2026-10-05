import os
from dotenv import load_dotenv
from webscraping_ai import Client

load_dotenv()

client = Client(
    api_key=os.getenv("WEBSCRAPING_AI_API_KEY")
)

def fetch_page(url: str):
    try:
        html = client.html(
            url,
            proxy="residential"
        )

        print("Fetched HTML length:", len(html))

        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(html)

        return html

    except Exception as e:
        print(f"Error fetching webpage: {e}")
        return None


def ask_ques(url, question):
    answer = client.question(
        url,
        proxy="stealth",
        question=question
    )

    print(answer)