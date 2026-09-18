# BRIEF.md — Sovereign AI demo video (SIH judges)

```yaml
workflow: product-launch-video
flow: automation
storyboard: no
message: "Confidential industrial work needs AI that never leaves the machine."
destination: presentation-projector
aspect: 16:9
language: en
audience: SIH judges
length: 60s
angle: show-it-as-is showcase — real captured UI, narrator speaks live over silent video
music: none
```

## Intent

Showcase (not promo): feature the workbench's own captured screens as the
video's assets. Silent by design (`music: none`, no SCRIPT.md) — the presenter
narrates live over it.

## Story (6 scenes, 60s)

1. Title — Sovereign AI Workbench, SIH PS 26117 / MRPL.
2. Problem — refinery knowledge can't go to the cloud; the AI lives on-premise.
3. Stack — four local specialists (qwen3.5:4b, qwen2.5-coder:7b,
   nomic-embed-text, glm-ocr:q8_0), 100% open-weight via Ollama.
4. Proof 1 — real captured UI, Knowledge ON, grounded answer with sources.
5. Proof 2 — pipeline: upload → OCR → chunk+embed → grounded answer;
   not in KB → says so, nothing invented.
6. Close — no API keys, no telemetry, air-gap ready.

## Assets

- `assets/sov-hero.png` — clean workbench UI (captured 2026-09-09)
- `assets/sov-asked.png` — Knowledge ON + typed question (captured)
- `assets/sov-answered.png` — real grounded answer (pending background capture;
  swap into scene 4 if it lands, else ship with asked shot)
- `assets/gsap.min.js` — vendored runtime (no render-time network)

## Notes

- Renderer is CLI-free: paused GSAP timeline seeked per-frame via Playwright,
  encoded with ffmpeg. Composition honors the hyperframes-core contract
  (standalone root, data-* timing, one paused timeline, deterministic).
- Inferred fields (receipt: autonomous run, user said "you decide all"):
  length 60s, 16:9, silent, showcase angle, text-on-screen only.
