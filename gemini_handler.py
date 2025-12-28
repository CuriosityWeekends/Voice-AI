from google import genai
from google.genai import types
from config import GEMINI_CONFIG
import re

# --------------------
# Client (NEW SDK)
# --------------------
client = genai.Client(
    api_key=GEMINI_CONFIG["api_key"]
)

# --------------------
# Tools (Google Search grounding)
# --------------------
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

tools_config = types.GenerateContentConfig(
    tools=[grounding_tool],
    temperature=GEMINI_CONFIG["temperature"],
    top_p=GEMINI_CONFIG["top_p"],
    top_k=GEMINI_CONFIG["top_k"],
)

# --------------------
# Memory
# --------------------
my_initial_question = ""
my_initial_response = ""


# ====================
# MAIN RESPONSE
# ====================
def get_response(prompt: str) -> tuple[str, str]:
    global my_initial_question, my_initial_response

    if my_initial_question:
        note = (
            f"User previously asked: {my_initial_question}. "
            f"You previously replied: {my_initial_response}. "
            f"Only use this if relevant. "
        )
    else:
        note = ""

    system_instruction = (
        GEMINI_CONFIG["system_instruction"]
        + GEMINI_CONFIG["ai_system_instruction"]
        + note
    )

    response = client.models.generate_content(
        model=GEMINI_CONFIG["model"],
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[grounding_tool],
            temperature=GEMINI_CONFIG["temperature"],
            top_p=GEMINI_CONFIG["top_p"],
            top_k=GEMINI_CONFIG["top_k"],
        ),
    )

    text = response.text or ""
    bot_reply = text.strip().splitlines()

    command = bot_reply[0] if bot_reply else ""
    reply_text = ""

    # ---- code block handling ----
    if "```" in command:
        print("Reformatting code blocks...")
        code_blocks = re.findall(
            r"```(.*?)```",
            text.replace("```python", "```").replace("```tool_code", "```"),
            re.DOTALL,
        )
        command = "; ".join(cb.strip() for cb in code_blocks)
        reply_text = re.sub(
            r"```.*?```",
            "",
            text.replace("```python", "```").replace("```tool_code", "```"),
            flags=re.DOTALL,
        ).strip()
    else:
        reply_text = "\n".join(bot_reply[1:]).strip()

    my_initial_question = prompt
    my_initial_response = reply_text

    print("🤖 Little Bot says:", reply_text)
    print("Command:", command)

    return command, reply_text


# ====================
# AI-INTERNAL CALL
# ====================
def give_get_response(note: str, prompt: str) -> tuple[str, str]:
    print("Prompt:", prompt)

    system_instruction = GEMINI_CONFIG["system_instruction"] + note

    response = client.models.generate_content(
        model=GEMINI_CONFIG["model"],
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=GEMINI_CONFIG["temperature"],
            top_p=GEMINI_CONFIG["top_p"],
            top_k=GEMINI_CONFIG["top_k"],
        ),
    )

    text = response.text or ""
    bot_reply = text.strip().splitlines()

    command = bot_reply[0] if bot_reply else ""
    reply_text = "\n".join(bot_reply[1:]).strip()

    if command.startswith("pass,"):
        reply_text = command[5:] + "\n" + reply_text
        command = "pass"

    print("🤖 Little Bot says:", reply_text)
    print("Command:", command)

    return command, reply_text
