# Recommended AI-video workflow and tools

1. Read the storyboard and timed script before generating media. Approve the identity/home anchors and the financial ledger. Begin with one face close-up, one phone/finger shot and the first-call scene as a low-cost quality test.
2. Use OpenAI image generation/editing for neutral character and home references, and then each scene still with both approved references. `gpt-image-1` is the configurable baseline, not an assertion that it is the latest model. Reference-edit requests preserve identity better than independent text-only images. Inspect every still for face, wardrobe, hands and room continuity.
3. Animate approved stills using a fal-hosted image-to-video model with reference-frame support. Kling-family models are a candidate; pick an available endpoint in the fal dashboard and copy its exact model ID and input schema. Capabilities, durations, pricing and licences depend on the selected model. The adapter uses fal's asynchronous queue; duration/image field names and additional model parameters are configurable. Alternatively export clips manually from Runway, Kling or another tool into the same filenames. Never pay for all shots before testing continuity.
4. Use OpenAI speech with `gpt-4o-mini-tts`, separate speakers and accent/delivery instructions. Built-in voices are approximations, not guaranteed authentic Singapore senior voices. Have a Singapore English speaker review delivery. If an accent is unsuitable, import consent-cleared recordings or swap the voice adapter. Do not impersonate a real friend or clone a person without permission. The preview contains synthetic guide tones only, not spoken performances.
5. Generate the English subtitle catalog from the script. Keep stable cue IDs. Translate `assets/subtitles/translation_template.json` into Mandarin later; use a licensed CJK font and regenerate subtitles and voice with reviewed timing. No dialogue or screen lettering is generated inside video frames.
6. Composite large illustrative banking/messages/contact overlays after generation. Real app logos, recipient details and credentials are excluded. Phone screens are intentionally blank in prompts; precise tracking/hand occlusion can be refined in DaVinci Resolve or another editor if a camera moves. Locked inserts permit simple overlays in the included pipeline.
7. Reverse only the specified bounded source intervals. Use short progressive time compression and isolated reversed FX, followed by complete silence on the exact first-call frame. Reuse the same take for the safer replay. Inspect the return of the first-transfer fingertip and the change from anxiety to calm.
8. Mix approved WAV voice cues, subtle original FX, and licensed music stems. Preview voices against subtitles and ensure every cue fits its slot without speeding up. The assembler rejects missing/too-long voices and missing film sources; it never silently replaces them with preview cards.
9. Render the 1080p final movie. Screen it with seniors for text readability, accent and comfort with rewind speed. Review emotion and clarity: the victim is a capable person under pressure, and the film illustrates prevention. Publish with a synthetic-media disclosure.

## Tools and sources

| Role | Recommendation | Included support |
|---|---|---|
| Images | OpenAI image generation + edits | Reference-aware HTTP adapter, PNG assets |
| Video | fal-hosted image-to-video model; manual exports also supported | Queue adapter, configurable schema, authenticated submit/poll |
| Voice | OpenAI speech; human recording if accent fails review | Speech adapter, four identities, cue WAVs |
| Music | Licensed stems, commissioned score, or a tool with clear commercial licence | WAV import; original synthetic preview score |
| Editing | FFmpeg; optional DaVinci Resolve for polish | Concatenation, fades, UI overlays, reverse/atempo, ASS captions, stereo mixing, H.264/AAC |
| Review | VLC/ffplay, headphones and a senior test audience | Local watermarked 180-second animatic |

Public sources retrieved successfully on 2026-10-04:

- https://platform.openai.com/docs/guides/image-generation
- https://platform.openai.com/docs/guides/text-to-speech
- https://docs.fal.ai/model-apis/model-endpoints/queue
- https://www.scamshield.gov.sg/

No hotline is displayed. Current official contacts should be checked on ScamShield before a release that includes them. The retrieved homepage confirms the source is available; this project does not rely on a remembered hotline number.

## Generation count and budget

The master is 180 seconds. `prompts/shots.json` determines the live count. Generated source takes are typically 4–8 seconds; provider minimums may require 5- or 10-second purchases. Cards, a freeze, exact replay, split screen and rewind fragments are local edits. Two initial reference images plus one still per generated take are the base image budget. Repeat only rejected takes. `generate_video.py --dry-run` prints intended jobs/durations without API calls. No precise price is claimed because model prices change.

All API credentials are environment variables: `IMAGE_API_KEY`, `VIDEO_API_KEY`, `VOICE_API_KEY`. No key is committed, logged or placed in a prompt.
