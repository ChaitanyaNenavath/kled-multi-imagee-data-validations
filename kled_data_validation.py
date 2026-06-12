
import cv2
import numpy as np
import json
from PIL import Image
from PIL.ExifTags import TAGS

# --- 1. Image Preprocessing using OpenCV ---

def preprocess_image(image_path, target_size=(224, 224)):
    """
    Loads an image, resizes it using OpenCV, and extracts basic metadata.
    """
    try:
        # Load image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Could not load image from {image_path}")
            return None, None

        # Resize image
        resized_img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)

        # Extract EXIF metadata using PIL (more robust for metadata)
        exif_data = {}
        try:
            pil_img = Image.open(image_path)
            if hasattr(pil_img, "_getexif"):
                _exif = pil_img._getexif()
                if _exif is not None:
                    for tag, value in _exif.items():
                        decoded = TAGS.get(tag, tag)
                        exif_data[decoded] = str(value)
        except Exception as e:
            print(f"Warning: Could not extract EXIF data for {image_path}: {e}")

        print(f"Image {image_path} preprocessed. Resized to {target_size}.")
        return resized_img, exif_data

    except Exception as e:
        print(f"An error occurred during image preprocessing: {e}")
        return None, None

# --- 2. Simulated LLM Integration for Metadata Analysis/Risk Scoring ---

def analyze_metadata_with_llm(metadata, image_analysis_summary=""):
    """
    Simulates an LLM analyzing image metadata and providing a risk score.
    In a real scenario, this would involve sending data to an LLM API.
    """
    print("\nSimulating LLM analysis...")
    prompt_parts = [
        "Analyze the following image metadata and provide a risk assessment for its authenticity and quality.",
        "Consider potential signs of manipulation, low quality, or unusual patterns.",
        "Metadata: " + json.dumps(metadata, indent=2),
    ]
    if image_analysis_summary:
        prompt_parts.append("Additional image analysis: " + image_analysis_summary)

    # Simulate LLM response based on metadata content
    risk_score = 0.0
    llm_comment = "Initial assessment based on available metadata.\n"

    if not metadata:
        llm_comment += "No EXIF metadata found, which could be a red flag for authenticity.\n"
        risk_score += 0.3
    else:
        if "Make" in metadata and "Model" in metadata:
            llm_comment += f"Device: {metadata['Make']} {metadata['Model']}.\n"
        if "DateTimeOriginal" in metadata:
            llm_comment += f"Original capture date: {metadata['DateTimeOriginal']}.\n"
        else:
            llm_comment += "Original capture date missing, potentially suspicious.\n"
            risk_score += 0.2

        if "Software" in metadata and "Photoshop" in metadata["Software"]:
            llm_comment += "Image processed with Photoshop, warrants closer inspection.\n"
            risk_score += 0.4

    if "synthetic" in image_analysis_summary.lower() or "duplicate" in image_analysis_summary.lower():
        llm_comment += "Image analysis suggests potential synthetic or duplicate content.\n"
        risk_score += 0.5

    # Simple risk scoring logic
    if risk_score > 0.7:
        llm_comment += "Overall: High risk. Recommend human review.\n"
    elif risk_score > 0.3:
        llm_comment += "Overall: Medium risk. Further automated checks or review recommended.\n"
    else:
        llm_comment += "Overall: Low risk. Appears authentic and of good quality.\n"

    return {"risk_score": min(1.0, risk_score), "llm_comment": llm_comment}

# --- Main Pipeline Simulation ---

def main():
    print("Kled Data Validation Pipeline Simulation")
    print("--------------------------------------")

    # Create a dummy image for demonstration
    dummy_image_path = "dummy_image.jpg"
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(dummy_img, "practice Test Image", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imwrite(dummy_image_path, dummy_img)
    print(f"Created a dummy image at: {dummy_image_path}")

    # Step 1: Preprocessing Layer (using OpenCV and PIL for metadata)
    print("\n--- Step 1: Preprocessing ---")
    processed_image, metadata = preprocess_image(dummy_image_path)

    if processed_image is not None:
        # For demonstration, we'll just print the shape and metadata
        print(f"Processed image shape: {processed_image.shape}")
        print("Extracted Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

        # Simulate some basic image analysis (e.g., from an ML model)
        # In a real system, this would be actual ML model output
        image_analysis_summary = "Image appears to be a simple graphic, no complex features detected. No obvious signs of synthetic generation, but also lacks rich photographic detail."
        if not metadata:
            image_analysis_summary += " No EXIF data available."

        # Step 2: ML Validation Pipeline (Simulated LLM for risk scoring)
        print("\n--- Step 2: ML Validation (LLM for Risk Scoring) ---")
        llm_result = analyze_metadata_with_llm(metadata, image_analysis_summary)
        print(f"LLM Risk Score: {llm_result['risk_score']:.2f}")
        print("LLM Comment:")
        print(llm_result['llm_comment'])

        # Step 3: Decision based on Risk Score (Simplified)
        print("\n--- Step 3: Decision ---")
        if llm_result['risk_score'] > 0.5:
            print("Decision: REJECT (High risk, requires human review)")
        elif llm_result['risk_score'] > 0.2:
            print("Decision: PENDING (Medium risk, further checks)")
        else:
            print("Decision: ACCEPT (Low risk)")

    print("\nSimulation Complete.")

if __name__ == "__main__":
    main()
