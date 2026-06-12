import json, os, glob
from collections import Counter

project_dir = os.path.expanduser("~/.claude/projects/C--Users-ASUS-Desktop-Personnal")
bash_counter = Counter()
mcp_counter = Counter()

for jsonl_file in glob.glob(os.path.join(project_dir, "*.jsonl")):
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                record = json.loads(line)
            except: continue

            msg = record.get('message', {})
            if not isinstance(msg, dict): continue
            content = msg.get('content', [])
            if isinstance(content, str): continue

            for block in content:
                if not isinstance(block, dict): continue
                if block.get('type') != 'tool_use': continue
                name = block.get('name', '')
                if name == 'Bash':
                    cmd = block.get('input', {}).get('command', '').strip()
                    tokens = cmd.split()
                    if not tokens: continue
                    t0 = tokens[0]
                    if t0 in ('sudo', 'timeout') and len(tokens) > 1:
                        t0 = tokens[1]
                    t1 = tokens[1] if len(tokens) > 1 else ''
                    bash_counter[f"{t0} {t1}"] += 1
                elif name.startswith('mcp__'):
                    mcp_counter[name] += 1

print("=== Bash commands ===")
for cmd, cnt in bash_counter.most_common(30):
    print(f"{cnt:4d}  {cmd}")

print(f"\n=== MCP tools ({len(mcp_counter)}) ===")
for tool, cnt in mcp_counter.most_common(20):
    print(f"{cnt:4d}  {tool}")
