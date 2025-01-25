import os
from ultralytics import YOLO

# Load the model
model = YOLO("yolo11x.pt")

# Path to scenes folder
scenes_folder = 'scenes'

# Iterate over all files in scenes folder
for filename in os.listdir(scenes_folder):
    if filename.endswith(('.jpg', '.jpeg', '.png')):  # Check if file is an image
        image_path = os.path.join(scenes_folder, filename)
        print(f"\nProcessing image: {filename}")
        
        # Load and process the image
        results = model(image_path)[0]
        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = result
            class_name = model.names[int(class_id)]
            print(f"Object: {class_name}, Confidence: {score:.2f}")
