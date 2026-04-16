def check_notion_entry(video_id):
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    headers = {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # Corrected filter logic for Relation and Select properties
    payload = {
        "filter": {
            "and": [
                {
                    "property": "Video ID",
                    "rich_text": {"equals": video_id}
                },
                {
                    "property": "Type",
                    "select": {"equals": "Reel"}
                },
                {
                    "property": "Channel",
                    # For a Relation, we check if the related page contains the name
                    "relation": {
                        "contains": "phonkstax" 
                    }
                }
            ]
        }
    }
    
    res = requests.post(url, json=payload, headers=headers).json()
    
    if "results" not in res:
        print(f"Debug Notion Response Error: {res}")
        return False
        
    return len(res.get("results", [])) > 0
