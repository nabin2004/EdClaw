# Manim SFT Curriculum

Build a structured Manim API knowledge base, then generate supervised fine-tuning (SFT) examples in JSONL format (`instruction` + `output` per line). The curriculum has three pillars: **Memorization**, **Comprehension**, and **Self-Reflection**.

## Data source

All task scripts read `output/manim_kb.json`, built from live Manim introspection. For each export in `data['exports'][class_name]`:

- `kind`: `'class'`, `'function'`, etc.
- `doc`: `{'summary': ..., 'full': ...}`
- `bases`: list of direct base class names
- `methods`: list of method dicts (`name`, `parameters`, `doc`, ...)
- `constructor`: dict with `parameters` (like a method)

Class-level tasks filter to `kind == 'class'` (~256 classes).

## How to run

```bash
python main.py                        # build manim_kb.json
python main.py --verbose              # detailed console tree
python main.py --output-dir out       # custom output folder

python task1.py                       # Pillar A: memorization only
python task2n3.py                     # Pillars B + C + full combined curriculum
```

## Output files

| File | Source | Contents |
|------|--------|----------|
| `output/manim_kb.json` | `main.py` | Structured Manim API knowledge base |
| `output/sft_memorise.jsonl` | `task1.py` | Pillar A — Memorization |
| `output/sft_comprehension.jsonl` | `task2n3.py` | Pillar B — Comprehension |
| `output/sft_self_reflection.jsonl` | `task2n3.py` | Pillar C — Self-Reflection |
| `output/manim_curriculum.jsonl` | `task2n3.py` | All three pillars combined |

---

## Pillar A: Memorization (`task1.py`)

**Goal:** Teach the model to recall exact API facts — docstrings, inheritance, constructor signatures, and method signatures.

### Sample outputs

1. Raw docstring memorization:
```json
{"instruction": "Read and memorize the full documentation for the `Mobject` class in Manim.", "output": "A mobject is a virtual object that can be displayed on screen. ... (full docstring here)"}
```

2. Inheritance memorization:
```json
{"instruction": "List all the direct base (super) classes of the `Mobject` class.", "output": "object"}
```

3. Constructor signature memorization:
```json
{"instruction": "Memorize the exact constructor signature for the `Mobject` class.", "output": "Mobject(self, color: ParsableManimColor = None, name: str = None, **kwargs)"}
```

4. Method signature flashcard (e.g., `set_z_index`):
```json
{"instruction": "Memorize the exact signature for the `set_z_index` method of the `Mobject` class.", "output": "set_z_index(self, z_index_value: float, family: bool = True)"}
```

5. Method name flashcard (no parameters, e.g., `get_center`):
```json
{"instruction": "What is the exact method name for `get_center` in the `Mobject` class? (No parameters)", "output": "get_center"}
```

### Expected scale

- 256 classes; Mobject alone has 245 methods in the KB.
- Rough estimate: 256 docstrings + 256 inheritance + 256 constructors + ~2,000 methods ≈ ~2,700 tasks.
- Actual count is higher (~39k) because each subclass's `methods` list includes inherited methods.

---

## Pillar B: Comprehension (`task2n3.py`)

**Goal:** Teach the model to understand what classes do, their relationships, and to infer facts from documentation.

### 1. Summarization

- **Prompt:** `Summarize the purpose of the class `{name}` in Manim in one concise sentence.`
- **Output:** `doc['summary']` (or `doc['full']`), truncated to 300 chars.

```json
{"instruction": "Summarize the purpose of the class `Circle` in Manim in one concise sentence.", "output": "A circle."}
```

### 2. Gist identification

- **Prompt:** `List the main methods of the class `{name}`.`
- **Output:** First 5 public method names (heuristic, comma-separated).

```json
{"instruction": "List the main methods of the class `Circle`.", "output": "add, add_animation_override, add_background_rectangle, add_updater, align_data"}
```

### 3. Natural language inference (inheritance)

- **Prompt:** `Based on the Manim API, is it true that `{name}` inherits from `{base}`? Answer Yes or No.`
- **Output:** `"Yes"` for each direct base; up to 2 `"No"` examples per class (random non-base classes).

```json
{"instruction": "Based on the Manim API, is it true that `Mobject` inherits from `object`? Answer Yes or No.", "output": "Yes"}
```

### Expected scale

~256 summarization + ~256 gist + ~512 NLI (2 per class) ≈ **~1,024 tasks**.

---

## Pillar C: Self-Reflection (`task2n3.py`)

**Goal:** Teach the model to identify gaps, correct errors, and explain concepts (Feynman-style).

### 1. Fill-in-the-blank

- **Prompt:** `Complete the constructor: `{name}({param} = ____)`` or `Complete the call: `{name}.{method}({param} = ____)``
- **Output:** The parameter's default value from the KB.

```json
{"instruction": "Complete the constructor: `Circle(radius = ____)`", "output": "1.0"}
```

### 2. Multi-choice

- **Prompt:** `Which of the following is a valid method of the class `{cls}`? Options: ...`
- **Output:** The correct method name (1 correct + 2 distractors from other classes).

```json
{"instruction": "Which of the following is a valid method of the class `Circle`? Options: play, get_center, construct", "output": "get_center"}
```

### 3. Bug-fix

- **Prompt:** Describes a common Manim mistake.
- **Output:** Corrected code (hardcoded templates, not auto-generated).

```json
{"instruction": "Correct the following code that is supposed to rotate by 90 degrees, but it's missing a constant: `mobject.rotate(90)`", "output": "mobject.rotate(90 * DEGREES)"}
```

### 4. Teaching

- **Prompt:** `Teach a beginner about the `{name}` class. Explain what it does and how to use it in a few sentences.`
- **Output:** `doc['summary']` truncated to 300 chars.

```json
{"instruction": "Teach a beginner about the `Scene` class. Explain what it does and how to use it in a few sentences.", "output": "A Scene is the canvas of your animation."}
```

### Expected scale

~500 fill-blank + ~200 multi-choice + 2 bug-fix + ~256 teaching ≈ **~1,000+ tasks** (fill-blank can be larger due to per-method defaults).

---

## Design decisions

- All tasks use the same JSONL format: `{"instruction": "...", "output": "..."}`.
- Only `kind == "class"` exports are used for class-level tasks.
- `random.seed(42)` in `task2n3.py` for reproducible NLI negatives and multi-choice shuffling.
- Summarization and teaching outputs are truncated to 300 characters.
- Gist uses the first 5 public method names (not semantic importance ranking).
- Bug-fix tasks use fixed Manim mistake templates (`rotate` / `DEGREES`, `fill_color` vs `color`).
- NLI negatives sample up to 2 random classes that are not direct bases.
- Multi-choice distractors are method names from other classes to reinforce class boundaries.
- `manim_curriculum.jsonl` combines all three pillars for end-to-end fine-tuning.

## Total curriculum

| Pillar | Script | Approx. tasks |
|--------|--------|-----------------|
| Memorization | `task1.py` | ~39,000 (with inherited methods) |
| Comprehension | `task2n3.py` | ~1,024 |
| Self-Reflection | `task2n3.py` | ~1,000+ |
| **Combined** | `task2n3.py` → `manim_curriculum.jsonl` | sum of all three |
