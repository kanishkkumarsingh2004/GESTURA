# Product Requirements Document (PRD)
# Real-Time Gesture Recognition and Audio Assistant

**Project Type:** AI / Machine Learning / Computer Vision  
**Application:** Streamlit Web Application  
**Machine Learning Framework:** PyTorch  
**Computer Vision:** OpenCV  
**Environment Manager:** uv  
**Python Environment:** `venv/`  
**Application Architecture:** Modular, component-based, ML pipeline separation  
**Version:** 1.0.0

---

# 1. Project Overview

## 1.1 Introduction

The project is a real-time hand gesture recognition and audio assistant built using Python, PyTorch, OpenCV and Streamlit.

The application will access the user's camera, continuously capture video frames, process the frames using computer vision techniques, and pass the processed images into a trained PyTorch model.

The model will identify the hand gesture and generate a corresponding prediction.

The application will also provide live audio output, allowing recognized gestures to be converted into spoken words.

The primary objective is to create a responsive, visually appealing and technically reliable gesture recognition system with an independent machine learning pipeline.

## 1.2 Core Objectives

1. Develop a complete PyTorch-based gesture recognition model.
2. Build an independent training and testing pipeline.
3. Implement real-time camera access through Streamlit.
4. Process camera frames using OpenCV.
5. Predict gestures continuously with confidence scores.
6. Convert stable predictions into audio output.
7. Provide a professional and interactive Streamlit interface.
8. Maintain modular and reusable Python components.
9. Support model checkpoints and reproducible training.
10. Make the system extensible for additional gestures and future models.

## 1.3 Initial Gesture Vocabulary

The initial model will support controlled gesture classification.

| Class | Predicted output |
|---|---|
| HELLO | Hello |
| YES | Yes |
| NO | No |
| THANK_YOU | Thank you |
| PLEASE | Please |
| STOP | Stop |
| HELP | Help |
| GOOD | Good |
| BAD | Bad |
| LOVE | Love |
| NONE | No recognized gesture |

The `NONE` class represents an unknown, invalid or unsupported gesture.

The application must not confidently classify arbitrary hand movements as one of the supported gestures.

---

# 2. Technology Stack

## 2.1 Core Technologies

| Technology | Responsibility |
|---|---|
| Python | Primary programming language |
| Streamlit | Web application and UI |
| PyTorch | Model development and training |
| Torchvision | Model architectures and image transformations |
| OpenCV | Image processing and frame manipulation |
| streamlit-webrtc | Browser camera streaming |
| NumPy | Numerical operations |
| Pillow | Image loading and processing |
| uv | Environment and dependency management |
| Pandas | Dataset metadata and evaluation |
| Matplotlib | Training and evaluation visualizations |
| Scikit-learn | Classification metrics |
| pytest | Automated testing |

## 2.2 Audio Technologies

Audio must work directly in the browser.

Requirements:

- Text-to-speech functionality.
- Gesture-specific spoken output.
- Audio playback controls.
- Playback queue.
- Duplicate audio prevention.
- Audio enable/disable settings.
- Adjustable playback volume where supported.

Use browser-native speech synthesis or a compatible audio component.

Do not block the video processing thread while audio is playing.

## 2.3 Environment Management

Use `uv` for all Python dependency and environment operations.

The environment directory must be named `venv`, not `.venv`.

Initial setup:

```bash
uv init --bare

uv python pin 3.11

uv venv venv

source venv/bin/activate

uv pip install -r requirements.txt
```

Dependencies must be maintained in `pyproject.toml` and locked using `uv.lock`.

Use the project's pinned Python version consistently.

The `venv/` directory must be excluded from Git.

---

# 3. Project Directory Structure

The project must follow a modular architecture.

```text
gesture-recognition/
│
├── app.py
├── requirements.txt
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── README.md
├── config.yaml
│
├── pages/
│   ├── 01_Dashboard.py
│   ├── 02_Live_Detection.py
│   ├── 03_Prediction_History.py
│   ├── 04_Model_Information.py
│   └── 05_Settings.py
│
├── components/
│   ├── __init__.py
│   ├── sidebar.py
│   ├── navbar.py
│   ├── cards.py
│   ├── charts.py
│   ├── camera_view.py
│   ├── prediction_view.py
│   └── audio_controls.py
│
├── train/
│   ├── __init__.py
│   ├── train.py
│   ├── trainer.py
│   ├── loss.py
│   ├── optimizer.py
│   ├── scheduler.py
│   └── callbacks.py
│
├── test/
│   ├── __init__.py
│   ├── test_model.py
│   ├── test_dataset.py
│   ├── test_inference.py
│   ├── test_preprocessing.py
│   └── test_camera.py
│
├── model/
│   ├── __init__.py
│   ├── architecture.py
│   ├── classifier.py
│   ├── model_loader.py
│   ├── inference.py
│   ├── checkpoint.py
│   ├── weights/
│   │   └── .gitkeep
│   └── exports/
│       └── .gitkeep
│
├── server/
│   ├── __init__.py
│   ├── camera_server.py
│   ├── stream_handler.py
│   ├── prediction_service.py
│   ├── audio_service.py
│   └── session_manager.py
│
├── data/
│   ├── raw/
│   │   ├── hello/
│   │   ├── yes/
│   │   ├── no/
│   │   ├── thank_you/
│   │   ├── please/
│   │   ├── stop/
│   │   ├── help/
│   │   ├── good/
│   │   ├── bad/
│   │   ├── love/
│   │   └── none/
│   │
│   ├── processed/
│   │
│   ├── splits/
│   │   ├── train.csv
│   │   ├── validation.csv
│   │   └── test.csv
│   │
│   └── dataset.py
│
├── utils/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── augmentation.py
│   ├── metrics.py
│   ├── visualization.py
│   ├── device.py
│   ├── logging.py
│   └── reproducibility.py
│
├── assets/
│   ├── images/
│   ├── icons/
│   └── audio/
│
├── outputs/
│   ├── checkpoints/
│   ├── logs/
│   ├── metrics/
│   ├── plots/
│   └── predictions/
│
├── scripts/
│   ├── collect_data.py
│   ├── preprocess_data.py
│   ├── evaluate.py
│   └── export_model.py
│
└── docs/
    ├── architecture.md
    ├── dataset.md
    ├── training.md
    └── deployment.md
```

## 3.1 Folder Responsibilities

### train/

Contains the complete model training pipeline.

Responsibilities:

- Loading the dataset.
- Training configuration.
- Forward and backward propagation.
- Loss calculation.
- Optimizer configuration.
- Learning-rate scheduling.
- Validation.
- Checkpoint generation.
- Training history.

### test/

Contains independent testing and validation modules.

Responsibilities:

- Model correctness.
- Dataset validation.
- Prediction accuracy.
- Preprocessing consistency.
- Camera pipeline validation.
- Inference testing.

### model/

Contains model architecture and inference-related components.

Responsibilities:

- PyTorch model architecture.
- Model initialization.
- Weight loading.
- Checkpoint management.
- Inference execution.
- Model metadata.

### server/

Contains the application-side processing services.

Responsibilities:

- Camera stream management.
- Frame processing coordination.
- Prediction orchestration.
- Audio processing.
- Session lifecycle management.

### data/

Contains all datasets and dataset metadata.

Raw datasets must never be overwritten by preprocessing operations.

### utils/

Contains shared utilities that can be reused across training, testing and inference.

### outputs/

Contains generated training artifacts, evaluation reports, model checkpoints and logs.

---

# 4. Machine Learning Requirements

## 4.1 Model Architecture

The machine learning implementation must use PyTorch.

The initial implementation should provide a configurable CNN classifier.

VGG16 should be supported as the initial architecture, with transfer learning from pretrained weights where appropriate.

The architecture must be implemented independently in:

`model/architecture.py`

Requirements:

- Configurable number of output classes.
- Configurable input dimensions.
- Transfer learning support.
- Replaceable classification head.
- CPU and CUDA execution support.
- Model parameter counting.
- Reproducible initialization.

The architecture should be modular so that MobileNetV3 or ResNet can be benchmarked later.

## 4.2 Image Input

Initial image configuration:

```yaml
image:
  width: 224
  height: 224
  channels: 3
  color_space: RGB
  normalization: imagenet
```

All camera frames and training images must undergo compatible preprocessing.

The preprocessing pipeline must handle:

- Resizing.
- Color conversion.
- Normalization.
- Tensor conversion.
- Invalid image handling.

## 4.3 Dataset Requirements

The dataset must contain images representing each supported gesture.

Dataset collection should account for:

- Different lighting conditions.
- Different backgrounds.
- Different hand orientations.
- Different users.
- Different camera distances.
- Different skin tones.
- Different hand sizes.
- Positive and negative examples.

Dataset splits must avoid leakage.

Images from the same recording session or individual should not be randomly distributed across training and testing if that would allow near-duplicate images to appear in both sets.

Recommended initial split:

| Dataset | Percentage |
|---|---:|
| Training | 70% |
| Validation | 15% |
| Testing | 15% |

These percentages are starting points, not guarantees of dataset quality.

## 4.4 Data Augmentation

Implement configurable augmentation:

- Random rotation.
- Random scaling.
- Horizontal flipping only where gesture semantics permit.
- Brightness variation.
- Contrast variation.
- Minor translation.
- Random cropping.

Do not apply transformations that change the meaning of a gesture.

## 4.5 Training Pipeline

The training pipeline must support:

1. Dataset loading.
2. Dataset validation.
3. Data augmentation.
4. Batch loading.
5. Model initialization.
6. Forward propagation.
7. Loss computation.
8. Backpropagation.
9. Optimizer updates.
10. Validation after each epoch.
11. Learning-rate scheduling.
12. Checkpoint saving.
13. Training metric logging.
14. Early stopping.

Configuration must be externalized.

Example:

```yaml
training:
  epochs: 50
  batch_size: 32
  learning_rate: 0.0001
  weight_decay: 0.0001
  optimizer: adamw
  loss: cross_entropy
  early_stopping: true
  patience: 8
  seed: 42

model:
  architecture: vgg16
  pretrained: true
  num_classes: 12

device:
  preference: auto
```

The number of classes must be generated from the actual class mapping rather than hardcoded independently in different modules.

## 4.6 Checkpoint Management

The training pipeline must save:

- Model weights.
- Optimizer state.
- Scheduler state.
- Epoch number.
- Best validation accuracy.
- Class mapping.
- Model configuration.
- Preprocessing configuration.

The best-performing validation checkpoint must be preserved independently from the latest checkpoint.

Use safe, explicit checkpoint-loading behavior.

---

# 5. Model Testing and Evaluation

The model must be evaluated independently of the Streamlit application.

## 5.1 Required Metrics

- Accuracy.
- Precision.
- Recall.
- F1-score.
- Per-class accuracy.
- Confusion matrix.
- Inference latency.

## 5.2 Evaluation Requirements

The testing pipeline must:

- Load the saved checkpoint.
- Reproduce training preprocessing.
- Evaluate the held-out test dataset.
- Generate classification reports.
- Generate confusion matrices.
- Record evaluation results.
- Identify frequently confused gestures.

The model must not be evaluated only on training accuracy.

## 5.3 Model Acceptance Criteria

Initial project targets:

| Metric | Target |
|---|---:|
| Validation accuracy | At least 90% |
| Test accuracy | At least 85% |
| Prediction confidence | Configurable |
| Model loading | Successful |
| CPU inference | Supported |
| CUDA inference | Supported when available |

These are development targets, not claims of achieved performance. A model must not be considered production-ready solely because it meets an accuracy threshold.

---

# 6. Real-Time Camera Detection

## 6.1 Camera Integration

The application must support live camera streaming.

Use:

- `streamlit-webrtc`
- OpenCV
- NumPy
- PyTorch inference service

The browser must request camera permission from the user.

The application must not assume that the server's local camera is the user's camera.

## 6.2 Camera Controls

The live detection interface must provide:

- Start camera.
- Stop camera.
- Camera status.
- Camera selection where supported.
- Live video preview.
- Camera error handling.
- FPS information.
- Detection status.

## 6.3 Frame Processing

Each incoming frame must follow this pipeline:

```text
Camera Frame
     |
     v
OpenCV Frame Capture
     |
     v
Color Space Conversion
     |
     v
Image Preprocessing
     |
     v
PyTorch Model
     |
     v
Class Probabilities
     |
     v
Confidence Validation
     |
     v
Prediction Stabilization
     |
     v
UI + Audio Output
```

The frame-processing pipeline must be independent of UI rendering.

## 6.4 Prediction Stabilization

Predictions must not be displayed as valid gestures based on a single unstable frame.

Implement:

- Confidence threshold.
- Consecutive-frame validation.
- Prediction smoothing.
- Minimum gesture persistence.
- Unknown gesture detection.
- Cooldown between identical predictions.

Example configuration:

```yaml
detection:
  confidence_threshold: 0.85
  confirmation_frames: 5
  cooldown_seconds: 1.5
  smoothing_window: 5
  unknown_class_enabled: true
```

These values must be configurable and calibrated against actual validation data.

---

# 7. Live Audio System

## 7.1 Audio Requirements

Every confirmed gesture must be mapped to a corresponding spoken phrase.

Example:

```text
Detected: HELLO
Output: Hello

Detected: THANK_YOU
Output: Thank you

Detected: HELP
Output: Help
```

## 7.2 Audio Processing Rules

The audio system must:

1. Receive confirmed predictions.
2. Check whether the prediction has already been announced.
3. Check cooldown restrictions.
4. Add eligible output to the playback queue.
5. Play the corresponding audio.
6. Prevent duplicate playback.
7. Continue video detection independently.

## 7.3 Audio Controls

Provide:

- Enable/disable audio.
- Mute.
- Replay latest prediction.
- Playback status.
- Voice selection where supported.
- Adjustable volume where supported.

Audio playback must run on the browser side.

The application must not repeatedly generate speech for every incoming camera frame.

---

# 8. Streamlit Application Requirements

## 8.1 General Design

The website must have a professional, modern and visually attractive interface.

The interface should resemble a dedicated AI computer-vision product rather than a default Streamlit demonstration.

Design direction:

- Dark theme.
- Deep navy/black background.
- Electric blue accent.
- Subtle gradients.
- Clean typography.
- Rounded cards.
- Minimal visual clutter.
- Smooth and restrained transitions.
- Clear visual hierarchy.

Use Streamlit-native components and custom CSS where appropriate.

Do not rely on excessive CSS hacks that break Streamlit's responsive layout or component functionality.

## 8.2 Dashboard

The dashboard should display:

- Application overview.
- Model status.
- Camera status.
- Total supported gestures.
- Current detection status.
- Recent predictions.
- Model accuracy from saved evaluation results.
- System information.
- Quick access to live detection.

The dashboard must not display fabricated performance metrics.

## 8.3 Live Detection Page

This is the primary application page.

It should contain:

**Camera Section**
- Large live camera preview.
- Start and stop controls.
- Camera connection status.
- Live FPS.

**Prediction Section**
- Current predicted gesture.
- Confidence percentage.
- Prediction label.
- Detection state.
- Prediction history.

**Audio Section**
- Audio enabled status.
- Mute and unmute.
- Latest spoken phrase.
- Replay control.

**Additional Information**
- Supported gesture classes.
- Detection threshold.
- Model information.

The camera preview must receive the highest visual priority.

## 8.4 Prediction History

Display:

- Predicted gesture.
- Confidence.
- Timestamp.
- Audio playback status.

History must be bounded to prevent unlimited memory consumption.

Provide an option to clear the session history.

## 8.5 Model Information

Display:

- Model architecture.
- Number of classes.
- Model version.
- Checkpoint status.
- Training epoch.
- Validation accuracy.
- Test accuracy.
- Model device.
- Input dimensions.
- Preprocessing information.

Only display information retrieved from actual model metadata and evaluation results.

## 8.6 Settings

Provide configuration for:

- Confidence threshold.
- Audio enable/disable.
- Prediction cooldown.
- Camera settings.
- Detection smoothing.
- Theme preferences.
- Prediction history management.

Invalid settings must be rejected safely.

---

# 9. Performance Requirements

The system should be optimized for continuous real-time execution.

Initial targets:

| Parameter | Target |
|---|---|
| Camera preview | Smooth continuous streaming |
| Prediction latency | Target under 150 ms |
| Model initialization | Load once per session/model lifecycle |
| Audio response | Begin shortly after confirmed prediction |
| Memory consumption | Stable during extended sessions |
| UI responsiveness | No blocking during inference |

Performance measurements must distinguish model inference latency from total camera-to-prediction latency.

The system must:

- Avoid reloading model weights on every frame.
- Avoid unnecessary tensor allocations.
- Use inference mode.
- Use GPU acceleration when available.
- Support CPU fallback.
- Avoid excessive Streamlit reruns.
- Prevent uncontrolled thread creation.
- Manage WebRTC stream lifecycle correctly.

The application should be benchmarked on the actual target hardware before making performance claims.

---

# 10. Application State and Session Management

Use Streamlit session state for UI-specific values.

Manage separately:

- Camera connection.
- Active detection status.
- Audio preferences.
- Latest prediction.
- Prediction history.
- Detection configuration.

The camera stream must be explicitly stopped when the user ends detection or disconnects.

Model instances should be cached appropriately, with device and model-version considerations.

Do not store mutable per-user state inside a globally shared model object.

---

# 11. Security and Privacy

The initial application should prioritize local execution.

Requirements:

- No camera recording by default.
- No automatic dataset uploads.
- No unnecessary external API calls.
- No hardcoded credentials.
- No public exposure of model files or sensitive logs.
- Safe model checkpoint loading.
- Controlled file access.
- Input validation.
- Clear camera permission behavior.
- Explicit session cleanup.

If deployment introduces remote users, use HTTPS and configure WebRTC connectivity securely.

Camera frames should be processed transiently unless the user explicitly enables data collection.

---

# 12. Logging and Monitoring

Implement structured logging.

Record:

- Application startup.
- Model loading.
- Model loading failures.
- Camera connection events.
- Prediction errors.
- Inference latency.
- Training progress.
- Evaluation results.

Do not log raw camera frames or sensitive user information.

Separate training logs from application logs.

---

# 13. Testing Requirements

Testing must cover the following layers.

## Unit Testing

- Model initialization.
- Dataset loading.
- Preprocessing.
- Prediction output.
- Checkpoint loading.
- Confidence calculation.
- Audio mapping.
- Prediction stabilization.

## Integration Testing

- Camera-to-inference pipeline.
- Inference-to-prediction pipeline.
- Prediction-to-audio pipeline.
- Model loading from checkpoint.
- Streamlit session lifecycle.

## Performance Testing

- CPU inference.
- GPU inference.
- Sustained camera streaming.
- Memory usage.
- Frame-processing latency.
- Long-running session stability.

## UI Testing

- Camera permission errors.
- Camera unavailable state.
- Model unavailable state.
- Audio disabled state.
- Responsive layout.
- Start/stop detection behavior.

---

# 14. Development Workflow

Development must follow this order.

### Phase 1: Project Initialization

- Create the project.
- Configure uv.
- Create `venv/`.
- Install dependencies.
- Create the directory structure.
- Configure logging and YAML configuration.

### Phase 2: Dataset Development

- Collect gesture images.
- Validate dataset structure.
- Generate class mappings.
- Create dataset splits.
- Implement preprocessing.
- Implement augmentation.

### Phase 3: Model Development

- Implement the PyTorch architecture.
- Implement the dataset loader.
- Implement the trainer.
- Implement checkpoint saving.
- Train the initial model.

### Phase 4: Model Evaluation

- Implement independent testing.
- Generate metrics.
- Analyze confusion matrix.
- Validate unseen samples.
- Select the best checkpoint.

### Phase 5: Real-Time Inference

- Implement model loading.
- Implement OpenCV preprocessing.
- Implement camera streaming.
- Connect the inference pipeline.
- Implement prediction stabilization.

### Phase 6: Audio Integration

- Implement gesture-to-text mapping.
- Implement browser audio output.
- Implement playback queue.
- Implement duplicate prevention.

### Phase 7: Streamlit UI

- Implement dashboard.
- Implement live detection.
- Implement prediction history.
- Implement model information.
- Implement settings.

### Phase 8: Testing and Optimization

- Run automated tests.
- Test actual camera streaming.
- Benchmark CPU/GPU performance.
- Fix memory and threading problems.
- Validate long-running sessions.

### Phase 9: Deployment

- Prepare configuration.
- Document environment setup.
- Document model setup.
- Configure deployment requirements.
- Verify browser camera and audio behavior.

---

# 15. Acceptance Criteria

The project is considered functionally complete when:

- [ ] The project can be initialized using uv.
- [ ] The environment is created in `venv/`.
- [ ] The directory structure follows the specification.
- [ ] The PyTorch model trains independently.
- [ ] The testing pipeline evaluates saved checkpoints.
- [ ] Evaluation metrics are generated correctly.
- [ ] The application loads the trained model.
- [ ] Browser camera access works.
- [ ] OpenCV processes incoming camera frames.
- [ ] Supported gestures are recognized.
- [ ] Confidence scores are displayed.
- [ ] Unrecognized gestures are handled correctly.
- [ ] Predictions are stabilized.
- [ ] Audio plays for confirmed predictions.
- [ ] Duplicate audio is prevented.
- [ ] Camera processing does not stop during audio playback.
- [ ] The UI is responsive and visually consistent.
- [ ] CPU fallback works.
- [ ] GPU acceleration works when available.
- [ ] The application handles camera and model failures.
- [ ] Automated tests pass.
- [ ] Documentation is complete.

---

# 16. Future Enhancements

The architecture should support future extensions without requiring a complete rewrite.

Potential additions:

1. Dynamic gesture recognition.
2. Sequence-based gesture classification.
3. MediaPipe hand landmark extraction.
4. LSTM or Transformer-based temporal recognition.
5. Custom gesture dataset collection.
6. User-defined gestures.
7. Multi-hand recognition.
8. Multi-language audio output.
9. Gesture-to-sentence conversion.
10. Recognition analytics.
11. Model comparison dashboard.
12. Model retraining interface.
13. Exportable prediction reports.

Dynamic gesture recognition must be treated as a separate ML capability rather than assuming that the initial static CNN can understand motion.

---

# 17. Final Architectural Principles

The following rules are mandatory throughout development.

1. Maintain strict separation between training, testing, inference, camera streaming and UI.
2. Never put the complete application inside `app.py`.
3. Never train the model automatically during application startup.
4. Never reload the model for every camera frame.
5. Never perform blocking audio playback inside the camera-processing loop.
6. Never mix training and testing datasets.
7. Never use fabricated evaluation metrics.
8. Never hardcode class mappings across multiple files.
9. Never store generated model weights inside the source-code directory unnecessarily.
10. Use configuration files for adjustable parameters.
11. Write reusable and testable functions.
12. Apply type hints and meaningful documentation.
13. Handle exceptions at appropriate application boundaries.
14. Keep dependencies pinned and reproducible.
15. Test every major module independently before integration.

**Final Product Goal:**

Deliver a complete, modular, PyTorch-powered real-time gesture recognition and audio assistant with a professional Streamlit interface, reliable camera streaming, stable gesture predictions, and responsive spoken output.