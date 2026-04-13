"""Fix encoding issues in all_generated_params.py"""
import os, ast, re

gp = 'phase3/generated_params'
params = {}

for f in sorted(os.listdir(gp)):
    if not f.endswith('_params.py') or f == 'all_generated_params.py':
        continue
    name = f.replace('_params.py', '')
    filepath = os.path.join(gp, f)
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    
    if name == 'judge':
        # Judge has two dicts: JUDGE_PRE_TRIGGER and JUDGE_POST_TRIGGER
        # Extract both
        pre_match = re.search(r'JUDGE_PRE_TRIGGER\s*=\s*(\{[^}]+\})', content, re.DOTALL)
        post_match = re.search(r'JUDGE_POST_TRIGGER\s*=\s*(\{[^}]+\})', content, re.DOTALL)
        
        if pre_match and post_match:
            pre = ast.literal_eval(pre_match.group(1))
            post = ast.literal_eval(post_match.group(1))
            params['judge_pre_trigger'] = pre
            params['judge_post_trigger'] = post
            print(f"  {name}: loaded pre_trigger + post_trigger")
        else:
            # Try nested dict approach
            print(f"  {name}: WARNING - couldn't find pre/post trigger dicts")
            print(f"    Content preview: {content[:200]}")
    else:
        # Find the first { ... } block
        # Use a brace-counting approach for robustness
        start = content.find('{')
        if start < 0:
            print(f"  {name}: WARNING - no dict found")
            continue
        
        depth = 0
        end = start
        for i in range(start, len(content)):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        
        try:
            d = ast.literal_eval(content[start:end])
            params[name] = d
            print(f"  {name}: OK ({len(d)} keys)")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")
            print(f"    Content: {content[start:start+200]}")

# Write clean combined file
out_path = os.path.join(gp, 'all_generated_params.py')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('"""LLM-generated parameters for all archetypes."""\n\n')
    f.write('GENERATED_PARAMS = {\n')
    for key in sorted(params.keys()):
        f.write(f'    {key!r}: {params[key]!r},\n')
    f.write('}\n')

print(f"\nWrote {out_path} with {len(params)} entries: {sorted(params.keys())}")

# Also fix __init__.py
init_path = os.path.join(gp, '__init__.py')
with open(init_path, 'w', encoding='utf-8') as f:
    f.write('from .all_generated_params import GENERATED_PARAMS\n')

print(f"Fixed {init_path}")
