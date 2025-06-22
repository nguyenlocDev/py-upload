import os
import random
from PIL import Image, ImageEnhance

# ==== Cấu hình ====
input_folder = "in"
output_folder = "out"
watermark_folder = "watermark"

output_height = 1920           # Chiều cao ảnh out
watermark_height = 230         # Chiều cao watermark (cố định)
opacity = 0.7                  # Độ mờ watermark (0.0 - 1.0)
horizontal_jitter = 30         # Lệch trái/phải ngẫu nhiên

os.makedirs(output_folder, exist_ok=True)

# ==== Load danh sách watermark ====
watermark_files = [
    os.path.join(watermark_folder, f)
    for f in os.listdir(watermark_folder)
    if f.lower().endswith((".png", ".jpg", ".jpeg"))
] 

if not watermark_files:
    raise Exception("❌ Không tìm thấy watermark nào trong thư mục watermarks/")

# ==== Hàm chỉnh độ mờ ====
def adjust_opacity(img, alpha):
    assert img.mode == 'RGBA'
    alpha_layer = img.split()[3]
    alpha_layer = ImageEnhance.Brightness(alpha_layer).enhance(alpha)
    img.putalpha(alpha_layer)
    return img

# ==== Xử lý từng ảnh ====
for filename in os.listdir(input_folder):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        img_path = os.path.join(input_folder, filename)
        img = Image.open(img_path).convert("RGBA")

        # Resize ảnh theo chiều cao
        aspect_ratio = img.width / img.height
        output_width = int(output_height * aspect_ratio)
        img_resized = img.resize((output_width, output_height), resample=Image.Resampling.LANCZOS)

        # === Chọn watermark ngẫu nhiên ===
        wm_path = random.choice(watermark_files)
        wm = Image.open(wm_path).convert("RGBA")

        # Resize watermark theo chiều cao cố định, giữ tỉ lệ
        wm_aspect = wm.width / wm.height
        wm_width = int(watermark_height * wm_aspect)
        wm_resized = wm.resize((wm_width, watermark_height), resample=Image.Resampling.LANCZOS)
        wm_resized = adjust_opacity(wm_resized, opacity)

        # Tính vị trí watermark
        pos_x = (output_width - wm_width) // 2 + random.randint(-horizontal_jitter, horizontal_jitter)
        pos_y = (output_height - watermark_height) // 3

        # Ghép watermark
        combined = Image.new("RGBA", img_resized.size)
        combined.paste(img_resized, (0, 0))
        combined.paste(wm_resized, (pos_x, pos_y), wm_resized)

        # Lưu ảnh
        out_path = os.path.join(output_folder, filename)
        combined.convert("RGB").save(out_path)

        print(f"✅ {filename} -> dùng watermark: {os.path.basename(wm_path)}")

print("🎉 Hoàn tất!")
