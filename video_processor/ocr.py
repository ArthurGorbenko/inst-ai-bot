import os
from paddleocr import PaddleOCR

def get_captions(images_path, scene_timestamps):
    """Extract text captions from scene images using OCR"""
    print(f"\n=== Starting get_captions for directory: {images_path} ===")
    try:
        files = os.listdir(images_path)
        print(f"Found {len(files)} files in directory")

        ocr = PaddleOCR(use_gpu=False, lang="en", show_log=False)
        scenes = {}

        for f in files:
            scene_info = f.split("--")
            if len(scene_info) >= 4:
                scene_num = scene_info[1]
                frame_num = scene_info[2]
                # With the updated template, the 4th segment now holds the actual timestamp
                timestamp = scene_info[3].split(".")[0]
                scene_id = f"{scene_num}_{frame_num}"

                image_path = os.path.join(images_path, f)
                print(f"Processing image: {image_path}")

                if scene_id not in scenes:
                    scenes[scene_id] = {
                        "descriptions": [],
                        "captions": [],
                        "images": [],
                        "scene_number": scene_num,
                        "frame_number": frame_num,
                        "timestamp": timestamp,
                        "frame": frame_num,  # Retain the frame number for reference if needed
                    }

                # Run PaddleOCR on the image
                results = ocr.ocr(image_path, cls=True)

                if results and results[0]:
                    # filter results with less than 0.9 confidence
                    results[0] = [
                        line
                        for line in results[0]
                        if line is not None and line[1][1] >= 0.9
                    ]
                    for line in results[0]:
                        if line is not None:
                            text = line[1][0]
                            confidence = line[1][1]
                            scenes[scene_id]["captions"].append(
                                {"text": text, "confidence": confidence}
                            )
                            print(f"{text} (Confidence: {confidence:.2f})")
                else:
                    print(f"No text detected in image: {image_path}")
            print()

        return scenes
    except Exception as e:
        print(f"Error in get_captions: {str(e)}")
        return {}  # Return empty dict instead of None on error 