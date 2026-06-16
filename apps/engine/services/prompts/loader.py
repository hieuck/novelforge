from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

logger = logging.getLogger("novelforge.prompts")

_BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent / "packages" / "prompts"


def _read(filename: str, fallback: str) -> str:
    # Try repo packages/prompts first, then engine-relative prompts.
    candidates = [_BASE_DIR / filename, Path(__file__).resolve().parent.parent / "prompts" / filename]
    for path in candidates:
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except OSError:
                continue
    return fallback


def load_prompt(name: str) -> str:
    if name == "system_base.txt":
        return _read(name, "Bạn là trợ lý viết tiểu thuyết.")
    if name == "writing_assistant.txt":
        return _read(
            name,
            "Bạn chuyên hỗ trợ tiểu thuyết: viết, chỉnh sửa, tóm tắt, duy trì nhất quán, giữ văn phong.",
        )
    if name == "actions/continue.txt":
        return _read(name, "Tiếp tục đoạn văn bản hiện tại một cách mượt mà và phù hợp.")
    if name == "actions/rewrite.txt":
        return _read(name, "Viết lại đoạn văn, giữ nguyên ý, cải thiện ngôn từ.")
    if name == "actions/expand.txt":
        return _read(name, "Mở rộng chi tiết bối cảnh và cảm xúc.")
    if name == "actions/shorten.txt":
        return _read(name, "Rút gọn nhưng giữ nguyên thông tin chính.")
    if name == "actions/improve_dialogue.txt":
        return _read(name, "Cải thiện hội thoại tự nhiên.")
    if name == "actions/make_emotional.txt":
        return _read(name, "Tăng cường cảm xúc cho văn bản.")
    if name == "actions/make_cinematic.txt":
        return _read(name, "Tăng tính điện ảnh: hình ảnh, âm thanh, chuyển động.")
    if name == "actions/fix_grammar.txt":
        return _read(name, "Sửa ngữ pháp, dấu câu, chính tả.")
    if name == "actions/summarize_chapter.txt":
        return _read(name, "Tóm tắt chương thành 1-2 đoạn ngắn.")
    if name == "actions/summarize_project.txt":
        return _read(name, "Tóm tắt toàn bộ project.")
    if name == "actions/continuity.txt":
        return _read(name, "Kiểm tra lỗi nhất quán cốt truyện.")
    if name == "actions/plot_holes.txt":
        return _read(name, "Tìm plot hole và đề xuất cách khắc phục.")
    if name == "actions/suggest_scene.txt":
        return _read(name, "Gợi ý 3 cảnh tiếp theo.")
    if name == "actions/generate_character.txt":
        return _read(name, "Sinh hồ sơ nhân vật chi tiết.")
    if name == "actions/generate_world.txt":
        return _read(name, "Sinh lore/worldbuilding chi tiết.")
    if name == "actions/translate_vi_en.txt":
        return _read(name, "Dịch tiếng Việt sang tiếng Anh, giữ văn phong.")
    if name == "actions/translate_en_vi.txt":
        return _read(name, "Dịch tiếng Anh sang tiếng Việt, giữ văn phong.")
    if name == "actions/premise.txt":
        return _read(name, "Sinh concept truyện hấp dẫn.")
    if name == "actions/outline.txt":
        return _read(name, "Sinh dàn ý cấu trúc rõ ràng.")
    logger.warning("Missing prompt %s", name)
    return ""
