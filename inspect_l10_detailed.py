import json

def get_lesson(num):
    with open(f"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/calculus/lesson_{num}.json", "r", encoding="utf-8") as f:
        return json.load(f)

l10 = get_lesson(10)
for idx, s in enumerate(l10["sections"]):
    print(f"=== Sec {idx+1}: {s['id']} ({s['alias']}) ===")
    print("title_bn:", s['title_bn'])
    if 'quote' in s:
        print("quote:", s['quote'])
    print("paragraphs:", len(s.get('paragraphs', [])))
    print("formulas:", len(s.get('formulas', [])))
    print("callout:", s.get('callout'))
    print("closing:", s.get('closing_thought_bn'))
