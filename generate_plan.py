import json

for num in [10, 11, 12]:
    p = f"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/calculus/lesson_{num}.json"
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    print(f"\n==============================================")
    print(f"LESSON {num} SECTIONS")
    print(f"==============================================")
    for s_idx, sec in enumerate(d["sections"]):
        print(f"\n[{sec['id']}] {sec.get('alias')}")
        print(f"Title: {sec.get('title_bn')}")
        for k in sec:
            if k in ['id', 'alias', 'number_bn', 'title_bn']:
                continue
            if k == 'quote':
                print(f"  quote: {sec['quote'].get('text_bn')} | author: {sec['quote'].get('author_bn')}")
            elif k == 'paragraphs':
                print(f"  paragraphs ({len(sec['paragraphs'])}):")
                for i, para in enumerate(sec['paragraphs']):
                    print(f"    p{i}: {para}")
            elif k == 'formulas':
                print(f"  formulas ({len(sec['formulas'])}):")
                for i, form in enumerate(sec['formulas']):
                    print(f"    f{i}: latex={form.get('latex')} | caption={form.get('caption_bn')}")
            elif k == 'callout':
                print(f"  callout: title={sec['callout'].get('title_bn')} | text={sec['callout'].get('text_bn')}")
            elif k == 'closing_thought_bn':
                print(f"  closing_thought_bn: {sec['closing_thought_bn']}")
