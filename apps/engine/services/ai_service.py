from __future__ import annotations

import logging
from typing import AsyncGenerator

from db.session import SessionLocal
from models.extra import AppSettings
from models.summary import Summary as SummaryCache
from services.context.builder import ProjectContext
from services.prompts.loader import load_prompt
from services.providers.openai_compat import build_client
from services.providers.base import ProviderSettings

logger = logging.getLogger("novelforge.ai")


async def _get_settings() -> ProviderSettings:
    db = SessionLocal()
    try:
        row = db.query(AppSettings).filter(AppSettings.active == True).first()
        if not row:
            return ProviderSettings()
        return ProviderSettings(
            provider=row.provider,
            base_url=row.base_url,
            api_key=row.api_key,
            model=row.model,
            temperature=row.temperature,
            max_tokens=row.max_tokens,
        )
    finally:
        db.close()


def _build_system_prompt(
    action: str,
    character_context: str,
    lore_context: str,
    timeline_context: str,
    style_context: str,
) -> str:
    base = load_prompt("system_base.txt")
    writing = load_prompt("writing_assistant.txt")
    action_block = load_prompt(f"actions/{action}.txt")
    extras: list[str] = []
    if character_context.strip():
        extras.append(f"Character Bible:\n{character_context}")
    if lore_context.strip():
        extras.append(f"World Lore:\n{lore_context}")
    if timeline_context.strip():
        extras.append(f"Timeline:\n{timeline_context}")
    if style_context.strip():
        extras.append(f"Style guide:\n{style_context}")
    return "\n\n".join([base, writing, action_block or "", "\n\n".join(extras)])


async def _inject_summaries(system_prompt: str, project_id: str) -> str:
    if not project_id:
        return system_prompt
    db = SessionLocal()
    try:
        summaries = (
            db.query(SummaryCache)
            .filter(SummaryCache.project_id == project_id)
            .all()
        )
    finally:
        db.close()
    if not summaries:
        return system_prompt
    summary_blocks = [f"[{s.kind}] {s.text}" for s in summaries]
    return system_prompt + "\n\nProject summaries:\n" + "\n\n".join(summary_blocks)


class AIEngine:
    def __init__(self, project_id: str | None = None) -> None:
        self.project_id = project_id
        self.context = ProjectContext(project_id)

    async def prepare(self) -> None:
        await self.context.load()

    async def run(
        self,
        action: str,
        text: str | None,
        instruction: str | None,
        chapter_id: str | None,
        history: list[dict] | None = None,
    ) -> str:
        settings = await _get_settings()
        client = build_client(settings)
        system_prompt = _build_system_prompt(
            action=action,
            character_context=self.context.character_context(),
            lore_context=self.context.lore_context(),
            timeline_context=self.context.timeline_context(),
            style_context=self.context.style_context(),
        )
        system_prompt = await _inject_summaries(system_prompt, self.project_id or "")

        chapter_context = ""
        if action not in {"premise", "outline", "world"}:
            chapter_context = self.context.chapter_context(chapter_id)

        user_prompt = _build_user_prompt(
            action, text or "", instruction or "", chapter_context
        )

        logger.info(
            "AI request action=%s provider=%s model=%s",
            action,
            settings.provider,
            settings.model,
        )

        # Build messages list for multi-turn support
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        if history:
            # Include prior turns (up to last 10 messages to keep context bounded)
            for msg in history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in {"user", "assistant"} and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_prompt})

        return await client.chat_messages(messages)

    async def stream(
        self,
        action: str,
        text: str | None,
        instruction: str | None,
        chapter_id: str | None,
        history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream AI output token by token."""
        settings = await _get_settings()
        client = build_client(settings)
        system_prompt = _build_system_prompt(
            action=action,
            character_context=self.context.character_context(),
            lore_context=self.context.lore_context(),
            timeline_context=self.context.timeline_context(),
            style_context=self.context.style_context(),
        )
        system_prompt = await _inject_summaries(system_prompt, self.project_id or "")

        chapter_context = ""
        if action not in {"premise", "outline", "world"}:
            chapter_context = self.context.chapter_context(chapter_id)

        user_prompt = _build_user_prompt(
            action, text or "", instruction or "", chapter_context
        )

        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in {"user", "assistant"} and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_prompt})

        async for chunk in client.chat_stream(messages):
            yield chunk


def _build_user_prompt(
    action: str,
    text: str,
    instruction: str,
    chapter_context: str,
) -> str:
    prefix_map: dict[str, str] = {
        "continue":         "Tiếp tục viết nội dung dựa trên đoạn hiện tại. Giữ văn phong, không lặp lại câu mở đầu.",
        "rewrite":          "Viết lại đoạn sau cho rõ ràng, mượt mà hơn, giữ nguyên ý.",
        "expand":           "Phát triển thêm chi tiết cho đoạn sau, làm phong phú bối cảnh, cảm xúc, và hành động.",
        "shorten":          "Rút gọn đoạn sau mà giữ nguyên thông tin chính.",
        "dialogue":         "Cải thiện hội thoại cho tự nhiên, có sắc thái, và vẫn phù hợp nhân vật.",
        "emotional":        "Làm văn bản sau giàu cảm xúc hơn, sâu sắc hơn.",
        "cinematic":        "Làm văn bản sau mang tính điện ảnh hơn: hình ảnh, âm thanh, góc quay.",
        "grammar":          "Sửa ngữ pháp, dấu câu, lỗi chính tả, giữ nguyên ý.",
        "fix_pacing":       "Cải thiện nhịp độ: tăng tốc đoạn chậm, thêm nhịp thở vào đoạn dày đặc.",
        "add_sensory":      "Thêm chi tiết giác quan: mùi, âm thanh, kết cấu, màu sắc.",
        "tension_build":    "Tăng căng thẳng và kịch tính. Thêm foreshadowing, uncertainty.",
        "perspective_shift":"Viết lại từ góc nhìn khác hoặc thay đổi POV.",
        "summarize_chapter":"Tóm tắt chương hiện tại thành 1-2 đoạn ngắn, nhấn mạnh sự kiện quan trọng.",
        "summarize_project":"Tóm tắt toàn bộ project thành tổng quan cốt truyện, mâu thuẫn, và hướng đi.",
        "continuity":       "Kiểm tra lỗi nhất quán và mạch plot: thời gian, hành động nhân vật, địa điểm, lore.",
        "plot_holes":       "Liệt kê plot hole tiềm ẩn, vết nứt logic, đề xuất cách vá.",
        "next_scene":       "Đề xuất 3 ý cảnh tiếp theo phù hợp với chương hiện tại.",
        "character":        "Sinh hồ sơ nhân vật dựa trên yêu cầu.",
        "world":            "Sinh thông tin lore/worldbuilding dựa trên yêu cầu.",
        "translate_vi_en":  "Dịch sang tiếng Anh, giữ văn phong văn học.",
        "translate_en_vi":  "Dịch sang tiếng Việt, giữ văn phong văn học.",
        "premise":          "Sinh concept câu chuyện hấp dẫn.",
        "outline":          "Sinh dàn ý cấu trúc truyện rõ ràng.",
    }
    action_text = prefix_map.get(action, "Hỗ trợ viết tiểu thuyết.")
    parts = [action_text]
    if chapter_context.strip():
        parts.append(f"Context:\n{chapter_context[:4000]}")
    if text.strip():
        parts.append(f"Input:\n{text}")
    if instruction.strip():
        parts.append(f"Instruction:\n{instruction}")
    if action in {"premise", "outline", "world", "character"}:
        parts.append("Trả về nội dung ngắn gọn, rõ ràng, dễ dùng ngay.")
    return "\n\n".join(parts)
