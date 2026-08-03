import json

class Planner:

    def __init__(self, llm):
        self.llm = llm

    def create_plan(self, request, project):

        prompt = f"""
you are an expert software engineer.

Your job is to create a development plan.

Project informoation:
{project}

User request:
{request}

Return ONLY vavlid JSON.

The JSON format must be:

{{
    "goal": "short description",
    "tasks": [
        {{
            "tool": "tool name",
            "action": "action name",
            "description": "what needs to happen"
        }}
    ]
}}

Availible tools:

filesystem
flask
terminal
git

Do not include markdown.
Do not include explanations.
"""

        response = self.llm.ask(prompt)

        try:

            plan = json.loads(response)

            return plan

        except json.JSONDecodeError:

            print("Gemini returned invalid JSON")
            print(response)

            return {
                "goal": "Unable to create plan",
                "tasks": []
            }
        