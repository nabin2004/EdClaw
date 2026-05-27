# IR schema sources

Manimator keeps its canonical IR schemas in manimator/contracts/ (Pydantic models with validators).

## Core IR

- Intent (manimator/contracts/intent.py)
  - ConceptType (enum)
  - Modality (enum)
  - IntentClassificationPayload (LLM output schema)
  - IntentResult (IR schema)

- Scene plan (manimator/contracts/scene_plan.py)
  - SceneClass (enum)
  - Budget (enum)
  - TransitionStyle (enum)
  - SceneEntry (IR schema)
  - ScenePlan (IR schema; schema_version="1.0.0")

- Scene spec (manimator/contracts/scene_spec.py)
  - MobjectSpec
  - AnimationSpec
  - CameraOp
  - SceneSpec (IR schema; schema_version="1.0.0")
  - MANIM_CLASS_WHITELIST (safety allowlist used by validators)

- Validation (manimator/contracts/validation.py)
  - ErrorType (enum)
  - ValidationResult (IR schema; schema_version="1.0.0")

- Critic (manimator/contracts/critic.py)
  - CriticResult (IR schema; schema_version="1.0.0")
  - MAX_REPLANS, DEFAULT_THRESHOLD (pipeline control constants)

## LLM-output schemas (pre-domain mapping)

LLMs often emit extra fields and partial shapes. We first parse LLM outputs into permissive models and then map them into the strict, versioned IR.

- manimator/contracts/llm_outputs.py
  - LLMScenePlanPayload, LLMSceneEntryPayload (scene decomposer output)
  - LLMPlannerPayload, LLMObjectSpec, LLMAnimationSpec, LLMCameraOp (scene planner output)

## Why this separation

- Keep strict IR stable and versioned.
- Accept richer/extra fields from LLMs without widening domain contracts.

