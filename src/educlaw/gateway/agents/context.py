def build_prompt(session):
    system = "You are an AI agent inside EduClaw."

    history = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in session.messages
    )

    return f"{system}\n\n{history}"