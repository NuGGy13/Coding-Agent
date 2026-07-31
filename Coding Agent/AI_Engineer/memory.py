import json
import os

class Memory:

    FILE = "memory.json"

    def load_project(self):

        if os.path.exists(self.FILE):

            with open(self.FILE, "r") as f:

                return json.load(f)

        return{}

    def save_project(self, project):

        with open(self.FILE, "w") as f:

            json.dump(project, f, indent=4)

    def log(self, step, result):

        print(f"LOGGED: {step['description']}")                    