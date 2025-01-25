import whisper
import sys
from pymongo import MongoClient

if(len(sys.argv) < 2):
    print("Provide argument for filename")
    sys.exit()

filename = sys.argv[1]

print(filename)

model = whisper.load_model("large")

result = model.transcribe(filename)

new_list = list(map(lambda x: {"start": round(x.get("start"), 1), "end": round(x.get("end"), 1), "text": x.get("text")}, result.get("segments")))
print(new_list)

client = MongoClient('mongodb://localhost:27017/')  # Your MongoDB connection
try:
    db = client['creator-kb']
    transcriptions_col = db['transcriptions']
    # Get filename without extension
    base_filename = filename.split(".")[0]
    print(base_filename)
    transcriptions_col.insert_one({"segments": new_list, "filename": base_filename})
finally:
    client.close()  # Properly close the connection
