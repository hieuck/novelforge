from services.ai_service import AIEngine


async def run_ai(
    *,
    project_id: str | None,
    action: str,
    text: str | None,
    instruction: str | None,
    chapter_id: str | None,
    history: list[dict] | None = None,
) -> dict[str, str]:
    engine = AIEngine(project_id=project_id)
    await engine.prepare()
    return {
        "result": await engine.run(
            action=action,
            text=text,
            instruction=instruction,
            chapter_id=chapter_id,
            history=history,
        ),
        "action": action,
    }
