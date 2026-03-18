import streamlit as st
import os
import re
import time
import tempfile
import textwrap
import io
import base64
import json
import shutil
import struct
import wave
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

PROJECTS_DIR = Path(__file__).parent / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

DEFAULT_NARRATION = {
    "voice_id": "",
    "voice_name": "",
    "text": "",
    "tags": "",
    "audio_generated": False,
}

# ElevenLabs default/public voices (work with any API key)
ELEVENLABS_DEFAULT_VOICES = [
    {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel - Calm, Narration"},
    {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi - Energetic, Upbeat"},
    {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella - Soft, Storytelling"},
    {"voice_id": "ErXwobaYiN019PkySvjV", "name": "Antoni - Warm, Cinematic"},
    {"voice_id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli - Young, Expressive"},
    {"voice_id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh - Deep, Documentary"},
    {"voice_id": "VR6AewLTigWG4xSOukaG", "name": "Arnold - Bold, Dramatic"},
    {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam - Deep, Professional"},
    {"voice_id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam - Neutral, Conversational"},
    {"voice_id": "jBpfuIE2acCO8z3wKNLl", "name": "Gigi - Lively, Social Media"},
]

MOCK_VOICES = [
    {"voice_id": "mock_rachel", "name": "Rachel - Calm (Mock)"},
    {"voice_id": "mock_josh", "name": "Josh - Deep (Mock)"},
    {"voice_id": "mock_bella", "name": "Bella - Soft (Mock)"},
]


# ---------------------------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp { font-family: 'Inter', sans-serif; }

/* ── Hero ───────────────────────────────────────────────── */
.hero-header {
    text-align: center;
    padding: 1.2rem 0 0.6rem;
}
.hero-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.hero-header p {
    color: #94a3b8;
    font-size: 0.95rem;
    font-weight: 300;
}

/* ── Project bar ────────────────────────────────────────── */
.project-bar {
    background: linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08));
    border: 1px solid rgba(102,126,234,0.2);
    border-radius: 12px;
    padding: 0.7rem 1.1rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.8rem;
    flex-wrap: wrap;
}
.project-bar .project-name { font-weight: 600; font-size: 1.05rem; color: #e2e8f0; }
.project-bar .project-meta { color: #94a3b8; font-size: 0.8rem; }

/* ── Status badges ──────────────────────────────────────── */
.status-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.status-new { background: #1e293b; color: #94a3b8; border: 1px solid #334155; }
.status-completed { background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.status-processing { background: rgba(234,179,8,0.12); color: #facc15; border: 1px solid rgba(234,179,8,0.3); }

/* ── Full script display ────────────────────────────────── */
.full-script {
    background: rgba(102,126,234,0.05);
    border: 1px solid rgba(102,126,234,0.15);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin-bottom: 1rem;
    font-size: 0.82rem;
    color: #94a3b8;
    font-style: italic;
    line-height: 1.5;
}
.full-script strong { color: #a5b4fc; font-style: normal; }

/* ── Scene card ─────────────────────────────────────────── */
.scene-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-left: 3px solid #667eea;
    border-radius: 0 12px 12px 0;
    padding: 1rem 1.2rem;
    margin-bottom: 1.2rem;
}
.scene-card-header {
    font-size: 1rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 0.8rem;
    line-height: 1.4;
}
.scene-card-header .scene-num {
    display: inline-block;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 6px;
    margin-right: 0.6rem;
}

/* ── Prompt labels ──────────────────────────────────────── */
.prompt-label {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 0.3rem;
}
.prompt-label-image { background: rgba(167,139,250,0.15); color: #a78bfa; border: 1px solid rgba(167,139,250,0.3); }
.prompt-label-video { background: rgba(52,211,153,0.12); color: #34d399; border: 1px solid rgba(52,211,153,0.25); }

/* ── No image placeholder ───────────────────────────────── */
.no-image-placeholder {
    background: #1e293b;
    border: 1px dashed #334155;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 180px;
    color: #475569;
    font-size: 0.85rem;
    font-weight: 500;
}

/* ── Narration section ──────────────────────────────────── */
.narration-section {
    background: rgba(102,126,234,0.04);
    border: 1px solid rgba(102,126,234,0.15);
    border-radius: 12px;
    padding: 0.8rem 1rem;
    margin-bottom: 1rem;
}
.narration-header {
    font-size: 0.85rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 0.5rem;
}
.speaker-tag {
    display: inline-block;
    background: rgba(236,72,153,0.1);
    color: #f472b6;
    border: 1px solid rgba(236,72,153,0.25);
    font-size: 0.72rem;
    padding: 1px 7px;
    border-radius: 4px;
    margin-right: 4px;
}

/* ── Section header ─────────────────────────────────────── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 1.2rem 0 0.6rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1e293b;
}
.section-header h3 {
    font-size: 0.95rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 0;
}

/* ── Welcome card ───────────────────────────────────────── */
.welcome-card {
    text-align: center;
    padding: 3rem 2rem;
    background: linear-gradient(135deg, rgba(102,126,234,0.06), rgba(118,75,162,0.06));
    border: 1px dashed rgba(102,126,234,0.25);
    border-radius: 16px;
    margin: 2rem auto;
    max-width: 500px;
}
.welcome-card h2 { font-size: 1.3rem; font-weight: 600; color: #e2e8f0; margin-bottom: 0.5rem; }
.welcome-card p { color: #94a3b8; font-size: 0.92rem; line-height: 1.6; }

/* ── Buttons ────────────────────────────────────────────── */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s ease;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 25px rgba(102,126,234,0.35);
}
div.stDownloadButton > button {
    background: transparent;
    border: 1px solid #667eea;
    color: #a5b4fc;
    border-radius: 10px;
    font-weight: 500;
}

/* ── Sidebar ────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0a0e1a;
    border-right: 1px solid #1e293b;
}
.sidebar-label {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #475569;
    margin: 0.8rem 0 0.3rem;
}

/* ── Video container ────────────────────────────────────── */
.video-container {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 1rem;
    margin-top: 0.5rem;
}

/* ── Hide defaults ──────────────────────────────────────── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""


# ---------------------------------------------------------------------------
# 1. PROJECT MANAGEMENT
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    slug = re.sub(r'[^\w\s-]', '', name.lower().strip())
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug or "untitled"


def list_projects() -> list[dict]:
    projects = []
    for d in PROJECTS_DIR.iterdir():
        meta_path = d / "project.json"
        if d.is_dir() and meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                meta["_dir"] = d.name
                projects.append(meta)
            except (json.JSONDecodeError, KeyError):
                pass
    projects.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return projects


def create_project(name: str) -> dict:
    slug = _slug(name)
    project_dir = PROJECTS_DIR / slug
    counter = 2
    while project_dir.exists():
        project_dir = PROJECTS_DIR / f"{slug}-{counter}"
        counter += 1
    project_dir.mkdir(parents=True)
    (project_dir / "sketches").mkdir()
    (project_dir / "clips").mkdir()
    meta = {
        "name": name,
        "slug": project_dir.name,
        "created_at": datetime.now().isoformat(),
        "script": "",
        "scenes": [],
        "narration": dict(DEFAULT_NARRATION),
        "status": "new",
        "clip_duration": 4,
    }
    (project_dir / "project.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    return meta


def migrate_project_schema(meta: dict) -> dict:
    """Migrate old flat scene list to new structured format."""
    scenes = meta.get("scenes", [])
    if scenes and isinstance(scenes[0], str):
        meta["scenes"] = [
            {
                "text": s,
                "image_prompt": generate_image_prompt(s),
                "video_prompt": generate_video_prompt(s),
                "image_generated": False,
                "video_generated": False,
            }
            for s in scenes
        ]
        # Check if images/videos already exist on disk
        slug = meta.get("slug", "")
        if slug:
            for i, scene in enumerate(meta["scenes"]):
                if (get_project_dir(slug) / "sketches" / f"scene_{i:03d}.png").exists():
                    scene["image_generated"] = True
                if (get_project_dir(slug) / "clips" / f"clip_{i:03d}.mp4").exists():
                    scene["video_generated"] = True
    if "narration" not in meta:
        meta["narration"] = dict(DEFAULT_NARRATION)
    return meta


def load_project(slug: str) -> dict | None:
    meta_path = PROJECTS_DIR / slug / "project.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["slug"] = slug
        meta = migrate_project_schema(meta)
        return meta
    return None


def save_project(meta: dict):
    slug = meta["slug"]
    meta_path = PROJECTS_DIR / slug / "project.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def delete_project(slug: str):
    project_dir = PROJECTS_DIR / slug
    if project_dir.exists():
        shutil.rmtree(project_dir)


def rename_project(slug: str, new_name: str) -> dict | None:
    meta = load_project(slug)
    if meta:
        meta["name"] = new_name
        save_project(meta)
    return meta


def get_project_dir(slug: str) -> Path:
    return PROJECTS_DIR / slug


def get_final_video(slug: str) -> Path | None:
    path = get_project_dir(slug) / "final_output.mp4"
    return path if path.exists() else None


# ---------------------------------------------------------------------------
# 2. PROMPT GENERATION
# ---------------------------------------------------------------------------

def generate_image_prompt(scene_text: str) -> str:
    return (
        f"Simple grey pencil sketch, minimal linework, no detailed faces, "
        f"storyboard style, monochrome grey tones on white background, "
        f"clean simple illustration, no shading details: {scene_text} "
        f"16:9 composition."
    )


def generate_video_prompt(scene_text: str) -> str:
    return f"Cinematic slow motion, gentle camera pan: {scene_text}"


def build_scene_dicts(scene_texts: list[str]) -> list[dict]:
    """Convert raw scene strings into structured scene dicts."""
    return [
        {
            "text": t,
            "image_prompt": generate_image_prompt(t),
            "video_prompt": generate_video_prompt(t),
            "image_generated": False,
            "video_generated": False,
        }
        for t in scene_texts
    ]


# ---------------------------------------------------------------------------
# 3. API FUNCTIONS — Script Parsing
# ---------------------------------------------------------------------------

def parse_script_mock(script: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    return [s.strip() for s in sentences if s.strip()]


def parse_script_openai(script: str, api_key: str) -> list[str]:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a screenwriting assistant. Split the following script "
                    "into individual scene descriptions, one per line. Each scene "
                    "should be a single visual moment that can be illustrated as a "
                    "pencil sketch. Return ONLY a JSON array of strings, no markdown."
                ),
            },
            {"role": "user", "content": script},
        ],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)


# ---------------------------------------------------------------------------
# 4. API FUNCTIONS — Image Generation
# ---------------------------------------------------------------------------

def _wrap_text(text: str, max_chars: int = 35) -> list[str]:
    return textwrap.wrap(text, width=max_chars)


def generate_sketch_mock(scene_text: str, index: int) -> Image.Image:
    w, h = 768, 512
    img = Image.new("RGB", (w, h), "#f5f0e8")
    draw = ImageDraw.Draw(img)
    for offset in (8, 12):
        draw.rectangle([offset, offset, w - offset, h - offset],
                        outline="#3a3a3a", width=2)
    draw.text((30, 20), f"Scene {index + 1}", fill="#555555")
    lines = _wrap_text(scene_text, 45)
    y = h // 2 - len(lines) * 12
    for line in lines:
        bbox = draw.textbbox((0, 0), line)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2, y), line, fill="#2a2a2a")
        y += 24
    for cx, cy in [(50, h - 60), (w - 50, h - 60)]:
        for i in range(5):
            draw.line((cx - 15 + i * 4, cy - 10, cx - 5 + i * 4, cy + 10),
                       fill="#aaaaaa", width=1)
    return img


def generate_sketch_openai(prompt: str, api_key: str) -> Image.Image:
    import requests as req
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1792x1024",
        quality="standard",
    )
    image_url = response.data[0].url
    image_data = req.get(image_url).content
    return Image.open(io.BytesIO(image_data))


def generate_single_image(meta: dict, index: int, use_mock: bool,
                          openai_key: str) -> bool:
    """Generate sketch for one scene. Returns True on success."""
    scene = meta["scenes"][index]
    slug = meta["slug"]
    sketches_dir = get_project_dir(slug) / "sketches"
    sketches_dir.mkdir(exist_ok=True)
    sketch_path = sketches_dir / f"scene_{index:03d}.png"

    # Guard: if image already exists on disk, skip (no double charge)
    if sketch_path.exists():
        st.info(f"Scene {index+1}: Image already exists. Skipping.")
        meta["scenes"][index]["image_generated"] = True
        save_project(meta)
        return True

    if use_mock:
        img = generate_sketch_mock(scene["text"], index)
    else:
        if not openai_key:
            st.error("OpenAI API key required.")
            return False
        img = generate_sketch_openai(scene["image_prompt"], openai_key)

    img.save(str(sketch_path))
    meta["scenes"][index]["image_generated"] = True
    save_project(meta)
    return True


def generate_all_images(meta: dict, use_mock: bool, openai_key: str):
    """Generate images for all scenes with progress."""
    progress = st.progress(0)
    for i in range(len(meta["scenes"])):
        progress.progress((i) / len(meta["scenes"]),
                          text=f"Generating image {i+1}/{len(meta['scenes'])}...")
        if not meta["scenes"][i]["image_generated"]:
            generate_single_image(meta, i, use_mock, openai_key)
    progress.progress(1.0, text="All images generated!")
    time.sleep(0.5)
    progress.empty()


# ---------------------------------------------------------------------------
# 5. API FUNCTIONS — Video Animation
# ---------------------------------------------------------------------------

def animate_sketch_mock(image: Image.Image, duration: float, index: int,
                        out_dir: str) -> str:
    from moviepy import ImageClip
    img_array = np.array(image)
    clip = ImageClip(img_array, duration=duration)

    start_scale, end_scale = 1.0, 1.15

    def zoom_frame(get_frame, t):
        progress = t / duration
        scale = start_scale + (end_scale - start_scale) * progress
        frame = get_frame(t)
        h, w = frame.shape[:2]
        new_h, new_w = int(h * scale), int(w * scale)
        resized = np.array(
            Image.fromarray(frame).resize((new_w, new_h), Image.LANCZOS)
        )
        y_off = (new_h - h) // 2
        x_off = (new_w - w) // 2
        return resized[y_off:y_off + h, x_off:x_off + w]

    clip = clip.transform(zoom_frame)
    clip = clip.with_fps(24)
    out_path = os.path.join(out_dir, f"clip_{index:03d}.mp4")
    clip.write_videofile(out_path, codec="libx264", audio=False,
                         logger=None, preset="ultrafast")
    clip.close()
    return out_path


def animate_sketch_atlascloud(image: Image.Image, video_prompt: str,
                              api_key: str, duration: float,
                              index: int, out_dir: str) -> str:
    """Generate animated video via Atlascloud Vidu q2-pro-fast reference-to-video."""
    import requests as req

    # Encode image as base64 data URI
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    image_data_uri = f"data:image/png;base64,{img_b64}"

    # Submit video generation request
    request_body = {
        "model": "vidu/q2-pro-fast/reference-to-video",
        "images": [image_data_uri],
        "prompt": video_prompt,
        "duration": int(duration),
        "seed": 0,
        "aspect_ratio": "16:9",
        "movement_amplitude": "auto",
    }

    st.info(f"Submitting scene {index + 1} to Atlascloud Vidu...")

    resp = req.post(
        "https://api.atlascloud.ai/api/v1/model/generateVideo",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json=request_body,
        timeout=180,
    )

    if resp.status_code == 404:
        raise RuntimeError(
            "Atlascloud API returned 404. This usually means insufficient "
            "balance or the model is temporarily unavailable. "
            "Check your balance at https://console.atlascloud.ai"
        )
    resp.raise_for_status()

    resp_data = resp.json()

    # Response may be nested: {"data": {"id": ...}} or flat: {"id": ...}
    inner_data = resp_data.get("data", {}) if isinstance(resp_data.get("data"), dict) else {}
    prediction_id = (
        inner_data.get("id")
        or resp_data.get("id")
        or resp_data.get("prediction_id")
    )
    if not prediction_id:
        raise RuntimeError(f"Atlascloud: No prediction ID in response: {resp_data}")

    st.info(f"Scene {index + 1}: Video submitted (ID: {prediction_id[:12]}...). Polling for result...")

    # Poll for completion (up to ~15 minutes)
    poll_status_placeholder = st.empty()
    for attempt in range(90):
        time.sleep(10)
        try:
            status_resp = req.get(
                f"https://api.atlascloud.ai/api/v1/model/prediction/{prediction_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=120,
            )
        except (req.exceptions.ReadTimeout, req.exceptions.ConnectionError):
            poll_status_placeholder.warning(
                f"Scene {index+1}: Poll attempt {attempt+1} timed out, retrying...")
            continue

        if status_resp.status_code != 200:
            poll_status_placeholder.warning(
                f"Scene {index+1}: Poll returned {status_resp.status_code}, retrying...")
            continue

        raw_data = status_resp.json()

        # Response is nested: {"data": {"id": ..., "status": ..., "outputs": [...]}}
        # Try nested first, then top-level as fallback
        inner = raw_data.get("data", {}) if isinstance(raw_data.get("data"), dict) else {}
        status = inner.get("status", "") or raw_data.get("status", "")

        poll_status_placeholder.info(
            f"Scene {index+1}: Status = {status} (attempt {attempt+1})")

        if status in ("succeeded", "completed"):
            # Get video URL from nested data.outputs, then fallback to top-level
            outputs = inner.get("outputs", []) or raw_data.get("outputs", [])
            if not outputs:
                output_url = (inner.get("output", {}).get("video", "")
                              or raw_data.get("output", {}).get("video", ""))
                if output_url:
                    outputs = [output_url]
            if not outputs:
                raise RuntimeError(
                    f"Atlascloud: Video succeeded but no outputs found. "
                    f"Full response: {json.dumps(raw_data)[:500]}")

            video_url = outputs[0] if isinstance(outputs[0], str) else outputs[0].get("url", "")
            if not video_url:
                raise RuntimeError(f"Atlascloud: Empty video URL in outputs: {outputs}")

            poll_status_placeholder.info(f"Scene {index+1}: Downloading video...")
            video_data = req.get(video_url, timeout=180).content
            out_path = os.path.join(out_dir, f"clip_{index:03d}.mp4")
            with open(out_path, "wb") as f:
                f.write(video_data)
            poll_status_placeholder.success(f"Scene {index+1}: Video ready!")
            return out_path

        elif status == "failed":
            error_msg = (inner.get("error", "") or raw_data.get("error", "")
                         or inner.get("message", "") or raw_data.get("message", "Unknown error"))
            poll_status_placeholder.empty()
            raise RuntimeError(f"Atlascloud generation failed: {error_msg}")

        # else: still processing — continue polling

    poll_status_placeholder.empty()
    raise TimeoutError("Atlascloud video generation timed out (15 min)")


def generate_single_video(meta: dict, index: int, use_mock: bool,
                          atlas_key: str, clip_duration: float) -> bool:
    """Generate video clip for one scene. Returns True on success."""
    scene = meta["scenes"][index]
    slug = meta["slug"]
    clips_dir = get_project_dir(slug) / "clips"
    clips_dir.mkdir(exist_ok=True)
    clip_path = clips_dir / f"clip_{index:03d}.mp4"

    # Guard: if video already exists on disk, skip (no double charge)
    if clip_path.exists():
        st.info(f"Scene {index+1}: Video already exists. Skipping.")
        meta["scenes"][index]["video_generated"] = True
        save_project(meta)
        return True

    # Guard: if a prediction is already in-flight for this scene, resume polling
    pending_key = f"_pending_video_{slug}_{index}"
    if pending_key in st.session_state:
        st.warning(f"Scene {index+1}: A request is already in progress. "
                   "Refresh the page once it completes.")
        return False

    sketch_path = get_project_dir(slug) / "sketches" / f"scene_{index:03d}.png"
    if not sketch_path.exists():
        st.error(f"Scene {index+1}: Generate the image first.")
        return False

    img = Image.open(sketch_path)

    if use_mock:
        animate_sketch_mock(img, clip_duration, index, str(clips_dir))
    else:
        if not atlas_key:
            st.error("Atlascloud API key required for video generation.")
            return False
        # Mark as in-flight before the API call
        st.session_state[pending_key] = True
        try:
            animate_sketch_atlascloud(img, scene["video_prompt"], atlas_key,
                                      clip_duration, index, str(clips_dir))
        finally:
            # Clear in-flight flag when done (success or failure)
            st.session_state.pop(pending_key, None)

    meta["scenes"][index]["video_generated"] = True
    save_project(meta)
    return True


def generate_all_videos(meta: dict, use_mock: bool, atlas_key: str,
                        clip_duration: float):
    """Generate videos for all scenes with progress."""
    progress = st.progress(0)
    for i in range(len(meta["scenes"])):
        progress.progress((i) / len(meta["scenes"]),
                          text=f"Animating scene {i+1}/{len(meta['scenes'])}...")
        if not meta["scenes"][i]["video_generated"]:
            ok = generate_single_video(meta, i, use_mock, atlas_key,
                                       clip_duration)
            if not ok:
                progress.empty()
                return
    progress.progress(1.0, text="All videos generated!")
    time.sleep(0.5)
    progress.empty()


# ---------------------------------------------------------------------------
# 6. API FUNCTIONS — Narration (ElevenLabs)
# ---------------------------------------------------------------------------

def get_elevenlabs_voices_mock() -> list[dict]:
    return MOCK_VOICES


def get_elevenlabs_voices(api_key: str) -> list[dict]:
    import requests as req
    resp = req.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": api_key},
        timeout=10,
    )
    resp.raise_for_status()
    voices = resp.json().get("voices", [])
    result = []
    for v in voices:
        name = v.get("name", "Unknown")
        labels = v.get("labels", {})
        # Build descriptive name like "Liam - Energetic, Social Media Creator"
        desc_parts = []
        if labels.get("accent"):
            desc_parts.append(labels["accent"].title())
        if labels.get("description"):
            desc_parts.append(labels["description"].title())
        if labels.get("use_case"):
            desc_parts.append(labels["use_case"].title())
        display_name = f"{name} - {', '.join(desc_parts)}" if desc_parts else name
        result.append({"voice_id": v["voice_id"], "name": display_name})
    return result


def generate_narration_mock(text: str, out_path: str) -> str:
    """Create a silent WAV as placeholder narration."""
    duration_sec = max(2, len(text.split()) * 0.4)
    sample_rate = 22050
    n_samples = int(sample_rate * duration_sec)
    with wave.open(out_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b'\x00\x00' * n_samples)
    return out_path


def generate_narration_elevenlabs(text: str, voice_id: str, tags: str,
                                  api_key: str, out_path: str) -> str:
    """Generate narration via ElevenLabs API using eleven_v3 model."""
    import requests as req

    # Prepend tags as style instructions for v3
    narration_text = text
    if tags.strip():
        narration_text = f"[{tags.strip()}] {text}"

    # ElevenLabs v3 has a 3000 char limit — split if needed
    if len(narration_text) > 3000:
        narration_text = narration_text[:3000]

    resp = req.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={
            "text": narration_text,
            "model_id": "eleven_v3",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True,
            },
        },
    )

    if resp.status_code != 200:
        error_detail = resp.text[:300] if resp.text else "Unknown error"
        raise RuntimeError(
            f"ElevenLabs API error ({resp.status_code}): {error_detail}"
        )

    with open(out_path, "wb") as f:
        f.write(resp.content)
    return out_path


# ---------------------------------------------------------------------------
# 7. VIDEO STITCHING
# ---------------------------------------------------------------------------

def stitch_video(clip_paths: list[str], music_path: str | None,
                 narration_path: str | None, out_dir: str) -> str:
    from moviepy import (
        VideoFileClip, concatenate_videoclips, AudioFileClip,
        CompositeAudioClip,
    )

    clips = [VideoFileClip(p) for p in clip_paths]
    final = concatenate_videoclips(clips, method="compose")

    audio_tracks = []

    # Add narration at full volume
    if narration_path and os.path.exists(narration_path):
        narration_audio = AudioFileClip(narration_path)
        if narration_audio.duration > final.duration:
            narration_audio = narration_audio.subclipped(0, final.duration)
        audio_tracks.append(narration_audio)

    # Add background music at lower volume
    if music_path and os.path.exists(music_path):
        bg_music = AudioFileClip(music_path)
        if bg_music.duration < final.duration:
            from moviepy import concatenate_audioclips
            loops_needed = int(final.duration / bg_music.duration) + 1
            bg_music = concatenate_audioclips([bg_music] * loops_needed)
        bg_music = bg_music.subclipped(0, final.duration).with_volume_scaled(0.2)
        audio_tracks.append(bg_music)

    if audio_tracks:
        if final.audio:
            audio_tracks.insert(0, final.audio)
        final = final.with_audio(CompositeAudioClip(audio_tracks))

    out_path = os.path.join(out_dir, "final_output.mp4")
    final.write_videofile(out_path, codec="libx264", audio_codec="aac",
                          logger=None, preset="ultrafast")

    for c in clips:
        c.close()
    final.close()
    return out_path


# ---------------------------------------------------------------------------
# 8. UI HELPERS
# ---------------------------------------------------------------------------

def _status_badge(status: str) -> str:
    labels = {
        "new": ("New", "status-new"),
        "parsed": ("Parsed", "status-processing"),
        "images_done": ("Images Done", "status-processing"),
        "videos_done": ("Videos Done", "status-processing"),
        "completed": ("Completed", "status-completed"),
    }
    label, cls = labels.get(status, ("Unknown", "status-new"))
    return f'<span class="status-badge {cls}">{label}</span>'


def _update_project_status(meta: dict):
    """Recalculate project status from scene states."""
    scenes = meta.get("scenes", [])
    if not scenes:
        meta["status"] = "new"
    elif all(s.get("video_generated") for s in scenes):
        if get_final_video(meta["slug"]):
            meta["status"] = "completed"
        else:
            meta["status"] = "videos_done"
    elif all(s.get("image_generated") for s in scenes):
        meta["status"] = "images_done"
    else:
        meta["status"] = "parsed"


# ---------------------------------------------------------------------------
# 9. STREAMLIT UI
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="SketchMotion",
        page_icon="&#127916;",
        layout="wide",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ── Session state ─────────────────────────────────────────────────
    if "current_project" not in st.session_state:
        existing = list_projects()
        st.session_state.current_project = existing[0]["slug"] if existing else None
    if "show_new_project" not in st.session_state:
        st.session_state.show_new_project = False

    # ── Sidebar ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;padding:0.6rem 0 0.2rem;">'
            '<span style="font-size:1.5rem;">&#127916;</span><br>'
            '<span style="font-weight:600;font-size:0.92rem;color:#e2e8f0;">'
            'SketchMotion</span></div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-label">Projects</div>',
                    unsafe_allow_html=True)

        projects = list_projects()
        project_names = [p["name"] for p in projects]
        project_slugs = [p["slug"] for p in projects]

        if st.button("+ New Project", use_container_width=True):
            st.session_state.show_new_project = True

        if st.session_state.show_new_project:
            with st.form("new_project_form"):
                new_name = st.text_input("Project Name",
                                         placeholder="My Short Film")
                col1, col2 = st.columns(2)
                submitted = col1.form_submit_button("Create", type="primary")
                cancelled = col2.form_submit_button("Cancel")
                if submitted and new_name.strip():
                    meta = create_project(new_name.strip())
                    st.session_state.current_project = meta["slug"]
                    st.session_state.show_new_project = False
                    st.rerun()
                if cancelled:
                    st.session_state.show_new_project = False
                    st.rerun()

        if projects:
            current_idx = 0
            if st.session_state.current_project in project_slugs:
                current_idx = project_slugs.index(
                    st.session_state.current_project)

            selected_name = st.selectbox(
                "Select Project", project_names, index=current_idx,
                key="project_selector", label_visibility="collapsed",
            )
            if selected_name:
                idx = project_names.index(selected_name)
                st.session_state.current_project = project_slugs[idx]

            if st.session_state.current_project:
                with st.expander("Manage Project", expanded=False):
                    new_name = st.text_input("Rename", key="rename_input",
                                             placeholder="New name",
                                             label_visibility="collapsed")
                    if st.button("Rename", use_container_width=True) \
                            and new_name.strip():
                        rename_project(st.session_state.current_project,
                                       new_name.strip())
                        st.rerun()
                    if st.button("Delete Project", use_container_width=True):
                        st.session_state.confirm_delete = True
                    if st.session_state.get("confirm_delete"):
                        st.warning("This cannot be undone.")
                        c1, c2 = st.columns(2)
                        if c1.button("Confirm", type="primary"):
                            delete_project(st.session_state.current_project)
                            st.session_state.current_project = None
                            st.session_state.confirm_delete = False
                            st.rerun()
                        if c2.button("Cancel "):
                            st.session_state.confirm_delete = False
                            st.rerun()

        st.markdown('<div class="sidebar-label">Configuration</div>',
                    unsafe_allow_html=True)
        use_mock = st.toggle("Mock Data (no API keys)", value=True)

        openai_key = st.text_input("OpenAI Key", type="password",
                                   help="GPT + DALL-E 3")
        atlas_key = st.text_input("Atlascloud Key", type="password",
                                  help="Wan 2.6 image-to-video")
        elevenlabs_key = st.text_input("ElevenLabs Key", type="password",
                                       help="Voice narration")

        st.markdown('<div class="sidebar-label">Video</div>',
                    unsafe_allow_html=True)
        clip_duration = st.slider("Clip Duration (s)", 2, 8, 4)

        music_file = st.file_uploader(
            "Background Music", type=["mp3", "wav", "ogg"],
            label_visibility="collapsed",
        )

    # ── Main Area ─────────────────────────────────────────────────────

    # Hero
    st.markdown(
        '<div class="hero-header">'
        '<h1>SketchMotion</h1>'
        '<p>Turn any script into a pencil-sketch animated video</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Welcome screen
    if not st.session_state.current_project:
        st.markdown(
            '<div class="welcome-card">'
            '<h2>Create Your First Project</h2>'
            '<p>Click <strong>+ New Project</strong> in the sidebar to start.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # Load project
    meta = load_project(st.session_state.current_project)
    if not meta:
        st.error("Project not found.")
        st.session_state.current_project = None
        return

    slug = meta["slug"]
    scenes = meta.get("scenes", [])

    # Project info bar
    _update_project_status(meta)
    badge = _status_badge(meta["status"])
    created = meta.get("created_at", "")[:10]
    scene_count = len(scenes)
    st.markdown(
        f'<div class="project-bar">'
        f'<span class="project-name">{meta["name"]}</span>'
        f'{badge}'
        f'<span class="project-meta">Created {created}'
        f'{f" &bull; {scene_count} scenes" if scene_count else ""}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Full script display (if parsed)
    if scenes and meta.get("script"):
        st.markdown(
            f'<div class="full-script"><strong>Full Script:</strong> '
            f'{meta["script"]}</div>',
            unsafe_allow_html=True,
        )

    # ── Script Input & Parse ──────────────────────────────────────────
    script = st.text_area(
        "Your Script", value=meta.get("script", ""), height=130,
        placeholder=(
            "A lone astronaut steps onto a barren red landscape. "
            "She looks up at the two moons hanging in the violet sky..."
        ),
        label_visibility="collapsed",
    )

    # Auto-save script
    if script != meta.get("script", ""):
        meta["script"] = script
        save_project(meta)

    if st.button("Parse Script", type="primary", use_container_width=True):
        if not script.strip():
            st.warning("Please enter a script first.")
        else:
            with st.spinner("Splitting script into scenes..."):
                meta["script"] = script
                if use_mock:
                    raw_scenes = parse_script_mock(script)
                else:
                    if not openai_key:
                        st.error("OpenAI API key required for parsing.")
                        st.stop()
                    raw_scenes = parse_script_openai(script, openai_key)

                meta["scenes"] = build_scene_dicts(raw_scenes)
                meta["narration"]["text"] = script
                save_project(meta)
            st.rerun()

    # ── Nothing to show yet ───────────────────────────────────────────
    if not scenes:
        return

    # ── Narration Section ─────────────────────────────────────────────
    st.markdown(
        '<div class="section-header">'
        '<h3>&#127908; Narration (ElevenLabs)</h3></div>',
        unsafe_allow_html=True,
    )

    enable_narration = st.toggle("Enable Narration", value=bool(
        meta.get("narration", {}).get("audio_generated") or elevenlabs_key
    ), key="enable_narration")

    narration = meta.get("narration", dict(DEFAULT_NARRATION))

    if enable_narration:
        # Voice selection: use real voices if key provided, mock otherwise
        if elevenlabs_key:
            cache_key = "_voices_cache"
            cache_key_key = "_voices_cache_api_key"
            if st.session_state.get(cache_key_key) != elevenlabs_key:
                st.session_state.pop(cache_key, None)
                st.session_state[cache_key_key] = elevenlabs_key
            if cache_key not in st.session_state:
                try:
                    with st.spinner("Fetching voices from ElevenLabs..."):
                        fetched = get_elevenlabs_voices(elevenlabs_key)
                    st.session_state[cache_key] = fetched if fetched else ELEVENLABS_DEFAULT_VOICES
                except Exception:
                    # Key may lack voices_read permission — use defaults
                    st.session_state[cache_key] = ELEVENLABS_DEFAULT_VOICES
            voices = st.session_state[cache_key]
        else:
            voices = get_elevenlabs_voices_mock() if use_mock else ELEVENLABS_DEFAULT_VOICES
            if not elevenlabs_key:
                st.caption("Add your ElevenLabs key in the sidebar to generate audio.")

        voice_names = [v["name"] for v in voices]
        voice_ids = [v["voice_id"] for v in voices]

        nar_col1, nar_col2 = st.columns([2, 1])
        with nar_col1:
            current_voice_idx = 0
            if narration.get("voice_id") in voice_ids:
                current_voice_idx = voice_ids.index(narration["voice_id"])
            selected_voice = st.selectbox("Voice", voice_names,
                                           index=current_voice_idx,
                                           key="voice_select")
            voice_idx = voice_names.index(selected_voice)
            narration["voice_id"] = voice_ids[voice_idx]
            narration["voice_name"] = voice_names[voice_idx]

        with nar_col2:
            tags = st.text_input("Style Tags",
                                  value=narration.get("tags", ""),
                                  placeholder="Sarcastic, Voiceover, Slow",
                                  key="narration_tags")
            narration["tags"] = tags

        if tags.strip():
            tag_html = " ".join(
                f'<span class="speaker-tag">{t.strip()}</span>'
                for t in tags.split(",") if t.strip()
            )
            st.markdown(tag_html, unsafe_allow_html=True)

        narration_text = st.text_area(
            "Narration Text",
            value=narration.get("text", meta.get("script", "")),
            height=80,
            key="narration_text",
            label_visibility="collapsed",
        )
        narration["text"] = narration_text

        # Save narration changes
        meta["narration"] = narration
        save_project(meta)

        if st.button("Generate Master Audio", key="gen_audio",
                     use_container_width=True, type="primary"):
            audio_path = str(get_project_dir(slug) / "narration.mp3")
            with st.spinner("Generating narration with ElevenLabs v3..."):
                if use_mock or not elevenlabs_key:
                    audio_path = audio_path.replace(".mp3", ".wav")
                    generate_narration_mock(narration_text, audio_path)
                    st.info("Generated mock narration (silent). Add ElevenLabs key for real audio.")
                else:
                    try:
                        generate_narration_elevenlabs(
                            narration_text, narration["voice_id"],
                            narration["tags"], elevenlabs_key, audio_path,
                        )
                    except Exception as e:
                        st.error(f"ElevenLabs error: {e}")
                        st.stop()
            narration["audio_generated"] = True
            meta["narration"] = narration
            save_project(meta)
            st.success("Narration generated!")
            st.rerun()

        # Show existing narration audio
        nar_path_mp3 = get_project_dir(slug) / "narration.mp3"
        nar_path_wav = get_project_dir(slug) / "narration.wav"
        existing_nar = (nar_path_mp3 if nar_path_mp3.exists()
                        else nar_path_wav if nar_path_wav.exists() else None)
        if existing_nar:
            st.audio(str(existing_nar))

    # ── Batch Buttons ─────────────────────────────────────────────────
    st.markdown(
        '<div class="section-header">'
        '<h3>&#9998; Scenes</h3></div>',
        unsafe_allow_html=True,
    )

    batch_col1, batch_col2 = st.columns(2)
    with batch_col1:
        if st.button("Generate All Images", key="gen_all_img",
                     use_container_width=True, type="primary"):
            generate_all_images(meta, use_mock, openai_key)
            st.rerun()
    with batch_col2:
        if st.button("Generate All Videos", key="gen_all_vid",
                     use_container_width=True, type="primary"):
            generate_all_videos(meta, use_mock, atlas_key, clip_duration)
            st.rerun()

    # ── Scene Cards ───────────────────────────────────────────────────
    for i, scene in enumerate(scenes):
        st.markdown(
            f'<div class="scene-card">'
            f'<div class="scene-card-header">'
            f'<span class="scene-num">{i+1:02d}</span>'
            f'{scene["text"]}'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        left_col, right_col = st.columns([3, 2])

        with left_col:
            # Image prompt
            st.markdown(
                '<span class="prompt-label prompt-label-image">Image Prompt</span>',
                unsafe_allow_html=True,
            )
            new_img_prompt = st.text_area(
                f"img_prompt_{i}", value=scene["image_prompt"],
                key=f"img_prompt_{i}", height=80,
                label_visibility="collapsed",
            )
            if new_img_prompt != scene["image_prompt"]:
                meta["scenes"][i]["image_prompt"] = new_img_prompt
                save_project(meta)

            # Video prompt
            st.markdown(
                '<span class="prompt-label prompt-label-video">Video Prompt</span>',
                unsafe_allow_html=True,
            )
            new_vid_prompt = st.text_area(
                f"vid_prompt_{i}", value=scene["video_prompt"],
                key=f"vid_prompt_{i}", height=80,
                label_visibility="collapsed",
            )
            if new_vid_prompt != scene["video_prompt"]:
                meta["scenes"][i]["video_prompt"] = new_vid_prompt
                save_project(meta)

            # Per-scene buttons
            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button(f"Generate Image", key=f"gen_img_{i}",
                             use_container_width=True):
                    with st.spinner(f"Generating image for scene {i+1}..."):
                        generate_single_image(meta, i, use_mock, openai_key)
                    st.rerun()
            with btn2:
                if st.button(f"Generate Video", key=f"gen_vid_{i}",
                             use_container_width=True):
                    with st.spinner(f"Animating scene {i+1}..."):
                        generate_single_video(meta, i, use_mock, atlas_key,
                                              clip_duration)
                    st.rerun()

        with right_col:
            # Image preview
            sketch_path = get_project_dir(slug) / "sketches" / f"scene_{i:03d}.png"
            if sketch_path.exists():
                st.image(str(sketch_path), use_container_width=True)
            else:
                st.markdown(
                    '<div class="no-image-placeholder">No Image</div>',
                    unsafe_allow_html=True,
                )

            # Video preview
            clip_path = get_project_dir(slug) / "clips" / f"clip_{i:03d}.mp4"
            if clip_path.exists():
                st.video(str(clip_path))
            else:
                st.markdown(
                    '<div class="no-image-placeholder" style="min-height:60px;margin-top:0.5rem;">No Video</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")

    # ── Stitch Final Video ────────────────────────────────────────────
    all_videos_done = all(s.get("video_generated") for s in scenes)

    st.markdown(
        '<div class="section-header">'
        '<h3>&#127916; Final Video</h3></div>',
        unsafe_allow_html=True,
    )

    if all_videos_done:
        # Collect paths
        stitch_col1, stitch_col2 = st.columns([2, 1])
        with stitch_col1:
            if st.button("Stitch Final Video", type="primary",
                         use_container_width=True, key="stitch_btn"):
                clips_dir = get_project_dir(slug) / "clips"
                clip_paths = sorted(
                    str(p) for p in clips_dir.glob("clip_*.mp4"))

                # Music
                music_path = None
                if music_file:
                    tmp_music = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=os.path.splitext(music_file.name)[1])
                    tmp_music.write(music_file.read())
                    tmp_music.close()
                    music_path = tmp_music.name

                # Narration — check if narration audio exists
                narration_path = None
                if enable_narration:
                    nar_mp3 = get_project_dir(slug) / "narration.mp3"
                    nar_wav = get_project_dir(slug) / "narration.wav"
                    if nar_mp3.exists():
                        narration_path = str(nar_mp3)
                    elif nar_wav.exists():
                        narration_path = str(nar_wav)

                with st.spinner("Stitching video..."):
                    stitch_video(clip_paths, music_path, narration_path,
                                 str(get_project_dir(slug)))

                meta["status"] = "completed"
                save_project(meta)
                st.rerun()
    else:
        remaining_imgs = sum(1 for s in scenes if not s.get("image_generated"))
        remaining_vids = sum(1 for s in scenes if not s.get("video_generated"))
        parts = []
        if remaining_imgs:
            parts.append(f"{remaining_imgs} image{'s' if remaining_imgs > 1 else ''}")
        if remaining_vids:
            parts.append(f"{remaining_vids} video{'s' if remaining_vids > 1 else ''}")
        st.info(f"Generate all scenes first. Remaining: {', '.join(parts)}.")

    # Show existing final video
    final = get_final_video(slug)
    if final:
        st.video(str(final))
        with open(final, "rb") as f:
            st.download_button(
                label="Download Video",
                data=f.read(),
                file_name=f"{meta['name'].replace(' ', '_')}_sketch.mp4",
                mime="video/mp4",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
