from planner import Planner
from llm import LLM
from memory import Memory

from tools.filesystem import FileSystem
from tools.flask import FlaskTool
from tools.terminal import Terminal
from tools.git import Git
from dotenv import load_dotenv
from google import genai

load_dotenv()  # Loads variables from .env into environment

client = genai.Client()  # Picks up GEMINI_API_KEY automatically

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Write a quick status report for my agent.",
)

print(response.text)

TOOLS = {

    "filesystem": FileSystem(),

    "flask": FlaskTool(),

    "terminal": Terminal(),

    "git": Git()

}

class AISoftwareEngineer:

    def __init__(self):

        self.memory = Memory()

        self.llm = LLM()

        self.planner = Planner(self.llm)

    def execute(self, request):

        project = self.memory.load_project()

        plan = self.planner.create_plan(request, project)

        print("\nExecution Plan\n")

        print("\nGoal:")
        print(plan["goal"])

        for step in plan["tasks"]:

            print("\nExecuting:")
            print(step["description"])

            tool = TOOLS.get(step["tool"])

            if tool:

                result = tool.run(step)

                self.memory.log(step, result)

            else:

                print("unknown tool:", step["tool"])

if __name__ == "__main__":

    engineer = AISoftwareEngineer()

    while True:
    
        request = input("nEngineer> ")

        if request.lower() == "exit":

            break

        engineer.execute(request)

        
