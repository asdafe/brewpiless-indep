from pathlib import Path
p = Path('htmljs/dist/english/config.htm')
text = p.read_text(encoding='utf-8', errors='replace')
for col in [2236, 4721, 9076]:
    start = max(0, col - 80)
    end = min(len(text), col + 80)
    snippet = text[start:end]
    print('---', col, '---')
    print(snippet)
    print()
