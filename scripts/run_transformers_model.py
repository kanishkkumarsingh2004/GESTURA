"""Download and run the dima806/hand_gestures_image_detection model via transformers.

This script downloads the trained ViT image-classification model from the Hugging Face
Hub (model weights only — this repo contains no training images) and runs inference
on a sample image using both the high-level pipeline and the low-level processor+model API.
"""

from transformers import pipeline, AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import requests
from io import BytesIO

MODEL_ID = "dima806/hand_gestures_image_detection"
SAMPLE_IMAGE_URL = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/hub/parrots.png"


def load_sample_image(url: str) -> Image.Image:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")


def run_pipeline(image: Image.Image) -> None:
    print(f"[pipeline] loading model: {MODEL_ID}")
    pipe = pipeline("image-classification", model=MODEL_ID)
    results = pipe(image)
    print("[pipeline] predictions:")
    for item in results[:5]:
        print(f"  {item['label']}: {item['score']:.4f}")


def run_direct(image: Image.Image) -> None:
    print(f"[direct] loading processor + model: {MODEL_ID}")
    processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForImageClassification.from_pretrained(MODEL_ID)

    inputs = processor(images=image, return_tensors="pt")
    import torch
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    probs = logits.softmax(dim=-1)[0]
    top = probs.topk(5)
    id2label = model.config.id2label
    print("[direct] predictions:")
    for score, idx in zip(top.values, top.indices):
        print(f"  {id2label[int(idx)]}: {float(score):.4f}")


def main() -> None:
    image = load_sample_image(SAMPLE_IMAGE_URL)
    print(f"Loaded sample image: {image.size}")
    run_pipeline(image)
    run_direct(image)
    print("Done.")


if __name__ == "__main__":
    main()
