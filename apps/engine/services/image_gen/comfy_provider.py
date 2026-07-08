"""Local ComfyUI provider for image generation.

Connects to a running ComfyUI instance at a configurable URL.
ComfyUI workflow must expose a text-to-image API endpoint.
"""

from __future__ import annotations

import json
import logging

from httpx import AsyncClient, Timeout

from .base import ImageGenProvider

logger = logging.getLogger("novelforge.image_gen.comfy")


class ComfyUIProvider(ImageGenProvider):
    """Generate images via a local ComfyUI API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8188", workflow: dict | None = None):
        self.base_url = base_url.rstrip("/")
        self.workflow = workflow or self._default_workflow()

    def _default_workflow(self) -> dict:
        """Minimal workflow: text prompt → empty latent → KSampler → save image."""
        return {
            "prompt": {
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": 42,
                        "steps": 20,
                        "cfg": 7,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1,
                        "model": ["4", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0],
                    },
                },
                "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}},
                "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
                "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "prompt_here", "clip": ["4", 1]}},
                "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 1]}},
                "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
                "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "novelforge", "images": ["8", 0]}},
            }
        }

    async def generate(self, prompt: str, size: str = "1024x1024") -> tuple[bytes, str]:
        w, h = (int(x) for x in size.split("x"))
        workflow = json.dumps(self.workflow).replace("prompt_here", prompt.replace('"', "'"))
        workflow = workflow.replace('"width": 1024, "height": 1024', f'"width": {w}, "height": {h}')

        payload = {"prompt": json.loads(workflow)}

        async with AsyncClient() as client:
            # Submit workflow
            resp = await client.post(
                f"{self.base_url}/prompt",
                json=payload,
                timeout=Timeout(connect=5.0, read=5.0),
            )
            resp.raise_for_status()
            job_id = resp.json().get("prompt_id", "")

            # Poll for completion
            import asyncio

            for _ in range(120):
                await asyncio.sleep(1)
                status_resp = await client.get(f"{self.base_url}/history/{job_id}", timeout=5.0)
                if status_resp.status_code == 200:
                    history = status_resp.json()
                    if job_id in history:
                        outputs = history[job_id].get("outputs", {})
                        for node_id, node_output in outputs.items():
                            images = node_output.get("images", [])
                            if images:
                                img_data = images[0]
                                img_resp = await client.get(
                                    f"{self.base_url}/view?filename={img_data['filename']}&subfolder={img_data.get('subfolder', '')}",
                                    timeout=30.0,
                                )
                                img_resp.raise_for_status()
                                return img_resp.content, f"image/{img_data.get('type', 'png')}"
                    break

        raise TimeoutError("ComfyUI image generation timed out")
