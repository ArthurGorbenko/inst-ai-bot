import json
from openai import OpenAI

def summarize_scenes(scenes):
    """Generate a structured summary of the video content using OpenAI"""
    # Initialize OpenAI client
    clientAI = OpenAI()
    
    scenes_json = json.dumps(scenes, indent=2)
    prompt_file_path = "./prompts/system/1.summarize-structured.txt"
    prompt = ""
    try:
        with open(prompt_file_path, "r") as file:
            prompt = file.read()
    except Exception as e:
        print(f"Error reading prompt file: {str(e)}")
        prompt = "Please analyze the following video scene data and provide a structured summary:"

    response = clientAI.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "system",
                "content": "You analyze scene-level video data and generate structured output for RAG-based systems to index and retrieve content accurately.",
            },
            {"role": "user", "content": prompt + scenes_json},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "structured_analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "A precise title for the video, useful as search anchor",
                        },
                        "summary": {
                            "type": "string",
                            "description": "Concise summary of what the video covers",
                        },
                        "keypoints": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": "string"},
                                    "text": {"type": "string"},
                                },
                                "required": ["timestamp", "text"],
                                "additionalProperties": False,
                            },
                            "description": "Scene-level moments with important statements, useful for grounding",
                        },
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Key searchable topics or tags",
                        },
                        "content_type": {
                            "type": "string",
                            "description": "Format/category of the content (humor, ad, motivational, vlog etc.)",
                        },
                        "call_to_action": {
                            "type": "string",
                            "description": "Any call-to-action mentioned, or null if not applicable",
                        },
                    },
                    "required": [
                        "title",
                        "summary",
                        "keypoints",
                        "topics",
                        "content_type",
                        "call_to_action"
                    ],
                    "additionalProperties": False,
                },
                "strict": True,
            }
        },
    )
    
    return json.loads(response.output_text) 