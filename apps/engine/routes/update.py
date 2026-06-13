from fastapi import APIRouter
from pydantic import BaseModel
import os
import subprocess
from pathlib import Path
from typing import Optional

router = APIRouter()


class UpdateCheckResponse(BaseModel):
    update_available: bool
    new_commits: int = 0
    current_commit: Optional[str] = None
    latest_commit: Optional[str] = None
    error: Optional[str] = None


class UpdateApplyResponse(BaseModel):
    success: bool
    message: str
    details: Optional[str] = None


NOVELFORGE_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def run_git(args: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(NOVELFORGE_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as exc:
        return 1, "", str(exc)


@router.get("/update/check", response_model=UpdateCheckResponse)
async def check_update() -> UpdateCheckResponse:
    remote = os.environ.get("NOVELFORGE_REMOTE", "https://github.com/hieuck/novelforge.git")
    branch = os.environ.get("NOVELFORGE_BRANCH", "master")

    code, out, err = run_git(["fetch", "--quiet", remote, branch])
    if code != 0:
        return UpdateCheckResponse(update_available=False, error=err or out or "Fetch failed")

    code, out, _ = run_git(["rev-parse", "HEAD"])
    if code != 0:
        return UpdateCheckResponse(update_available=False, error="Unable to resolve current commit")
    current_commit = out

    code, out, _ = run_git(["rev-parse", f"origin/{branch}"])
    if code != 0:
        return UpdateCheckResponse(update_available=False, error="Unable to resolve remote commit")
    latest_commit = out

    code, out, _ = run_git(["rev-list", f"HEAD..origin/{branch}", "--count"])
    if code != 0:
        return UpdateCheckResponse(update_available=False, error="Unable to count commits")
    new_commits = int(out.strip() or "0")

    return UpdateCheckResponse(
        update_available=new_commits > 0,
        new_commits=new_commits,
        current_commit=current_commit,
        latest_commit=latest_commit,
    )


@router.post("/update/apply", response_model=UpdateApplyResponse)
async def apply_update() -> UpdateApplyResponse:
    branch = os.environ.get("NOVELFORGE_BRANCH", "master")
    remote = os.environ.get("NOVELFORGE_REMOTE", "https://github.com/hieuck/novelforge.git")

    code, out, err = run_git(["status", "--porcelain"])
    if code != 0:
        return UpdateApplyResponse(success=False, message="Unable to read git status", details=err or out)
    if out:
        return UpdateApplyResponse(success=False, message="Working tree is dirty", details=out)

    code, out, err = run_git(["pull", "--ff-only", remote, branch])
    if code != 0:
        code, out, err = run_git(["reset", "--hard", f"origin/{branch}"])
        if code != 0:
            return UpdateApplyResponse(success=False, message="Update failed", details=err or out)

    code, out, err = run_git(["rev-parse", "HEAD"])
    applied_commit = out if code == 0 else "unknown"

    return UpdateApplyResponse(
        success=True,
        message="Update applied. Please restart NovelForge.",
        details=applied_commit,
    )
