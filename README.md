# It Began Here — Fake Friend Call Scam

A Singapore anti-scam short about Madam Lim, a capable 70-year-old whose trust in an unverified caller leads to financial loss. Selected decisions rewind to the first question: **“You really don't remember me?”** The safer replay teaches **STOP. CHECK. VERIFY.**

The complete plan is ready in [the storyboard](docs/storyboard.md), [shot list and prompts](docs/shot_list_and_prompts.md), [character bible/style guide](docs/character_bible_and_style.md), [timed dialogue](docs/dialogue_script.md), [rewind plan](docs/rewind_plan.md), [workflow/tools](docs/workflow_and_tools.md), [architecture](docs/architecture_and_implementation.md) and [asset list](docs/assets.md). Machine-readable manifests live in `prompts/`.

The cut is **180 seconds**, **42 edit segments**, **23 generated moving source takes**, and **32 separate voice cues**. The educational ending gets **53 seconds**, including 9–10-second warning-card holds. Reused/reversed footage and locally produced cards reduce paid generation. The financial ledger reconciles: $42,860 opening savings − $42,000 payments = $860. Additional repeated payments of $22,000 are explicitly labelled in the montage.

## 1. Install requirements

Python 3.12 and FFmpeg/FFprobe are available in this workspace. The existing `.venv` is ready. For a fresh machine:

```bash
cd /workspace/my-project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The baseline uses only Python's standard library. Install a full FFmpeg build with libass, drawtext, libx264 and AAC. On Ubuntu/Debian: `sudo apt-get install ffmpeg fonts-dejavu-core`. Set `config/project.json` → `font` to your installed TrueType/OpenType font path on other systems. Default is `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`.

```bash
python scripts/validate_project.py
python -m unittest discover -s tests -v
```

## 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` in your editor:

```dotenv
IMAGE_API_KEY=your_image_provider_key
VIDEO_API_KEY=your_video_provider_key
VOICE_API_KEY=your_voice_provider_key
VIDEO_MODEL=your_selected_fal_image_to_video_model_id
```

The image and voice adapters use OpenAI. The video adapter uses fal's queue; `VIDEO_API_KEY` is the fal key. **Choose a currently available `fal-ai/...` image-to-video endpoint from its dashboard.** Check its request schema and set `video_payload`, `video_supported_durations`, `video_duration_field`, `video_duration_format`, `video_image_field` and `video_prompt_field` in `config/project.json`. For example, an endpoint accepting `image_url`, `prompt`, and string `duration` of `5` or `10` matches the defaults. If its field names or return `video.url` differ, adapt the small fal adapter. No model is silently chosen for you or asserted to be available.

`IMAGE_MODEL`, `VOICE_MODEL` and optional per-speaker `VOICE_*` names are configurable. These are built-in synthetic voices; Singapore accents require review. Keys are never hard-coded or printed. `.env` is ignored by Git. Provider defaults are `manual` so generation requires explicit `--provider`. All paid generation commands below may incur provider charges; start with one test shot.

## 3. Generate character reference images

```bash
python scripts/generate_images.py --references --dry-run
python scripts/generate_images.py --provider openai --references
```

This creates `assets/images/references/home.png` and `madam_lim.png`. Approve face, hairstyle, age and room layout before continuing. Alternatively save approved manual PNGs at those paths. Anchors are passed into every shot image edit. Wardrobes vary only by specified story day. A seed alone does not guarantee identity.

## 4. Generate scenes

Generate one test first:

```bash
python scripts/generate_images.py --provider openai --shot scene_01_shot_02
python scripts/generate_video.py --shot scene_01_shot_02 --dry-run
python scripts/generate_video.py --provider fal --shot scene_01_shot_02
```

Then generate stills, review them, and animate:

```bash
python scripts/generate_images.py --provider openai
python scripts/generate_video.py --dry-run
python scripts/generate_video.py --provider fal
```

The adapter buys an allowed take length sufficient for the edit and trims later. Runway/Kling/manual exports can instead be saved to `assets/video/<shot_id>.mp4`. Source clips should be at least their edit duration. Sound from video models is stripped; controlled voices and FX are mixed separately. Do not bake generated subtitles or phone text into clips.

Existing files are skipped. `--force` regenerates image/voice files. For video, `--force` resumes/redownloads the saved queue job. To intentionally buy a replacement video, review and remove only its job JSON in `assets/video/jobs/` before rerunning with `--force`. Saved queue IDs prevent duplicate submission when a generation is interrupted. Live provider calls remain unverified until real keys and the selected model are configured.

## 5. Generate voices

```bash
python scripts/generate_voice.py --dry-run
python scripts/generate_voice.py --provider openai
```

Voice cues are independent `assets/audio/<cue_id>.wav` files. Four speakers are defined in the character bible. Use `--speaker narrator` to test the narrator alone. Imported consent-cleared recordings are supported at the same filenames. The generator reports cues longer than their time slots. **Re-time the manifest or record a shorter delivery; the assembler rejects long cues and never accelerates or truncates speech.** Speaker definitions request natural Singapore English but are not a guarantee of local accent quality.

## 6. Generate subtitles

```bash
python scripts/generate_subtitles.py
```

Produces English SRT/ASS, cue catalog and a translation template. Stable IDs make Mandarin adaptation possible without changing the story. Copy the template to a new JSON and replace the English values with reviewed translations:

```bash
python scripts/generate_subtitles.py --translation assets/subtitles/zh.json --language zh
```

For a Mandarin export, set `language`, `subtitle_language`, and `subtitle_font_family` in config, select an installed CJK font, and replace voice cue WAVs with reviewed Mandarin performances. Re-time dialogue and regenerate the derived shot timeline if necessary. Final assembly uses configured language/subtitle language. English/master timing is currently the approved baseline.

## 7. Generate the rewind

```bash
python scripts/create_rewind.py
```

Creates the scene's visual intermediate in `output/cache/film/…/scene_09.mp4` and isolated reversed FX. Voice, silence and music are mixed during final assembly. Use `--preview` to inspect with local storyboards. Nine selected bounded clips provide progressive time compression; the whole completed movie is never reversed. The exact original first-call take supplies both the freeze and safe replay. Digital silence lasts two seconds before the rewind and two seconds at its arrival.

## 8. Assemble the movie

Optional licensed music stems: `assets/music/normal.wav`, `hopeful.wav`, `tension.wav`, `safe.wav`. They are looped quietly under dialogue. Without imports, the pipeline supplies an original minimal tonal bed and original generic FX. No proprietary notification sounds are copied. Refine score and phone UI tracking in an editor for a polished release.

```bash
python scripts/assemble_video.py
```

The production command checks for every approved source and voice cue before rendering. It exports **`output/final_video.mp4`** as 1920×1080, 24fps H.264, stereo 48kHz AAC, captions burned in, with a loudness target of −16 LUFS. Text overlays, cards, split screen, freezes, trim/fades, selected reversal, timing, audio mixing and final mux are local FFmpeg operations. `--force` rebuilds intermediate shots after visual changes.

## 9. Preview the movie

No API keys required:

```bash
python scripts/build_preview.py
ffplay output/animatic.mp4
```

The **watermarked animatic** is a 180-second timing/storyboard preview with moving timing dots, real subtitles, original guide tones and the full educational ending. It is **not AI-generated cinematic footage and does not include spoken performances**. Preview assets never substitute for production assets. The final filename is reserved for the approved film. Open `output/animatic.mp4` or the final movie in VLC if `ffplay` is unavailable.

## 10. Export and review

The assembly command above is the final export command. Inspect `output/final_video.json` and FFprobe:

```bash
ffprobe -v error -show_format -show_streams output/final_video.mp4
```

Review with senior viewers: text size/hold times, Singapore pronunciation, familiar HDB detail, emotional dignity, identity/wardrobe continuity, readable overlays, absence of real financial details, signature arrival silence, and the final four-second reading hold. Tell viewers the film uses synthetic media. No hotline is included; official Singapore information is at https://www.scamshield.gov.sg/ (retrieved 2026-10-04). Contact your bank immediately if money has already been sent.

## Editing and learning the code

Start with `scamfilm/project.py` → manifests; `providers/` → external media; `graphics.py`/`subtitles.py` → exact text; `rewind.py` → bounded reversal; `audio.py` → scheduling and silence; `assembly.py` → final orchestration. `docs/architecture_and_implementation.md` explains all stages. To change timing, edit shot duration/cues then run `python scripts/refresh_plan.py`. It aligns durations to frames, recalculates all timeline positions and config runtime, validates before saving, and refreshes the storyboard, script, shot/rewind documents and assets. Source intervals must still fit their referenced takes. Outputs and caches are rebuildable; source assets and reference images remain separate.
