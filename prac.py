import cv2
import json
import os
from PIL import Image
from PIL.ExifTags import TAGS


# ==========================================
# 1. IMAGE PREPROCESSING
# ==========================================

def preprocess_image(image_path, target_size=(224, 224)):
    try:
        if not os.path.exists(image_path):
            print(f"Error: File does not exist -> {image_path}")
            return None, None

        img = cv2.imread(image_path)

        if img is None:
            print(f"Error: Could not load image from {image_path}")
            return None, None

        resized_img = cv2.resize(
            img,
            target_size,
            interpolation=cv2.INTER_AREA
        )

        exif_data = {}

        try:
            pil_img = Image.open(image_path)

            if hasattr(pil_img, "_getexif"):
                exif = pil_img._getexif()

                if exif is not None:
                    for tag, value in exif.items():
                        decoded = TAGS.get(tag, tag)
                        exif_data[decoded] = str(value)

        except Exception as e:
            print(
                f"Warning: EXIF extraction failed "
                f"for {image_path}: {e}"
            )

        return resized_img, exif_data

    except Exception as e:
        print(f"Preprocessing Error: {e}")
        return None, None


# ==========================================
# 2. SIMULATED LLM RISK ANALYSIS
# ==========================================

def analyze_metadata_with_llm(
    metadata,
    duplicate_found=False
):

    risk_score = 0.0
    comments = []

    # EXIF checks
    if not metadata:
        risk_score += 0.3
        comments.append("No EXIF metadata found.")

    else:

        if "DateTimeOriginal" not in metadata:
            risk_score += 0.2
            comments.append("Missing original capture date.")

        if (
            "Software" in metadata
            and "Photoshop" in metadata["Software"]
        ):
            risk_score += 0.4
            comments.append("Edited using Photoshop.")

    # Duplicate check
    if duplicate_found:
        risk_score += 0.5
        comments.append("Duplicate content detected.")

    risk_score = min(1.0, risk_score)

    # Decision logic
    if risk_score > 0.7:
        decision = "REJECT"

    elif risk_score > 0.3:
        decision = "PENDING"

    else:
        decision = "ACCEPT"

    return {
        "risk_score": round(risk_score, 2),
        "decision": decision,
        "comment": " | ".join(comments)
    }


# ==========================================
# 3. PROCESS SINGLE IMAGE
# ==========================================

def process_single_image(image_path):

    processed_image, metadata = preprocess_image(image_path)

    if processed_image is None:

        return {
            "image": image_path,
            "status": "FAILED",
            "decision": "ERROR",
            "risk_score": "NA",
            "comment": "Image could not be loaded"
        }

    # Simulated duplicate detection
    duplicate_found = False

    llm_result = analyze_metadata_with_llm(
        metadata,
        duplicate_found
    )

    return {
        "image": image_path,
        "status": "SUCCESS",
        "metadata": metadata,
        "risk_score": llm_result["risk_score"],
        "decision": llm_result["decision"],
        "comment": llm_result["comment"]
    }


# ==========================================
# 4. MULTI IMAGE PROCESSING
# ==========================================

def process_multiple_images(image_paths):

    results = []

    for path in image_paths:

        print(f"\nProcessing: {path}")

        result = process_single_image(path)

        results.append(result)

    return results


# ==========================================
# LOAD IMAGES FROM FOLDER
# ==========================================

def load_images_from_folder(folder_path):

    supported_formats = (
        ".jpg",
        ".jpeg",
        ".png"
    )

    image_paths = []

    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return image_paths

    for file in os.listdir(folder_path):

        if file.lower().endswith(
            supported_formats
        ):
            image_paths.append(
                os.path.join(folder_path, file)
            )

    return image_paths


# ==========================================
# MAIN
# ==========================================

def main():

    print("\n🚀 Kled Multi-Image Data Validation Pipeline")
    print("--------------------------------------------")

    current_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    image_paths = [
        os.path.join(current_dir, "dummy_image.jpg"),
        os.path.join(current_dir, "image2.jpg"),
        os.path.join(current_dir, "image3.jpg")
    ]

    # Alternative:
    # image_paths = load_images_from_folder(
    #     os.path.join(current_dir, "images")
    # )

    results = process_multiple_images(
        image_paths
    )

    # Save JSON
    output_file = os.path.join(
        current_dir,
        "validation_results.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            results,
            f,
            indent=4
        )

    print(
        f"\n✅ Processing Complete. "
        f"Results saved to {output_file}"
    )

    # Summary
    print("\n--- SUMMARY ---")

    for r in results:

        print(
            f"{r.get('image','Unknown')} -> "
            f"{r.get('decision','ERROR')} "
            f"(Risk: {r.get('risk_score','NA')})"
        )

    print("\nDone.")


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    main()