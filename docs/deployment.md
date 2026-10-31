# Deployment Documentation

## Local development

1. Initialize the environment:

   ```bash
   uv python pin 3.11
   uv venv venv
   source venv/bin/activate
   uv sync
   ```

2. Run the application:

   ```bash
   uv run --active streamlit run app.py
   ```

3. Open the Streamlit URL shown in the terminal and grant camera permission.

## Model requirement

A trained checkpoint must exist at `outputs/checkpoints/best_model.pth` (or the
path configured in `config.yaml`) for inference to work. Train one first via
`python -m train.train`.

## Production deployment

- Serve over HTTPS (browser camera/WebRTC requires a secure context).
- Configure WebRTC STUN/TURN if direct peer connectivity is unavailable.
- Isolate sessions; never share mutable prediction or camera state.
- Bound queues and enforce session/resource limits.
- Validate checkpoint integrity before loading.

## Environment variables

No secrets are required for local operation. Keep any future credentials out of
source control (see `.gitignore` and `security.md`).
