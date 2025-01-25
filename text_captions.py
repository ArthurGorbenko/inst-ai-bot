import easyocr

reader = easyocr.Reader(['en'])
results = reader.readtext("./scenes/3481080082629109504_5599290503-Scene-001-02.jpg")

print("Detected Text:")
for result in results:
    print(f"{result[1]} (Confidence: {result[2]:.2f})")
