import json

from groq import Groq

from src.triage.context import gather_context
from src.triage.prompts import SYSTEM_PROMPT, USER_TEMPLATE


def triage(alert: dict) -> dict:
    # Client created per-call so startup doesn't fail without GROQ_API_KEY
    client = Groq()

    ctx = gather_context(alert)

    logs_section = f"Pod logs:\n{ctx['pod_logs']}\n" if ctx.get("pod_logs") else ""

    user_message = USER_TEMPLATE.format(
        alert_json=json.dumps(alert, indent=2, default=str),
        events=ctx["events"] or "(none)",
        deployments=ctx["deployments"] or "(none)",
        pdbs=ctx["pdbs"] or "(none)",
        logs_section=logs_section,
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    return {
        "alert": alert,
        "context_collected": ctx["counts"],
        "report_markdown": response.choices[0].message.content,
    }
