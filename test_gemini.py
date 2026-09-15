# ==================================================
# IMPORTS
# ==================================================

from google import genai
from config import GEMINI_API_KEY


# ==================================================
# CREATE CLIENT
# ==================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ==================================================
# PROMPT
# ==================================================

prompt = """
Translate this financial news into professional Arabic.

Rules:
- Translate only.
- Do not add information.
- Do not remove information.
- Keep company names and stock symbols in English.
- Use professional financial Arabic.

News:
Federal Reserve leaves interest rates unchanged while signaling that inflation remains elevated.
"""


# ==================================================
# REQUEST
# ==================================================

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=prompt,
)


# ==================================================
# RESULT
# ==================================================

print("\n==============================")
print("ADEL SMART BOT")
print("==============================\n")

print(response.text)

