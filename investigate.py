import json
import urllib.request

from parse_data import load_items, get_unclaimed_items, save_result

MODEL = "qwen2.5:0.5b"  # 与 ollama list 显示的模型名一致


def build_prompt(description, available_items):
    """Build system and user prompts for Qwen."""

    system_prompt = """You are a campus lost-and-found assistant.

You must use ONLY the available items JSON provided by the user.
Not all details of an item must match to be a possible match.

You must return ONLY valid JSON with exactly this structure:
{ "matches": ["ITEM_ID"], "confidence": "LOW" }

Rules:
- "matches" contains all possible matching item IDs from the available items.
- "confidence" must be exactly one of: LOW, MEDIUM, HIGH.
- If there is no match, return an empty list for "matches".
- Do not include any explanation, markdown, or extra text.
"""

    user_prompt = f"""User description of lost item:
{description}

Available unclaimed items:
{json.dumps(available_items, indent=2)}

Return only JSON in the required structure.
"""

    return system_prompt, user_prompt


def ask_qwen(system_prompt, user_prompt):
    """Call Ollama HTTP API directly using urllib, no external package needed."""
    url = "http://localhost:11434/api/chat"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0},
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Ollama API request failed: {e}")


def parse_response(response_text):
    """Parse Qwen's response text into a Python dictionary."""
    text = response_text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()
    return json.loads(text)


def validate_result(result, available_items):
    """Validate structure, types, confidence value, and item IDs."""
    if not isinstance(result, dict):
        return False

    if "matches" not in result or "confidence" not in result:
        return False

    if not isinstance(result["matches"], list):
        return False

    if not isinstance(result["confidence"], str):
        return False

    if result["confidence"] not in {"LOW", "MEDIUM", "HIGH"}:
        return False

    valid_ids = {item["id"] for item in available_items}

    for match_id in result["matches"]:
        if match_id not in valid_ids:
            return False

    return True


def display_matches(result, available_items):
    """Display matches in a user-friendly format."""
    print("MATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")

    matches = result["matches"]

    if not matches:
        print("\nNo matches found.")
        print("Possible matches: []")
        return

    item_by_id = {item["id"]: item for item in available_items}

    print("\nPossible matches:")
    for item_id in matches:
        item = item_by_id.get(item_id)
        if item:
            print()
            print(f"ID: {item['id']}")
            print(f"Item: {item['item']}")
            print(f"Color: {item['color']}")
            print(f"Location: {item['location']}")
            print(f"Date found: {item['date']}")


def main():
    items = load_items("found_items.json")
    available_items = get_unclaimed_items(items)

    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)

    description = input("\nDescribe the item you lost: ").strip()

    print("\nSearching for possible matches...\n")

    system_prompt, user_prompt = build_prompt(description, available_items)
    response_text = ask_qwen(system_prompt, user_prompt)

    try:
        result = parse_response(response_text)
    except json.JSONDecodeError as e:
        print("Error: Qwen did not return valid JSON.")
        print(e)
        return

    if not validate_result(result, available_items):
        print("Error: Qwen returned an invalid result structure.")
        return

    display_matches(result, available_items)

    save_result(result, "output/match_result.json")
    print("\nResult saved to output/match_result.json")


if __name__ == "__main__":
    main()