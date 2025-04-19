import os
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

def generate_scene_description(images_dir, existing_scenes=None):
    """Generate descriptions for scene images using BLIP model"""
    print(f"\n=== Starting generate_scene_description for directory: {images_dir} ===")
    try:
        print("Loading BLIP processor and model...")
        processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )

        files = os.listdir(images_dir)
        print(f"Found {len(files)} files in directory")
        scenes = existing_scenes or {}

        for f in files:
            # Extract scene info from filename
            scene_info = f.split("--")
            if len(scene_info) >= 4:
                scene_num = scene_info[1]
                frame_num = scene_info[2]
                # Now the 4th segment contains the actual timestamp
                timestamp = scene_info[3].split(".")[0]
                scene_id = f"{scene_num}_{frame_num}"

                image_path = os.path.join(images_dir, f)
                print(f"Processing image: {image_path}")

                image = Image.open(image_path)
                inputs = processor(image, return_tensors="pt")
                outputs = model.generate(**inputs)
                description = processor.decode(outputs[0], skip_special_tokens=True)

                if scene_id not in scenes:
                    scenes[scene_id] = {
                        "descriptions": [],
                        "captions": [],
                        "images": [],
                        "scene_number": scene_num,
                        "frame_number": frame_num,
                        "timestamp": timestamp,
                    }

                scenes[scene_id]["descriptions"].append(description)
                scenes[scene_id]["images"].append(f)
                print(f"Generated Description for scene {scene_id}: {description}\n")

        return scenes
    except Exception as e:
        print(f"Error in generate_scene_description: {str(e)}") 