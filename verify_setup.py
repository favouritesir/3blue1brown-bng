import json
from pathlib import Path

reg = json.load(open('data/resource_registry/registry.json', encoding='utf-8'))
print(f"Registry valid! {len(reg['resources'])} resources loaded.")

cat = Path('catalog/index.html')
print(f"Catalog HTML exists: {cat.exists()}, size: {cat.stat().st_size} bytes")

gov = Path('governance/system_health.json')
print(f"Governor health log exists: {gov.exists()}")
