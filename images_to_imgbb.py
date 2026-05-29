import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle
from tqdm import tqdm

API_KEYS = [
    "f4f17650f24602d0caa2b38043701b6a",
    "e121caa69f546b92408d2d13b1bf347e",
    "d656faaf67bd330817a9b69c32197d09",
    "aa5a02d221d0258002a7112f54d73663",
    "a0fc069c3910b805c30280846cdf3f58",
    "02238a978e12375b45fa85df9df72d20",
]

key_cycle = cycle(API_KEYS)

def upload(img_url):
    key = next(key_cycle)
    try:
        r = requests.post(
            f"https://api.imgbb.com/1/upload?key={key}",
            data={"image": img_url},
            timeout=15,
        )
        data = r.json()
        if data.get("success"):
            return data["data"]["url"]
    except Exception:
        pass
    return None

files = [f for f in os.listdir(".") if f.endswith(".json")]

for path in tqdm(files, desc="Files"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        continue

    tasks = [
        (i, img["url"] if isinstance(img, dict) else img)
        for i, img in enumerate(data.get("images", []))
        if (img["url"] if isinstance(img, dict) else img)
        and "i.ibb.co" not in (img["url"] if isinstance(img, dict) else img)
    ]

    if not tasks:
        continue

    with ThreadPoolExecutor(max_workers=len(API_KEYS)) as executor:
        futures = {executor.submit(upload, url): i for i, url in tasks}
        for future in tqdm(as_completed(futures), total=len(futures), desc=path, leave=False):
            i, new_url = futures[future], future.result()
            if new_url:
                if isinstance(data["images"][i], dict):
                    data["images"][i]["url"] = new_url
                else:
                    data["images"][i] = new_url

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)