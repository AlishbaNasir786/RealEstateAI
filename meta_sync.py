import os
# Use built-in urllib so Vercel bundle-size stripping can never break this
try:
    import requests
except ImportError:
    import urllib.request as _urllib_req
    import urllib.error as _urllib_err
    import ssl as _ssl
    import json as _json_mod

    class _FakeResp:
        def __init__(self, status, data):
            self.status_code = status
            self.text = data.decode('utf-8', errors='replace')
        def json(self):
            return _json_mod.loads(self.text)

    class _ReqShim:
        def get(self, url, params=None, timeout=15):
            if params:
                from urllib.parse import urlencode
                url = url + '?' + urlencode(params)
            req = _urllib_req.Request(url)
            ctx = _ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = _ssl.CERT_NONE
            try:
                with _urllib_req.urlopen(req, timeout=timeout, context=ctx) as r:
                    return _FakeResp(r.status, r.read())
            except _urllib_err.HTTPError as e:
                return _FakeResp(e.code, e.read())

    requests = _ReqShim()
import json
from dotenv import load_dotenv
from db import supabase

load_dotenv()

FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") # Optional: to configure real LLM

def get_page_posts():
    """Fetch recent posts from the linked Meta Page."""
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("Missing FB_PAGE_ACCESS_TOKEN or FB_PAGE_ID in .env")
        return []
        
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/posts"
    params = {
        "fields": "message,full_picture,created_time,attachments",
        "access_token": FB_PAGE_ACCESS_TOKEN,
        "limit": 10
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error fetching from Graph API: {response.text}")
        return []
        
    return response.json().get("data", [])

def parse_caption_with_llm(caption):
    """
    Uses an LLM to parse the caption into structured property data.
    If GEMINI_API_KEY is missing, falls back to basic heuristic extraction.
    """
    if not caption:
        return None
        
    if GEMINI_API_KEY:
        try:
            # Placeholder for actual LLM call using Google Generative AI / OpenAI
            # e.g., google.generativeai.GenerativeModel('gemini-pro').generate_content(...)
            pass
        except Exception as e:
            print(f"LLM Error: {e}")
            
    # Basic Heuristic Fallback (To be replaced by real LLM prompt logic)
    caption_lower = caption.lower()
    if "price" not in caption_lower and "pkr" not in caption_lower:
        return None # Skip if it doesn't look like a property listing

    # Attempt to extract fields naively as a fallback
    return {
        "title": caption[:50] + "..." if len(caption) > 50 else caption,
        "price": 0, # Would be extracted by LLM
        "city": "Unknown", # Would be extracted by LLM
        "beds": None,
        "baths": None,
        "property_type": "House" if "house" in caption_lower else "Flat",
        "mode": "for_rent" if "rent" in caption_lower else "for_sale"
    }

def sync_meta_posts():
    print("Starting Meta Graph API sync...")
    posts = get_page_posts()
    if not posts:
        print("No posts found or missing credentials. Halting sync.")
        return
        
    for post in posts:
        caption = post.get("message", "")
        img_url = post.get("full_picture", "")
        
        parsed_data = parse_caption_with_llm(caption)
        
        if not parsed_data:
            print(f"Skipping post {post.get('id')} - Not a valid property listing.")
            continue
            
        print(f"Parsed valid property from post {post.get('id')}: {parsed_data['title']}")
        
        # Insert into properties table
        prop_insert = {
            "title": parsed_data["title"],
            "city": parsed_data["city"],
            "listing_mode": parsed_data["mode"],
            "property_type": parsed_data["property_type"],
            "price_numeric": parsed_data["price"],
            "beds": parsed_data["beds"],
            "baths": parsed_data["baths"]
        }
        
        try:
            res = supabase.table('properties').insert(prop_insert).execute()
            inserted_id = res.data[0]['id'] if res.data else None
            
            # If image exists, insert into property_images
            if img_url and inserted_id:
                supabase.table('property_images').insert({
                    "property_id": inserted_id,
                    "image_url": img_url,
                    "is_primary": True
                }).execute()
                
            print(f"Successfully inserted property {inserted_id} into Supabase.")
        except Exception as e:
            print(f"Error inserting into Supabase: {e}")

if __name__ == "__main__":
    sync_meta_posts()
