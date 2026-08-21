# scripts/verify_public_news_grounding.py
import requests
import json

BASE_URL = "https://staging.ardhamind.projectair.in/api/live-assistant/query"
CONV_ID = "public_staging_news_grounding_seq_20260821"

queries = [
    "What are the top news that might affect the market today?",
    "Which one matters most?",
    "Why?",
    "Which sector is most exposed?",
    "What time is the next major event?"
]

print("=== STARTING PUBLIC STAGING MULTI-TURN NEWS ACCEPTANCE TEST ===")
for idx, q in enumerate(queries, 1):
    resp = requests.post(BASE_URL, json={"message": q, "conversation_id": CONV_ID})
    data = resp.json()
    print(f"\n--- TURN {idx}: '{q}' ---")
    print(f"ANSWER ACT: {data.get('answer_act')}")
    print(f"INTENTS: {data.get('intent')}")
    print(f"PROVIDER: {data.get('provider')} | MODEL: {data.get('model')} | FALLBACK: {data.get('fallback_used')}")
    print(f"DATA SUFFICIENCY: {data.get('data_sufficiency')}")
    print(f"ANSWER:\n{data.get('answer')}")

print("\n=== TEST COMPLETED SUCCESSFULLY ===")
