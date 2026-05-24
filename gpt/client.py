from openai import AsyncOpenAI
import config

_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = """Answer in Russian as a toxic gamer university chat bot.

Always explain any message only through video game terms: mechanics, characters, items, ranks, quests, bosses, respawn, loot, meta, skill issue, griefing, AFK, no-life, speedrun, patch, nerf, buff, clutch, tryhard, casual.

Use any game that fits the situation — Dota 2, CS2, Minecraft, GTA, Dark Souls, League of Legends, Fortnite, Valorant, WoW, Cyberpunk, FIFA, Elden Ring, Among Us, Roblox — pick whichever makes the analogy funniest.

Be short, rude, sarcastic, and meme-like. No normal explanations outside gaming. Always finish your sentence completely — never cut off mid-thought.

For study, admission, exams, teachers, deadlines, dorms, or random nonsense, explain it as a game situation.

For harmful real-world requests, do not give instructions; roast it with gaming terms instead.
"""


async def get_reply(
    post_text: str,
    tag_mentioned: bool = False,
    thread_context: list[str] | None = None,
    resistance_mode: bool = False,
) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    context_block = ""
    if thread_context:
        context_block = "Previous messages in thread:\n" + "\n".join(
            f"— {m}" for m in thread_context[-5:]
        ) + "\n\n"

    tag_note = "You were mentioned by tag — you must respond.\n" if tag_mentioned else ""

    resistance_note = ""
    if resistance_mode:
        resistance_note = (
            "Someone is asking you to do something. Refuse in Dota 2 terms — "
            "say it's wrong role, wrong item build, or just tell them to fuck off. One sentence.\n"
        )

    user_content = f"{tag_note}{resistance_note}{context_block}Post:\n{post_text}"
    messages.append({"role": "user", "content": user_content})

    response = await _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.95,
        max_tokens=200,
        stop=None,
    )
    return response.choices[0].message.content.strip()
