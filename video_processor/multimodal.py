from twelvelabs import TwelveLabs

prompt="""
Analyze an Instagram reel from a tech blogger influencer and provide a Comprehensive Description. Include the following details: Describe the reel's purpose, main topics, and target audience, explaining what it communicates and its context in the tech niche. Detail the visual elements, including the setting, objects, gadgets, and notable effects or transitions. Summarize the spoken content or dialogues, highlighting key phrases, quotes, and points emphasized by the influencer. Explain the narrative flow, describing how the content progresses from start to finish, including the opening, main segments, and conclusion. Identify and describe any calls to action, such as encouraging viewers to like, comment, follow, or click links. Analyze the influencer's persona, including tone, style, personality traits, and engagement with their audience. Output the results in the following JSON format: {"content_overview": "Description of the reel's purpose, topics, and target audience.","key_visual_elements": "Details of setting, objects, effects, and transitions.","spoken_content_and_dialogues": "Summary of spoken content with key phrases or quotes.","narrative_flow": "How the reel's content progresses.","calls_to_action": "Details on any calls to action.","influencer_persona": "Analysis of the influencer's tone, style, and engagement."} Ensure the JSON is valid, contains no formatting or new line characters, and includes as much detail as possible for each field.
"""

def generate_summary(api_key, video_id):
    print("calling generate summary")
    client = TwelveLabs(api_key=api_key)
    res = None
    try:
        res = client.generate.text(video_id=video_id, prompt=prompt, temperature=0.7)
    except Exception as e:
        print("Error happened in generate_summary after getting summary", e)
        
    return res
    
    