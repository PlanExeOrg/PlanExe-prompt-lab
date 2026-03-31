import json, os

def compute_field_lengths(run_id, base, plans):
    desc_lens = []
    synergy_lens = []
    conflict_lens = []
    for plan in plans:
        fp = f'{base}/{run_id}_enrich_potential_levers/outputs/{plan}/002-12-enriched_levers_raw.json'
        if not os.path.exists(fp):
            continue
        with open(fp) as f:
            d = json.load(f)
        for lev in d.get('characterized_levers', []):
            desc_lens.append(len(lev.get('description', '') or ''))
            synergy_lens.append(len(lev.get('synergy_text', '') or ''))
            conflict_lens.append(len(lev.get('conflict_text', '') or ''))
    n = len(desc_lens)
    if n == 0:
        return 0, 0, 0, 0
    return n, sum(desc_lens)//n, sum(synergy_lens)//n, sum(conflict_lens)//n

base = '/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/4'
plans = ['20250321_silo', '20250329_gta_game', '20260308_sovereign_identity', '20260310_hong_kong_game', '20260311_parasomnia_research_unit']

run_meta = {
    '55': 'ollama-llama3.1',
    '56': 'openrouter-openai-gpt-oss-20b',
    '57': 'openai-gpt-5-nano',
    '58': 'openrouter-qwen3-30b-a3b',
    '59': 'openrouter-openai-gpt-4o-mini',
    '60': 'openrouter-gemini-2.0-flash-001',
    '61': 'anthropic-claude-haiku-4-5-pinned',
    '27': 'ollama-llama3.1',
    '28': 'openrouter-openai-gpt-oss-20b',
    '29': 'openai-gpt-5-nano',
    '30': 'openrouter-qwen3-30b-a3b',
    '31': 'openrouter-openai-gpt-4o-mini',
    '32': 'openrouter-gemini-2.0-flash-001',
    '33': 'anthropic-claude-haiku-4-5-pinned',
}

print("Run | Model | N | Avg desc | Avg synergy | Avg conflict")
print("--- | ----- | - | -------- | ----------- | ------------")
for run_id in ['27', '28', '29', '30', '31', '32', '33', '55', '56', '57', '58', '59', '60', '61']:
    n, desc, syn, conf = compute_field_lengths(run_id, base, plans)
    label = "BEFORE" if int(run_id) < 50 else "AFTER"
    print(f'{run_id} ({label}) | {run_meta[run_id][:30]} | {n} | {desc} | {syn} | {conf}')

print()
print("=== BASELINE ===")
base_dir = '/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/baseline/train'
desc_lens = []
synergy_lens = []
conflict_lens = []
for plan in plans:
    fp = f'{base_dir}/{plan}/002-12-enriched_levers_raw.json'
    if not os.path.exists(fp):
        continue
    with open(fp) as f:
        d = json.load(f)
    for lev in d.get('characterized_levers', []):
        desc_lens.append(len(lev.get('description', '') or ''))
        synergy_lens.append(len(lev.get('synergy_text', '') or ''))
        conflict_lens.append(len(lev.get('conflict_text', '') or ''))
n = len(desc_lens)
if n > 0:
    print(f'Baseline: N={n}, avg_desc={sum(desc_lens)//n}, avg_synergy={sum(synergy_lens)//n}, avg_conflict={sum(conflict_lens)//n}')
