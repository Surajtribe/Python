import streamlit as st
from google import genai
from google.genai.types import Part
import os
import time
import glob
import base64
from PIL import Image
import io
import json

def compress_image_bytes(img_bytes, max_size=(3000, 3000), quality=95):
    from PIL import Image
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    w, h = img.size
    if w == h:
        target_ratio = 3 / 2 
        new_w = w
        new_h = int(w / target_ratio)

        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    img.thumbnail(max_size, Image.LANCZOS)

    buf = io.BytesIO()
    img.save(
        buf,
        format="JPEG",
        quality=quality,
        subsampling=0,
        optimize=True
    )

    return buf.getvalue()


# ---------------- CONFIG ----------------
PROJECT_ID = "cobalt-diorama-474513-a8"
LOCATION = "global"

MODEL_PRO = "publishers/google/models/gemini-3-pro-image-preview"
MODEL_FLASH = "gemini-2.5-flash-image"
MODEL_ID = "gemini-2.5-flash-image"


BASE_DIR = "D:\\HK-AI-Image-Generation-main\\"
PRODUCTS_DIR = os.path.join(BASE_DIR, "products")
FABRIC_DIR = os.path.join(BASE_DIR, "cover", "fabric")
LEATHER_DIR = os.path.join(BASE_DIR, "cover", "leather")
SAVE_DIR = os.path.join(BASE_DIR, "results")

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
os.makedirs(SAVE_DIR, exist_ok=True)

# ---------------- HELPERS ----------------

@st.cache_data
def load_images(folder):
    return sorted(
        glob.glob(os.path.join(folder, "*.jpg")) +
        glob.glob(os.path.join(folder, "*.jpeg")) +
        glob.glob(os.path.join(folder, "*.png"))
    )

@st.cache_data
def load_thumbnail(path, max_width=300):
    img = Image.open(path)
    w, h = img.size
    scale = max_width / w
    img_small = img.resize((max_width, int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img_small.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def save_image_unique(img_bytes, base_name):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{base_name}_{timestamp}.png"
    path = os.path.join(SAVE_DIR, filename)
    with open(path, "wb") as f:
        f.write(img_bytes)
    return path


def call_model(model_id, parts, retries=3):
    """
    Calls Gemini image model with retry.
    Returns: (image_bytes, error_text)
    """

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=[
                    {
                        "role": "user",
                        "parts": parts
                    }
                ]
            )

            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        return part.inline_data.data, None

            return None, "No image data returned from model."

        except Exception as e:
            last_error = e
            print(f"[Gemini] Attempt {attempt}/{retries} failed: {e}")
            time.sleep(2 * attempt)  # backoff

    return None, f"Failed after {retries} retries. Last error: {last_error}"
# ---------------- UI ----------------

st.title("Skagen Studio – AI Image Generator")

# MODEL SELECTOR
st.markdown("### Choose AI model")
model_select = st.radio(
    "Choose AI model",
    ["Gemini 3 Pro (Nano Banana Pro)", "Gemini 2.5 Flash Image"],
    index=0,
    label_visibility="collapsed"
)


if model_select == "Gemini 3 Pro (Nano Banana Pro)":
    MODEL_ID = MODEL_PRO
else:
    MODEL_ID = MODEL_FLASH

# -------- SELECT PRODUCT --------
st.markdown("### Upload Product Images")

uploaded_products = st.file_uploader(
    "Select product images from your device",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

all_product_bytes = []

if uploaded_products:
    st.markdown("### Product reference images")
    cols = st.columns(3)

    for i, file in enumerate(uploaded_products):
        img_bytes = file.read()
        all_product_bytes.append(img_bytes)

        img = Image.open(io.BytesIO(img_bytes))
        with cols[i % 3]:
            st.image(
                img,
                caption=f"Product Image {i + 1}",
                use_container_width=True
            )



# ---------------- CURRENT COLOR ----------------

st.markdown("### CURRENT color (optional)")

is_leather_current = st.toggle("Leather (Fabric default)", key="current_mat_toggle")
cur_dir = LEATHER_DIR if is_leather_current else FABRIC_DIR
cur_files = load_images(cur_dir)

selected_current_color_file = st.selectbox(
    "Choose CURRENT color",
    ["-- select --"] + [os.path.basename(f) for f in cur_files],
    key="current_color_select"
)

current_color_bytes = None
if selected_current_color_file != "-- select --":
    cur_path = os.path.join(cur_dir, selected_current_color_file)
    with open(cur_path, "rb") as f:
        current_color_bytes = f.read()

    thumb = load_thumbnail(cur_path)
    st.image(f"data:image/png;base64,{thumb}", caption="Current color preview")


# ---------------- TARGET COLOR ----------------

st.markdown("### TARGET color (required)")

is_leather_target = st.toggle("Leather (Fabric default)", key="target_mat_toggle")
target_dir = LEATHER_DIR if is_leather_target else FABRIC_DIR
target_files = load_images(target_dir)

selected_target_color_file = st.selectbox(
    "Choose TARGET color",
    ["-- select --"] + [os.path.basename(f) for f in target_files],
    key="target_color_select"
)

target_color_bytes = None
if selected_target_color_file != "-- select --":
    tgt_path = os.path.join(target_dir, selected_target_color_file)
    with open(tgt_path, "rb") as f:
        target_color_bytes = f.read()

    thumb = load_thumbnail(tgt_path)
    st.image(f"data:image/png;base64,{thumb}", caption="Target color preview")


# ---------------- ADDITIONAL INPUTS ----------------

st.markdown("### Additional references (optional)")

human_refs = st.file_uploader("Human references", ["jpg", "jpeg", "png"], accept_multiple_files=True)
interior_refs = st.file_uploader("Interior style reference images", ["jpg", "jpeg", "png"], accept_multiple_files=True)

interior_style = st.selectbox(
    "Interior style preset (optional)",
    [
        "-- none --",
        "New York penthouse",
        "Norwegian timber “hytte”",
        "Scandinavian minimalism",
        "High-end hotel luxury",
        "Dark moody loft",
        "Modern Minimal / Scandinavian landscape"
    ],
    key="interior_style_dropdown"
)

prompt_text = st.text_area("Additional prompt (optional)")


# ---------------- GENERATE ----------------
if st.button("Generate"):

    if not all_product_bytes:
        st.error("No product images found.")
        st.stop()

    if not target_color_bytes:
        st.error("Please choose TARGET color.")
        st.stop()

    # -------- BUILD INSTRUCTIONS --------

    auto_interior = ""
    if interior_refs:
        auto_interior = "Target interior is added as interior reference image."

    dropdown_prompt = ""
    if interior_style != "-- none --":
        dropdown_prompt = f"{interior_style} is a target interior."

    instructions = (
        "Place the chair from all provided product images into an interior. "
        "Use all angles to preserve correct geometry, stitching, arms, legs and proportions. "
        "Replace upholstery with the TARGET color. "
        "No changes to silhouette or construction. "
        "Chair must look realistically placed with correct scale, natural shadows and lighting. "
        "Render with high clarity, sharp edges, detailed textures, professional product photography lighting. "
        "Avoid blur, softness, artifacts, or painterly effects. "
        "Clean, crisp, high-detail output. "
        + auto_interior + " " + dropdown_prompt
    )

    if prompt_text:
        instructions += " " + prompt_text

    # -------- BUILD PARTS (TEXT FIRST) --------

    parts = [{"text": instructions}]

    # product images (compressed)
    for img in all_product_bytes:
        compressed = compress_image_bytes(img)
        parts.append(
            Part(
                inline_data={
                    "data": compressed,
                    "mime_type": "image/jpeg"
                }
            )
        )

    # target color (compressed)
    compressed_target = compress_image_bytes(target_color_bytes)
    parts.append(
        Part(
            inline_data={
                "data": compressed_target,
                "mime_type": "image/jpeg"
            }
        )
    )

    # -------- CALL MODEL --------

    st.info("Generating image…")

    img_bytes, error = call_model(MODEL_ID, parts)

    if img_bytes:
        out_path = save_image_unique(img_bytes, "result")
        st.image(img_bytes)
        st.success(f"Saved to: {out_path}")

        st.markdown("### Debug info")
        st.json({"model_used": MODEL_ID})

    else:
        st.error("❌ Model failed.")
        st.json({"model_used": MODEL_ID, "error": error})


