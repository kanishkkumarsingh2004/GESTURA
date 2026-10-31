# Engineering Rules & Development Standards
# Real-Time Gesture Recognition and Audio Assistant

**Project:** Gesture Recognition and Audio Assistant  
**Version:** 1.0.0  
**Document Type:** Mandatory Engineering Standards  
**Framework:** Streamlit  
**ML Framework:** PyTorch  
**Computer Vision:** OpenCV  
**Environment Manager:** uv  
**Virtual Environment:** `venv/`

---

# 1. Purpose and Authority

This document defines mandatory engineering rules for every developer, contributor, automated tool, and AI coding agent working on this project.

Every implementation must comply with:

- Product requirements defined in `PRD.md`.
- System architecture defined in `architecture.md`.
- Engineering standards defined in this document.
- Security requirements defined in `security.md`, when available.

These documents must be treated as project-level specifications.

When requirements conflict:

1. Security requirements take priority for security-related decisions.
2. Explicit product requirements determine intended functionality.
3. Architecture requirements determine system boundaries.
4. Engineering rules determine implementation standards.

If a requirement is ambiguous or contradictory, document the conflict before making an architectural change.

Do not silently invent requirements.

# 2. Core Engineering Principles

Every implementation must follow these principles.

## 2.1 Code Quality

- Write clean, readable and maintainable code.
- Prefer explicit implementations over unnecessarily clever solutions.
- Use meaningful variable, function and class names.
- Apply type hints to public functions and important interfaces.
- Write docstrings for complex or reusable functionality.
- Avoid duplicate implementations.
- Avoid deeply nested conditional logic.
- Keep functions focused on one responsibility.
- Handle errors explicitly.
- Never suppress errors without a documented reason.

## 2.2 Modularity

- Maintain strict separation between application layers.
- Do not combine training, testing, inference and UI implementations.
- Reuse existing modules before creating new ones.
- Keep shared functionality in appropriate utility modules.
- Avoid circular imports.
- Do not create unnecessary abstraction layers.
- Keep dependencies between modules explicit.

## 2.3 Simplicity

- Do not introduce unnecessary frameworks.
- Do not add dependencies without a concrete requirement.
- Do not create generic factories for one implementation.
- Do not introduce unnecessary design patterns.
- Avoid premature optimization.
- Prefer the simplest implementation that satisfies the requirement correctly.

# 3. Mandatory Project Structure Rules

The project must follow the directory structure defined in `architecture.md`.

## 3.1 Directory Responsibilities

| Directory | Allowed responsibility |
|---|---|
| `pages/` | Streamlit page implementations |
| `components/` | Reusable UI components |
| `train/` | Training pipeline |
| `test/` | Automated testing |
| `model/` | Model architecture and inference |
| `server/` | Application services and stream coordination |
| `data/` | Dataset handling and dataset metadata |
| `utils/` | Shared utilities |
| `assets/` | Static assets |
| `outputs/` | Generated artifacts |
| `scripts/` | Executable utility scripts |
| `docs/` | Technical documentation |

## 3.2 File Placement Rules

- Never place model architecture code inside `app.py`.
- Never place training loops inside Streamlit pages.
- Never place camera-processing implementations inside UI components.
- Never put dataset loading logic inside model architecture files.
- Never store application secrets inside source code.
- Never create multiple files implementing the same responsibility.
- Never create files merely to make the directory structure appear more complex.

Before creating a new file, inspect the existing project structure and determine whether an existing module should be extended.

# 4. Python Coding Standards

## 4.1 Python Version

- Use the Python version pinned in `.python-version`.
- Do not introduce syntax incompatible with the pinned version.
- Keep dependencies compatible with the selected Python version.

## 4.2 Naming Conventions

Follow standard Python naming conventions.

| Element | Convention | Example |
|---|---|---|
| Variables | snake_case | `prediction_result` |
| Functions | snake_case | `load_model()` |
| Classes | PascalCase | `InferenceEngine` |
| Constants | UPPER_SNAKE_CASE | `CONFIDENCE_THRESHOLD` |
| Modules | snake_case | `model_loader.py` |

## 4.3 Type Hints

Use type hints for public interfaces.

Example:

```python
def predict(image: np.ndarray) -> PredictionResult:
    ...
```

Use appropriate data structures for complex outputs instead of returning unstructured dictionaries everywhere.

## 4.4 Function Design

Every function should:

- Have a clear purpose.
- Have predictable inputs.
- Have predictable outputs.
- Validate important inputs.
- Avoid unexpected side effects.
- Handle relevant exceptions.

Avoid functions that perform unrelated operations.

## 4.5 Error Handling

- Use specific exception types.
- Do not use bare `except`.
- Do not silently return fake predictions after failures.
- Preserve useful error information in logs.
- Present user-friendly messages at application boundaries.
- Never expose internal stack traces to ordinary users.

# 5. Environment and Dependency Management

**uv is mandatory.**

The project must use `uv` for dependency management and environment creation.

## 5.1 Environment Rules

The environment directory must be named:

`venv/`

Never create:

`.venv/`

Initialize the environment using:

```bash
uv venv venv
```

Activate using:

```bash
source venv/bin/activate
```

## 5.2 Dependency Rules

- Maintain dependencies in `pyproject.toml`.
- Maintain the dependency lockfile in `uv.lock`.
- Use `uv add` for normal dependencies.
- Use `uv add --dev` for development dependencies.
- Use `uv sync` to synchronize the environment.
- Do not manually modify installed packages inside `venv/`.
- Do not use `pip install` as the project's normal dependency-management workflow.
- Do not introduce an additional package manager.

Example:

```bash
uv add streamlit
uv add streamlit-webrtc
uv add opencv-python-headless
uv add numpy
uv add pillow
uv add torch torchvision
uv add pandas
uv add scikit-learn
uv add matplotlib
uv add pyyaml

uv add --dev pytest ruff mypy

uv lock
uv sync
```

Install PyTorch using a build compatible with the machine's supported CUDA environment.

Do not assume that the newest CUDA-enabled PyTorch build will work with every NVIDIA driver.

## 5.3 Dependency Changes

Before adding a dependency:

1. Check whether the functionality already exists in the project.
2. Check whether an existing dependency can provide it.
3. Check compatibility with the pinned Python version.
4. Check compatibility with PyTorch and OpenCV.
5. Document why the dependency is needed.

Never add a large framework to solve a problem that requires a small utility.

# 6. Streamlit Development Rules

## 6.1 UI Separation

- `app.py` must remain lightweight.
- Pages must contain presentation and orchestration logic.
- Reusable UI elements must live inside `components/`.
- Model inference must be delegated to the inference service.
- Camera processing must be delegated to the camera service.
- Audio processing must be delegated to the audio service.

## 6.2 Session State

Use Streamlit Session State for session-specific information.

Examples:

- Detection status.
- Audio preferences.
- Prediction history.
- Camera configuration.
- User interface preferences.

Rules:

- Initialize session values safely.
- Avoid accessing undefined session keys.
- Do not store per-user state in global variables.
- Do not share mutable prediction buffers between users.
- Clean up session resources when detection stops.

## 6.3 Caching

Use `st.cache_resource` for appropriate reusable resources, such as immutable model instances.

Use `st.cache_data` for suitable computed data.

Never cache:

- Mutable user prediction histories as shared data.
- User-specific camera state.
- Session-specific audio queues.
- Mutable prediction stabilization buffers.

A cached model must be safe for concurrent access.

## 6.4 UI Design

The application must maintain a consistent design system.

Design requirements:

- Dark visual theme.
- Electric blue accent.
- Consistent spacing.
- Reusable UI components.
- Responsive layout.
- Clear typography.
- Accessible contrast.
- Consistent button behavior.
- Clear loading and error states.

Do not:

- Overuse gradients.
- Add excessive animations.
- Use random colors across pages.
- Introduce inconsistent card styles.
- Hide essential information behind unnecessary interactions.
- Break responsive behavior with fragile CSS selectors.

## 6.5 Streamlit Reruns

- Avoid unnecessary application reruns.
- Avoid reinitializing expensive resources during reruns.
- Avoid blocking the main application thread.
- Use appropriate Streamlit fragments or other supported update mechanisms where beneficial.
- Keep UI updates independent of camera-processing callbacks.

# 7. Camera and OpenCV Rules

## 7.1 Camera Access

Use `streamlit-webrtc` for browser camera streaming.

Do not assume `cv2.VideoCapture(0)` accesses the visitor's browser camera.

`cv2.VideoCapture()` may be used for explicitly supported local-device workflows, testing or dataset collection.

## 7.2 Frame Processing

Every incoming frame must:

1. Be validated.
2. Be converted to the required color space.
3. Be processed using the shared preprocessing pipeline.
4. Be passed to inference when selected.
5. Be released or discarded when no longer needed.

## 7.3 Camera Callback Rules

Camera callbacks must:

- Remain lightweight.
- Avoid Streamlit rendering operations.
- Avoid blocking audio operations.
- Avoid model initialization.
- Avoid training operations.
- Avoid unlimited thread creation.
- Avoid uncontrolled memory allocation.

## 7.4 Frame Management

- Keep frame buffers bounded.
- Avoid unnecessary image copies.
- Skip stale frames when processing falls behind.
- Measure actual processing FPS.
- Avoid pretending that camera FPS equals inference FPS.

## 7.5 Camera Lifecycle

Camera resources must be explicitly managed.

When detection stops:

- Stop processing new frames.
- Stop the WebRTC stream.
- Release associated resources.
- Clear session-specific transient buffers.
- Prevent background workers from continuing unnecessarily.

# 8. Machine Learning Rules

## 8.1 Model Architecture

All model architecture definitions must remain inside `model/`.

Rules:

- Use PyTorch.
- Keep architecture definitions independent of Streamlit.
- Support configurable output classes.
- Support configurable input dimensions.
- Support CPU execution.
- Support CUDA execution when available.
- Use reusable model initialization functions.
- Keep architecture changes backward-compatible where possible.

Do not hardcode the number of output classes in multiple modules.

## 8.2 Model Selection

The initial model may use VGG16.

However:

- Do not assume VGG16 is optimal.
- Benchmark MobileNetV3 where appropriate.
- Compare accuracy, model size, memory and inference latency.
- Base architecture decisions on actual experiments.

## 8.3 Training and Inference Separation

Training and inference must remain independent.

Mandatory rules:

- Never train during application startup.
- Never train during live camera detection.
- Never modify model weights during normal inference.
- Never run a training loop from a Streamlit page.
- Never load training datasets unnecessarily into the inference process.
- Never allow one session to change the shared model parameters.

## 8.4 Inference

All inference must:

- Use `model.eval()`.
- Use `torch.inference_mode()`.
- Validate tensor dimensions.
- Validate model input compatibility.
- Use consistent preprocessing.
- Return structured prediction results.
- Handle inference failures explicitly.

## 8.5 Device Management

Device selection must be centralized.

Use automatic CUDA detection with CPU fallback.

Never assume that CUDA availability is guaranteed.

Never hardcode a GPU device index without configuration or validation.

Do not repeatedly move the model between CPU and GPU during normal inference.

## 8.6 Checkpoint Management

- Save checkpoints outside source-code files.
- Preserve the best validation checkpoint.
- Preserve the latest training checkpoint when needed.
- Store architecture metadata.
- Store class mappings.
- Store preprocessing configuration.
- Validate checkpoint compatibility before loading.
- Do not overwrite a known-good checkpoint without a recovery path.

Prefer state-dictionary-based checkpoint loading and safe deserialization.

Never load untrusted model checkpoints.

# 9. Dataset Engineering Rules

## 9.1 Raw Dataset Protection

Raw datasets are immutable source data.

- Never overwrite original images.
- Never modify original labels without an explicit dataset correction.
- Never delete raw data as part of preprocessing.
- Never silently discard invalid images.
- Record dataset validation failures.

## 9.2 Dataset Splitting

Dataset splits must prevent leakage.

Do not randomly distribute near-identical frames from the same recording across training and testing.

Use appropriate participant-level or recording-session-level splitting.

## 9.3 Label Management

- Maintain one centralized class mapping.
- Validate class labels.
- Reject unsupported labels.
- Keep class IDs stable for each model version.
- Never reorder class mappings without updating model metadata.

## 9.4 Data Augmentation

Only apply augmentations that preserve gesture semantics.

Horizontal flipping must be evaluated carefully because some gestures may be direction-sensitive.

Do not introduce transformations that produce misleading training samples.

## 9.5 Dataset Quality

Every training run must record:

- Dataset version.
- Number of images.
- Number of samples per class.
- Dataset split.
- Preprocessing configuration.
- Augmentation configuration.

Never fabricate dataset statistics.

# 10. Training Rules

## 10.1 Training Pipeline

Training must follow a predictable workflow:

1. Load configuration.
2. Validate dataset.
3. Initialize reproducibility settings.
4. Load datasets.
5. Initialize DataLoaders.
6. Initialize model.
7. Initialize loss function.
8. Initialize optimizer.
9. Initialize scheduler.
10. Train.
11. Validate.
12. Save checkpoints.
13. Evaluate.
14. Record results.

## 10.2 Reproducibility

Set and record random seeds where supported.

Record:

- Python version.
- PyTorch version.
- CUDA version.
- GPU model.
- Dataset version.
- Configuration.
- Random seed.
- Training duration.

Do not claim perfect determinism unless the selected operations and hardware support it.

## 10.3 Training Metrics

Record actual:

- Training loss.
- Validation loss.
- Training accuracy.
- Validation accuracy.
- Learning rate.
- Epoch duration.

Never generate synthetic metrics to make a training report appear complete.

## 10.4 Checkpoint Rules

- Save checkpoints at controlled intervals.
- Save the best validation checkpoint.
- Preserve enough optimizer and scheduler state for resuming training.
- Validate checkpoint integrity.
- Never overwrite the only working checkpoint before verifying its replacement.

# 11. Model Evaluation Rules

The test dataset must remain separate from training and model selection.

Mandatory evaluation metrics:

- Accuracy.
- Precision.
- Recall.
- F1-score.
- Confusion matrix.
- Per-class performance.
- Inference latency.

Rules:

1. Evaluate using the saved checkpoint.
2. Use the same preprocessing expected by the model.
3. Record the evaluated checkpoint version.
4. Never use test results to repeatedly tune the model.
5. Never report training accuracy as test accuracy.
6. Never fabricate performance values.
7. Investigate poor-performing classes.
8. Record hardware when reporting latency.

A model must not be considered production-ready based on accuracy alone.

# 12. Prediction Stabilization Rules

The application must not announce every individual frame prediction.

Implement:

- Confidence threshold.
- Consecutive-frame confirmation.
- Prediction smoothing.
- Cooldown.
- Duplicate suppression.
- Unknown gesture handling.
- Re-arm conditions.

Rules:

- Do not announce unsupported gestures.
- Do not announce predictions below the configured threshold.
- Do not repeatedly announce a held gesture.
- Do not allow stale predictions to remain active indefinitely.
- Reset session-specific state appropriately when detection stops.

A high softmax score must not automatically be interpreted as proof that an unfamiliar gesture belongs to a known class.

# 13. Audio Engineering Rules

## 13.1 Audio Execution

Audio playback must occur on the browser side.

Do not use blocking Python playback inside the camera-processing pipeline.

## 13.2 Audio Queue

The queue must be:

- Bounded.
- Session-specific.
- Duplicate-aware.
- Safely managed.
- Able to handle playback failures.

## 13.3 Duplicate Prevention

A stable prediction must be announced once according to the configured re-arm and cooldown policy.

Do not repeatedly play the same phrase while the gesture remains unchanged.

## 13.4 Browser Compatibility

- Provide explicit audio activation.
- Handle autoplay restrictions.
- Provide mute controls.
- Handle unavailable speech synthesis.
- Never assume that every browser provides identical voices.

The application must remain functional when audio is disabled.

# 14. Server and Concurrency Rules

## 14.1 Shared Resources

Shared model resources must be treated as read-only during inference.

Session-specific state must never be stored in a shared singleton.

## 14.2 Thread Safety

- Use explicit synchronization where required.
- Avoid uncontrolled shared mutable objects.
- Avoid creating a thread per frame.
- Bound background workers.
- Handle worker shutdown.
- Avoid deadlocks.
- Avoid blocking the Streamlit application thread.

## 14.3 Queue Management

Every queue must have a defined capacity.

When a camera queue becomes full, stale frames should generally be discarded rather than allowing latency to grow indefinitely.

Audio events require different handling because dropping confirmed spoken predictions may affect usability. Their queue policy must be explicitly defined.

## 14.4 Failure Recovery

A failed camera connection must not leave background processing running indefinitely.

An inference error must not generate a false prediction.

A failed audio request must not stop camera processing.

# 15. Security and Privacy Rules

These rules are mandatory.

- Never commit credentials.
- Never expose secret keys.
- Never store camera recordings without explicit permission.
- Never upload camera frames automatically.
- Never expose internal error traces to users.
- Never load untrusted model checkpoints.
- Validate uploaded files.
- Restrict filesystem access.
- Validate configuration inputs.
- Use HTTPS for remote deployment.
- Configure WebRTC connectivity securely.
- Keep user sessions isolated.
- Avoid logging personally identifiable information.
- Do not expose private prediction histories across sessions.

All future security-specific controls must be documented in `security.md`.

# 16. Logging Rules

Use centralized logging.

Log:

- Application startup.
- Model initialization.
- Checkpoint validation.
- Camera lifecycle events.
- Inference failures.
- Processing latency.
- Audio failures.
- Training progress.
- Evaluation results.

Do not:

- Log every camera frame.
- Log complete raw image data.
- Log sensitive information.
- Use print statements as the permanent logging mechanism.
- Suppress critical exceptions.

Use appropriate logging levels:

| Level | Usage |
|---|---|
| DEBUG | Detailed development diagnostics |
| INFO | Normal application events |
| WARNING | Recoverable unexpected conditions |
| ERROR | Failed operations |
| CRITICAL | Application-level critical failures |

# 17. Testing Rules

Every major feature must be tested.

## 17.1 Testing Requirements

- Write unit tests for reusable functions.
- Write integration tests for subsystem boundaries.
- Test invalid inputs.
- Test expected failures.
- Test model loading.
- Test checkpoint compatibility.
- Test preprocessing consistency.
- Test prediction stabilization.
- Test session isolation.
- Test camera lifecycle.
- Test audio failure handling.

## 17.2 Test Isolation

Automated tests must not depend unnecessarily on:

- Physical camera hardware.
- External network access.
- A running browser.
- A production dataset.
- A physical audio device.
- A CUDA-enabled GPU.

Use synthetic inputs, fixtures and mocks when appropriate.

## 17.3 Test Integrity

Never:

- Delete failing tests to make a build pass.
- Skip tests without justification.
- Mock the behavior being tested in a way that makes the test meaningless.
- Claim that tests passed without executing them.
- Hide test failures.

Every reported test result must reflect an actual execution.

# 18. Performance Rules

Performance must be measured rather than assumed.

Measure:

- Model initialization time.
- Model inference time.
- Camera-to-prediction latency.
- Effective inference FPS.
- Camera processing FPS.
- GPU memory.
- CPU memory.
- Long-running session stability.

Rules:

- Avoid repeated model loading.
- Avoid unnecessary preprocessing.
- Avoid redundant tensor copies.
- Avoid unbounded queues.
- Avoid excessive Streamlit reruns.
- Avoid repeated disk operations during inference.
- Do not optimize code without identifying the actual bottleneck.

The application must not report camera FPS as model inference FPS.

# 19. Documentation Rules

All major modules must have clear documentation.

Maintain:

- `README.md`
- `PRD.md`
- `architecture.md`
- `rules.md`
- `security.md`
- `docs/dataset.md`
- `docs/training.md`
- `docs/deployment.md`

Whenever architecture changes:

1. Identify affected documents.
2. Update the relevant documentation.
3. Ensure implementation and documentation agree.
4. Record important compatibility changes.

Never leave outdated documentation that contradicts actual behavior.

# 20. Git and Version Control Rules

## 20.1 Git Hygiene

Never commit:

- `venv/`
- Python cache directories.
- Temporary files.
- Unnecessary camera recordings.
- Private datasets without authorization.
- Credentials.
- Unnecessary large generated artifacts.
- Local environment configuration containing secrets.

## 20.2 Commit Messages

Use meaningful commit messages.

Examples:

```text
feat: implement live gesture inference
fix: resolve camera stream lifecycle issue
refactor: separate prediction stabilization
test: add inference pipeline tests
docs: update model architecture documentation
perf: optimize frame preprocessing
```

## 20.3 Changes

- Keep commits logically focused.
- Avoid unrelated modifications.
- Review the final diff.
- Do not overwrite unrelated user changes.
- Do not delete working implementations without verifying dependencies.

# 21. AI Coding Agent Rules

These rules apply to every AI agent contributing to this repository.

## 21.1 Before Making Changes

The agent must:

1. Inspect the repository.
2. Read `PRD.md`.
3. Read `architecture.md`.
4. Read `rules.md`.
5. Read `security.md` when present.
6. Inspect relevant source files.
7. Identify existing implementations.
8. Understand dependencies and call relationships.
9. Identify affected tests.
10. Plan the implementation.

The agent must not start generating code based only on a short feature description when the existing project structure is available.

## 21.2 Skills Management

If the repository contains `skills-lock.json`, it is the authoritative manifest for project-specific skills.

Mandatory rules:

- Inspect `skills-lock.json` before skill-related work.
- Use the exact locked skill versions and sources.
- Follow the relevant skill instructions.
- Do not silently substitute a different skill.
- Do not assume a skill exists merely because its name appears in a prompt.
- Do not execute untrusted skill code without appropriate inspection.
- Never modify the lockfile simply to bypass a missing or incompatible skill.
- Report missing, invalid or incompatible skills.
- Preserve reproducibility of skill-related workflows.

If no relevant skill is locked, use the project's documented engineering standards and report the absence when the task specifically requires a skill.

## 21.3 Implementation Rules

AI agents must:

- Inspect before modifying.
- Reuse existing code where appropriate.
- Follow the defined architecture.
- Keep changes limited to the requested scope.
- Use existing project conventions.
- Add or update tests.
- Update documentation where necessary.
- Validate imports and dependency changes.
- Preserve existing working behavior.

AI agents must never:

- Invent nonexistent modules.
- Assume APIs exist without checking.
- Replace an entire subsystem unnecessarily.
- Introduce redundant abstractions.
- Fabricate test output.
- Fabricate model metrics.
- Hide incomplete implementation behind placeholder success messages.
- Claim functionality is complete when only a mock implementation exists.

## 21.4 Completion Report

Every completed implementation task must report:

1. What was implemented.
2. Files created.
3. Files modified.
4. Dependencies added or changed.
5. Tests executed.
6. Actual test results.
7. Known limitations.
8. Remaining tasks.

If something could not be tested, explicitly state why.

# 22. Forbidden Engineering Practices

The following practices are prohibited.

| Practice | Status |
|---|---|
| Training inside Streamlit startup | Prohibited |
| Model loading on every frame | Prohibited |
| Global mutable prediction state | Prohibited |
| Blocking audio in camera callbacks | Prohibited |
| Unlimited frame queues | Prohibited |
| Hardcoded secrets | Prohibited |
| Fabricated ML metrics | Prohibited |
| Silent exception suppression | Prohibited |
| Dataset leakage | Prohibited |
| Duplicate class mappings | Prohibited |
| Unnecessary dependencies | Prohibited |
| Unverified checkpoint loading | Prohibited |
| Fake successful test reports | Prohibited |
| Uncontrolled thread creation | Prohibited |
| Committing `venv/` | Prohibited |
| Unreviewed architecture changes | Prohibited |

# 23. Definition of Engineering Completion

A task is not complete merely because code has been written.

A task is complete only when:

- [ ] Requirements have been understood.
- [ ] Existing architecture has been respected.
- [ ] Implementation is functional.
- [ ] Inputs are validated.
- [ ] Errors are handled.
- [ ] Relevant tests have been added or updated.
- [ ] Relevant tests have been executed.
- [ ] No unrelated functionality has been broken.
- [ ] Documentation has been updated where required.
- [ ] Dependencies are synchronized.
- [ ] Changes have been reviewed.
- [ ] Known limitations have been disclosed.

# 24. Final Engineering Standard

The project must be developed as a professional machine-learning application, not as a collection of scripts connected together.

Every implementation must prioritize:

1. Correctness over speed of implementation.
2. Reliability over unnecessary complexity.
3. Reproducibility over undocumented experimentation.
4. Security over convenience.
5. Maintainability over code volume.
6. Measured performance over assumptions.
7. Real functionality over visual demonstrations.
8. Explicit architecture over hidden dependencies.

**Final Rule:**

Do not introduce code, dependencies, architecture, abstractions or functionality unless there is a clear technical reason for doing so.

Every change must improve the correctness, reliability, maintainability, security or functionality of the project.