# Text-to-speech (TTS) in EduClaw

EduClaw includes a **pluggable TTS subsystem** under `educlaw.tts`: a small `TTSBackend` protocol, a registry (built-ins + `importlib.metadata` entry points, same pattern as [`educlaw.channels`](../src/educlaw/channels/registry.py)), and optional **Kitten TTS** integration for **offline-friendly**, CPU-only synthesis with compact ONNX models (~25–80 MB on disk).

**See also:** [EduClaw_Concepts_Explained.md](EduClaw_Concepts_Explained.md) (subsystem 13), [DEVELOPERS.md](DEVELOPERS.md) (WebSocket + CLI), [AUTOCOURSE.md](AUTOCOURSE.md) (separate `mode: autocourse` path for full lectures; you can feed lecture text to `type: tts` from the client).

## Why it exists

- **Offline / air-gapped labs**: cache models once, then set `HF_HUB_OFFLINE=1` for Hugging Face Hub.
- **Small footprint**: Kitten ships int8 and small-parameter checkpoints suitable for laptops and edge boxes.
- **Modularity**: swap backends via profile or register your own via entry points.

## Quick enable (Kitten, CPU)

1. **Install the wheel and extras** (Kitten publishes wheels on GitHub Releases, not only PyPI):

   ```bash
   pip install 'educlaw[tts-kitten]'
   ```

   The `tts-kitten` extra pins the official wheel URL from [KittenTTS releases](https://github.com/KittenML/KittenTTS/releases).

2. **Pre-download a model** (first run may hit the Hub; set `HF_HOME` / cache dir as you prefer):

   ```bash
   python -c "from kittentts import KittenTTS; KittenTTS('KittenML/kitten-tts-nano-0.8-int8', cache_dir=str(__import__('pathlib').Path.home()/'.educlaw/tts'))"
   ```

3. **Profile** (`profiles/local.toml` under `[educlaw]`):

   ```toml
   tts_enabled = true
   tts_backend = "kitten"
   tts_model_id = "KittenML/kitten-tts-nano-0.8-int8"
   tts_voice = "Jasper"
   tts_speed = 1.0
   ```

   **`tts_model_id` is required** when `tts_backend = "kitten"` — there is no baked-in default model id.

4. **Air-gapped use**: after the model is cached under `tts_cache_dir` (default `data_dir/tts`), export:

   ```bash
   export HF_HUB_OFFLINE=1
   ```

## WebSocket protocol

After the normal `connect` frame, send:

```json
{"type": "tts", "text": "Hello from EduClaw.", "voice": "Jasper", "speed": 1.0, "idempotency_key": "optional"}
```

Responses (in order):

- `{"type":"tts_event","payload":{"kind":"audio","format":"wav","sample_rate":24000,"voice":"Jasper","bytes_b64":"..."}}`
- `{"type":"tts_event","payload":{"kind":"done"}}`

Errors use `payload.kind` of `error` and `payload.message`. If `tts_enabled` is false, you get `TTS disabled`. Blocked input follows the same Shield policy as chat/autocourse.

## CLI

| Command | Purpose |
|--------|---------|
| `educlaw tts list` | List registered backend names; if `tts_enabled`, build the active backend and print `available_voices`. |
| `educlaw tts say "Your text" -o out.wav` | Synthesize to a WAV file (requires `tts_enabled` and a working backend). |

## Tuning knobs (`Settings` / env `EDUCLAW_*`)

| Field | Meaning |
|--------|---------|
| `tts_enabled` | Master switch; when false, gateway exposes no synthesizer (`deps.tts` is `None`). |
| `tts_backend` | Registry key: `kitten`, `null` (silent stub for tests), or a custom entry-point name. |
| `tts_model_id` | **Required for `kitten`**: Hugging Face repo id, e.g. `KittenML/kitten-tts-nano-0.8-int8`. |
| `tts_voice` | Default voice if the client omits `voice` on the WS frame. |
| `tts_speed` | Default speed multiplier. |
| `tts_sample_rate` | Hint for the `null` backend; Kitten emits 24 kHz PCM internally. |
| `tts_cache_dir` | Model cache directory (default `data_dir/tts`). |

### Kitten model sizes (reference)

| Model | Params | Approx. size |
|--------|--------|----------------|
| kitten-tts-nano-0.8-int8 | 15M | ~25 MB |
| kitten-tts-nano-0.8 | 15M | ~56 MB |
| kitten-tts-micro-0.8 | 40M | ~41 MB |
| kitten-tts-mini-0.8 | 80M | ~80 MB |

See the upstream [KittenTTS README](https://github.com/KittenML/KittenTTS) for updates.

## Adding a custom backend

1. Implement `TTSBackend` from `educlaw.tts.contract` (`name`, `available_voices`, async `synthesize`, async `close`).
2. Expose a factory `def factory(settings: Settings) -> TTSBackend: ...`
3. Register either:
   - **In-process**: `from educlaw.tts.registry import register` then `register("mytts", factory)` before `build_backend` runs, or
   - **Packaged**: in your `pyproject.toml`:

     ```toml
     [project.entry-points."educlaw.tts"]
     mytts = "my_package.tts:factory"
     ```

Entry-point names override built-ins with the same key.

## Troubleshooting

- **`ImportError: kittentts`**: install `educlaw[tts-kitten]` (includes the GitHub wheel).
- **`RuntimeError: Unknown TTS backend`**: typo in `tts_backend` — run `educlaw tts list` for keys.
- **`tts_model_id` unset** with `kitten`: set a Hub repo id in the profile.
- **Voice not found**: use a name from `available_voices` (Kitten ships Bella, Jasper, Luna, Bruno, Rosie, Hugo, Kiki, Leo by default).
- **Hub timeouts offline**: ensure the model is cached and `HF_HUB_OFFLINE=1` only after a successful download.
