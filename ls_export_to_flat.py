import json, sys, pathlib

infile = sys.argv[1]  
outfile = pathlib.Path(infile).with_name("flat_dataset.jsonl")

def get_choice(res, name):
    for r in res:
        if r["from_name"] == name and r["type"] == "choices":
            return r["value"]["choices"][0] if r["value"]["choices"] else None
    return None

def get_multi(res, name):
    for r in res:
        if r["from_name"] == name and r["type"] == "choices":
            return r["value"]["choices"]
    return []

def get_text(res, name):
    for r in res:
        if r["from_name"] == name and r["type"] == "textarea":
            return r["value"]["text"][0] if r["value"]["text"] else ""
    return ""

out = open(outfile, "w", encoding="utf-8")
data = json.load(open(infile, "r", encoding="utf-8"))

for task in data:
    d = task["data"]
    res = task.get("annotations", task.get("completions", []))[0]["result"]
    row = {
        "image": d.get("image"),
        "fabric_image": d.get("fabric_image"),
        "gender": get_choice(res, "gender"),
        "age_group": get_choice(res, "age_group"),
        "skin_tone": get_choice(res, "skin_tone"),
        "body_shape": get_choice(res, "body_shape"),
        "event": get_choice(res, "event"),
        "fabric_type": get_choice(res, "fabric_type"),
        "style": get_choice(res, "style"),
        "accessories": get_multi(res, "accessories"),
        "caption": get_text(res, "caption"),
        "prompt": get_text(res, "prompt")
    }
    out.write(json.dumps(row, ensure_ascii=False) + "\n")

out.close()
print(f"Wrote {outfile}")
