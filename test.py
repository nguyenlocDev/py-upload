import os
import random
from PIL import Image, ImageEnhance
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import shutil
import uvicorn

app = FastAPI()

# ==== Configuration ====
input_folder = "in"
output_folder = "out"
watermark_folder = "watermark"

output_height = 1920           # Output image height
watermark_height = 230         # Watermark height (fixed)
opacity = 0.7                  # Watermark opacity (0.0 - 1.0)
horizontal_jitter = 100         # Random horizontal offset

os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

# ==== Load watermark files ====
watermark_files = [
    os.path.join(watermark_folder, f)
    for f in os.listdir(watermark_folder)
    if f.lower().endswith((".png", ".jpg", ".jpeg"))
]

if not watermark_files:
    raise ValueError("❌ No watermark files found in watermark folder")

# ==== Adjust opacity function ====
def adjust_opacity(img, alpha):
    assert img.mode == 'RGBA', "Image must be in RGBA mode"
    alpha_layer = img.split()[3]
    alpha_layer = ImageEnhance.Brightness(alpha_layer).enhance(alpha)
    img.putalpha(alpha_layer)
    return img

# ==== Process image function ====
def process_image(img_path, filename):
    try:
        # Verify image is valid
        with Image.open(img_path) as img_file:
            img_file.verify()  # Check if it's a valid image
    except Exception as e:
        raise ValueError(f"Invalid image file: {img_path}, {str(e)}")

    # Re-open image for processing
    img = Image.open(img_path).convert("RGBA")

    # Resize image
    aspect_ratio = img.width / img.height
    output_width = int(output_height * aspect_ratio)
    img_resized = img.resize((output_width, output_height), resample=Image.Resampling.LANCZOS)

    # Select random watermark
    wm_path = random.choice(watermark_files)
    wm = Image.open(wm_path).convert("RGBA")

    # Resize watermark
    wm_aspect = wm.width / wm.height
    wm_width = int(watermark_height * wm_aspect)
    wm_resized = wm.resize((wm_width, watermark_height), resample=Image.Resampling.LANCZOS)
    wm_resized = adjust_opacity(wm_resized, opacity)

    # Calculate watermark position
    pos_x = (output_width - wm_width) // 2 + random.randint(-horizontal_jitter, horizontal_jitter)
    pos_y = (output_height - watermark_height) // 3 + random.randint(-horizontal_jitter, horizontal_jitter)

    # Combine image and watermark
    combined = Image.new("RGBA", img_resized.size)
    combined.paste(img_resized, (0, 0))
    combined.paste(wm_resized, (pos_x, pos_y), wm_resized)

    # Save output
    out_path = os.path.join(output_folder, filename)
    combined.convert("RGB").save(out_path)

    return out_path, os.path.basename(wm_path)

# ==== API Endpoint ====
@app.post("/upload-images/")
async def upload_images(files: List[UploadFile] = File(...)):
    processed_files = []

    for file in files:
        # Validate content type
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a valid image (JPEG/PNG)")

        # Save file temporarily
        file_path = os.path.join(input_folder, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            # Process image
            out_path, wm_used = process_image(file_path, file.filename)
            processed_files.append({
                "filename": file.filename,
                "output_path": out_path,
                "watermark_used": wm_used
            })
        except ValueError as e:
            # Handle invalid image
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)

    return JSONResponse(content={
        "message": "Image processing complete!",
        "processed_files": processed_files
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)