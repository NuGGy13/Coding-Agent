from google import genai
from config import Config


class GeminiProvider:

    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)

    def chat(self, prompt):

        response = self.client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=prompt
        )

        return response.text