def match_transcription_to_scenes(scenes, transcription):
    """Match transcription segments to video scenes based on timestamps"""
    print("\n=== Matching transcriptions to scenes ===")

    # Convert scene timestamps to seconds for easier comparison
    scene_times = {}
    for scene_id, scene_data in scenes.items():
        ts = scene_data["timestamp"]
        print(f"Processing timestamp: {ts} for scene {scene_id}")

        try:
            # Normalize timestamp format (replace semicolons with colons if present)
            ts = ts.replace(";", ":")

            # Split timestamp into components
            if ":" in ts:
                parts = ts.split(":")
                if len(parts) == 3:  # HH:MM:SS format
                    h, m, s = parts
                elif len(parts) == 2:  # MM:SS format
                    h, m, s = "0", parts[0], parts[1]
                else:
                    h, m, s = "0", "0", parts[0]
            else:
                h, m, s = "0", "0", ts

            # Handle milliseconds if present
            s, ms = s.split(".") if "." in s else (s, "0")
            total_seconds = int(h) * 3600 + int(m) * 60 + float(s) + float(ms) / 1000
            scene_times[scene_id] = total_seconds
            print(f"Converted to {total_seconds} seconds")
        except Exception as e:
            print(f"Error parsing timestamp {ts} for scene {scene_id}: {str(e)}")
            scene_num = int(scene_data.get("scene_number", "0"))
            scene_times[scene_id] = (
                scene_num * 5
            )  # Assume 5 seconds per scene as fallback

    # Sort scenes by timestamp
    sorted_scenes = sorted(scene_times.items(), key=lambda x: x[1])

    # Calculate scene duration estimates
    scene_durations = {}
    for i, (scene_id, start_time) in enumerate(sorted_scenes):
        if i < len(sorted_scenes) - 1:
            end_time = sorted_scenes[i + 1][1]
        else:
            # For the last scene, estimate duration based on last transcription
            end_time = (
                max(t["end"] for t in transcription)
                if transcription
                else start_time + 5
            )
        scene_durations[scene_id] = (start_time, end_time)

    # Clear existing transcriptions
    for scene_id in scenes:
        scenes[scene_id]["transcription"] = []

    # Match transcriptions to scenes based on overlap
    for segment in transcription:
        segment_start = segment["start"]
        segment_end = segment["end"]
        segment_text = segment["text"]

        # Find all scenes that overlap with this segment
        for scene_id, (scene_start, scene_end) in scene_durations.items():
            # Check if there's any overlap between segment and scene
            if segment_start <= scene_end and segment_end >= scene_start:
                overlap_start = max(segment_start, scene_start)
                overlap_end = min(segment_end, scene_end)
                overlap_duration = overlap_end - overlap_start

                # Only add if there's significant overlap (more than 0.5 seconds)
                if overlap_duration > 0.5:
                    scenes[scene_id]["transcription"].append(
                        {
                            "start": segment_start,
                            "end": segment_end,
                            "text": segment_text,
                            "overlap_duration": overlap_duration,
                        }
                    )
                    print(
                        f"Matched transcription to scene {scene_id} (overlap: {overlap_duration:.2f}s): {segment_text}"
                    )

    # For scenes without transcription, find the nearest segment
    for scene_id, scene_data in scenes.items():
        if not scene_data["transcription"]:
            # Use the parsed timestamp (converted to seconds) for matching
            scene_start = scene_times[scene_id]
            closest_segment = min(
                transcription, key=lambda x: abs(x["start"] - scene_start)
            )
            scenes[scene_id]["transcription"].append(
                {
                    "start": closest_segment["start"],
                    "end": closest_segment["end"],
                    "text": closest_segment["text"],
                    "note": "nearest_match",
                }
            )
            print(
                f"Assigned nearest transcription to scene {scene_id}: {closest_segment['text']}"
            )

    return scenes 