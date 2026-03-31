import json, os

def per_plan(run_id, base, plans):
    results = {}
    for plan in plans:
        fp = f'{base}/{run_id}_enrich_potential_levers/outputs/{plan}/002-12-enriched_levers_raw.json'
        if not os.path.exists(fp):
            results[plan] = ('missing', 0, 0, 0)
            continue
        with open(fp) as f:
            d = json.load(f)
        errors = d.get('errors', [])
        unk = sum(1 for e in errors if e.get('type') == 'unknown_lever_id')
        inc = sum(1 for e in errors if e.get('type') == 'incomplete')
        char = len(d.get('characterized_levers', []))
        results[plan] = ('ok', char, unk, inc)
    return results

base = '/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/4'
plans = ['20250321_silo', '20250329_gta_game', '20260308_sovereign_identity', '20260310_hong_kong_game', '20260311_parasomnia_research_unit']

run_labels = {
    '55': 'llama3.1 AFTER',
    '27': 'llama3.1 BEFORE',
    '57': 'gpt-5-nano AFTER',
    '29': 'gpt-5-nano BEFORE',
    '56': 'gpt-oss-20b AFTER',
    '28': 'gpt-oss-20b BEFORE',
    '61': 'haiku AFTER',
    '33': 'haiku BEFORE',
}

for run_id in ['27', '55', '29', '57', '28', '56', '33', '61']:
    print(f"\n=== {run_labels[run_id]} (run {run_id}) ===")
    r = per_plan(run_id, base, plans)
    for plan, (status, char, unk, inc) in r.items():
        print(f"  {plan}: char={char}, unknown_id={unk}, incomplete={inc}")
