# Project architecture and implementation plan

The planning manifest is the single source of truth. Plain Python modules separate providers, media editing, audio, captions and orchestration. The initial implementation uses only the standard library plus an installed FFmpeg/FFprobe with libass/drawtext.

```text
my-project/
├── README.md
├── requirements.txt
├── .env.example
├── config/project.json
├── docs/
│   ├── storyboard.md
│   ├── character_bible_and_style.md
│   ├── dialogue_script.md
│   ├── shot_list_and_prompts.md
│   ├── rewind_plan.md
│   ├── workflow_and_tools.md
│   ├── architecture_and_implementation.md
│   └── assets.md
├── prompts/{characters,scenes,shots,negative_prompts}.json
├── scamfilm/
│   ├── project.py              # paths, config, environment, manifest validation
│   ├── media.py                # FFmpeg execution, probing, trimming, encoding
│   ├── graphics.py             # safe text overlays and cards
│   ├── audio.py                # original guide FX, music and voice scheduling
│   ├── subtitles.py            # SRT/ASS and translation catalog
│   ├── rewind.py               # bounded reverse plus time compression
│   ├── assembly.py             # per-shot builds and final mux
│   └── providers/
│       ├── base.py             # interchangeable image/video/voice contracts
│       ├── http.py             # TLS HTTP, downloads and multipart requests
│       ├── openai.py           # image references and speech
│       └── fal.py              # asynchronous image-to-video
├── scripts/
│   ├── validate_project.py
│   ├── generate_images.py
│   ├── generate_video.py
│   ├── generate_voice.py
│   ├── generate_subtitles.py
│   ├── create_rewind.py
│   ├── assemble_video.py
│   └── build_preview.py
├── tests/
├── assets/{images,video,audio,music,subtitles}/
└── output/
    ├── animatic.mp4            # visibly labelled local timing preview
    └── final_video.mp4         # production export after approved AI/voice assets
```

## Data contracts

Every shot includes scene/shot number, filename, edit duration, purpose, camera angle/framing, action, expression, timed dialogue/VO cues, sound/music, image/video/negative prompts, transition, subtitles, reverse compatibility, and source intervals when reused. Cue IDs are stable across translation. Absolute timeline positions are derived from local durations; edits must update the whole timeline together.

Provider methods: `generate_image(prompt, output, references=())`, `generate_video(image, prompt, output, duration)`, `generate_voice(text, speaker, output)`. Music is an explicit WAV import with original synthesized preview stems. No fictional external music endpoint is implied. To add a provider implement the corresponding protocol and select it through the factory; the editor is unchanged. Manual import is always possible.

## Build stages

1. **Planning:** author complete manifests and readable planning documents; check ledger, source links, cue limits, reading holds and total runtime.
2. **Generation:** create references, approved stills and source videos, then independent speech cues. Resume by skipping existing files; `--force` is explicit. Persist fal job IDs immediately so interruption does not cause duplicate purchases. Dry runs disclose planned work. No live provider runs without configuration.
3. **Local editing:** create original guide FX/music, render fictional UI overlays, generate captions. Normalize clips to consistent frame rate/resolution, trim or hold the tail for small provider duration differences, strip unapproved native audio. Explicit sources under one second or invalid media fail early.
4. **Rewind:** use `trim, reverse, setpts` on selected bounded intervals and `atrim, areverse, atempo` on isolated effects. Different segment speeds form the ramp. Dedicated first-call frame, exact zeroed silence intervals, reset card. No reversed subtitles/dialogue.
5. **Assembly:** source clips, cards, reuse, freeze and split screen are modular shot builders. Composite educational overlays; mix scheduled voice WAVs and original/approved sound stems; create global ASS subtitles; concatenate shot masters; apply loudness processing; mux H.264/AAC at 1080p. Scene and final methods share the same normalized shot cache. Fades are local so they do not silently change runtime.
6. **Verification:** validate money arithmetic, chronological cue ordering, reuse links, reverse bounds and fixed 180-second duration. Render short reverse and silent audio fixtures; check real frame/audio properties using FFprobe and WAV samples. Render complete preview to prove the local pipeline. Live-provider payloads are untested until credentials/model selection exist.

## Outputs and completion boundaries

The offline preview is typography/storyboard imagery, guide sound and captions; it is not a cinematic AI-generated film or authentic Singapore voice performance. It carries a visible watermark. `final_video.mp4` is reserved for the actual production command, which fails on missing approved assets. Generated-video continuity, native accents, licences and real provider schemas require review before release. This boundary prevents accidentally publishing a placeholder as the finished film.

The bank ledger is $42,860 opening, $42,000 sent, $860 remaining. The $22,000 aggregate is clearly illustrated. The rewind is metaphorical. The narrative teaches STOP, CHECK, VERIFY rather than operational crime techniques.
