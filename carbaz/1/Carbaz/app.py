"""Interactive AI Resume and CV chatbot.."""

import json
import os

from dotenv import load_dotenv
from gradio import ChatInterface
from openai import OpenAI
from pypdf import PdfReader
from requests import post


load_dotenv(override=True)


def push(text):
    """Send a push notification using Pushover."""
    post("https://api.pushover.net/1/messages.json",
         data={"user": os.getenv("PUSHOVER_USER"),
               "token": os.getenv("PUSHOVER_TOKEN"),
               "message": text})


def record_user_details(email, name="Name not provided", notes="not provided"):
    """Record user details via a push notification."""
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    """Record an unknown question via a push notification."""
    push(f"Recording {question}")
    return {"recorded": "ok"}


# Define tool JSON schema for the "record_user_details" tool.
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being"
                   " in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation"
                " that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

# Define tool JSON schema for the "record_unknown_question" tool.
record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be"
                   " answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

# List of available tools.
tools = [{"type": "function", "function": record_user_details_json},
         {"type": "function", "function": record_unknown_question_json}]


class Me:
    """Class representing myself for the chatbot."""
    def __init__(self, name, cv_pdf_path, summary_path):
        """Initialize the Me class by loading LinkedIn profile and summary."""
        self.openai = OpenAI()
        self.name = name
        reader = PdfReader(cv_pdf_path)
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open(summary_path, "r", encoding="utf-8") as f:
            self.summary = f.read()

    def handle_tool_call(self, tool_calls):
        """Handle tool calls made by the AI model."""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool",
                            "content": json.dumps(result),
                            "tool_call_id": tool_call.id})
        return results

    def system_prompt(self):
        """Generate the system prompt for the chatbot."""
        return f"""You are acting as {self.name}.
            You are answering questions on {self.name}'s website, particularly questions
            related to {self.name}'s career, background, skills and experience.
            Your responsibility is to represent {self.name} for interactions on the
            website as faithfully as possible.
            You are given a summary of {self.name}'s background and LinkedIn profile
            which you can use to answer questions.
            Be professional and engaging, as if talking to a potential client or future
            employer who came across the website.
            If you don't know the answer to any question, use your
            "record_unknown_question" tool to record the question that you couldn't
            answer, even if it's about something trivial or unrelated to career.
            If the user is engaging in discussion, try to steer them towards getting in
            touch via email; ask for their email and record it using your
            "record_user_details" tool, but do this only once to avoid annoying the user
            or spamming me with same email several times, if user insists remind him that
            you already have their email and you'll contact them.

            ## Summary:
            {self.summary}

            ## LinkedIn Profile:
            {self.linkedin}

            With this context, please chat with the user,
            always staying in character as {self.name}.
            """

    def chat(self, message, history):
        """Handle a chat message from the user."""
        messages = [{"role": "system", "content": self.system_prompt()}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        while True:  # Loop to handle tool calls until no more are needed.
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini", messages=messages, tools=tools)
            # Check if the response includes tool calls.
            if response.choices[0].finish_reason != "tool_calls":
                break
            message = response.choices[0].message
            results = self.handle_tool_call(message.tool_calls)
            messages.append(message)
            messages.extend(results)
        return response.choices[0].message.content


if __name__ == "__main__":
    name = "Carlos Bazaga"
    cv_pdf = "me/linkedin.pdf"
    summary_txt = "me/summary.txt"
    ChatInterface(Me(name, cv_pdf, summary_txt).chat,
                  type="messages", title="Carlos Bazaga's virtual CV").launch()
