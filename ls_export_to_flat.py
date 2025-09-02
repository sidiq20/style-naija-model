import json, sys, pathlib

infile = sys.argv[1]
outfile = pathlib.Path(infile).with_name("style_naija_dataset.jsonl")

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

def get_number(res, name):
    for r in res:
        if r["from_name"] == name and r["type"] == "number":
            return r["value"]["number"]
    return None

def get_date(res, name):
    for r in res:
        if r["from_name"] == name and r["type"] == "datetime":
            return r["value"]["datetime"]
    return None

out = open(outfile, "w", encoding="utf-8")
data = json.load(open(infile, "r", encoding="utf-8"))

for task in data:
    d = task["data"]
    res = task.get("annotations", task.get("completions", []))[0]["result"]

    row = {
        "user_id": d.get("user_id"),
        "photo": d.get("photo"),
        "fabric_image": d.get("fabric_image"),
        "style_reference_image": d.get("style_reference_image"),

        "gender": get_choice(res, "gender"),
        "body_shape": get_choice(res, "body_shape"),
        "fabric_type": get_choice(res, "fabric_type"),
        "occasion_type": get_choice(res, "occasion_type"),
        "preferred_style_type": get_choice(res, "preferred_style_type"),
        "region": get_choice(res, "region"),

        # Optional preferences
        "fit_preference": get_choice(res, "fit_preference"),
        "sleeve_preference": get_choice(res, "sleeve_preference"),
        "length_preference": get_choice(res, "length_preference"),
        "neckline_preference": get_choice(res, "neckline_preference"),

        # Free text fields
        "style_description": get_text(res, "style_description"),
        "accessory_preference": get_text(res, "accessory_preference"),

        # Numbers
        "height_cm": get_number(res, "height_cm"),
        "weight_kg": get_number(res, "weight_kg"),
        "budget_estimate": get_number(res, "budget_estimate"),
        "fabric_yardage": get_number(res, "fabric_yardage"),

        # Submission date
        "submission_date": get_date(res, "submission_date"),
    }

    out.write(json.dumps(row, ensure_ascii=False) + "\n")

out.close()
print(f"Wrote {outfile}")
