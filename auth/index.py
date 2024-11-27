import http.client
import urllib.parse
import os
from dotenv import load_dotenv
import requests

load_dotenv()

token = os.getenv('FB_TOKEN')
token = urllib.parse.quote(token)

print(token)

url = f"https://graph.facebook.com/v21.0/17991198722554695/insights?metric=clips_replays_count,ig_reels_aggregated_all_plays_count,ig_reels_avg_watch_time, ig_reels_video_view_total_time,reach,saved,total_interactions&access_token={token}"
payload = {}
headers = {}

# response = requests.request("GET", url, headers=headers, data=payload)

# print(response.text)


url=f"https://graph.facebook.com/v21.0/17841405595099911/insights?metric=impressions&access_token={token}&period=day"

response2 = requests.request("GET", url, headers={}, data={})

print(response2.text)