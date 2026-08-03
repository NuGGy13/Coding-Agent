from providers import GeminiProvider


class LLM:

    def __init__(self):
        self.provider = GeminiProvider()

    def ask(self, prompt):

        print("\nThinking...\n")

        return self.provider.chat(prompt)