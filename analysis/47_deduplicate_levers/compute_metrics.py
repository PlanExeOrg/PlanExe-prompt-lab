import json
import os

plans = ['20250321_silo', '20250329_gta_game', '20260308_sovereign_identity', '20260310_hong_kong_game', '20260311_parasomnia_research_unit']
runs = {
    '36': 'ollama-llama3.1',
    '37': 'openrouter-openai-gpt-oss-20b',
    '38': 'openai-gpt-5-nano',
    '39': 'openrouter-qwen3-30b-a3b',
    '40': 'openrouter-openai-gpt-4o-mini',
    '41': 'openrouter-gemini-2.0-flash-001',
    '42': 'anthropic-claude-haiku-4-5-pinned',
}
base = '/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab'

def analyze_file(path):
    with open(path) as f:
        data = json.load(f)
    levers = data.get('deduplicated_levers', [])
    if not levers:
        return None
    lever_count = len(levers)
    option_counts = [len(l.get('options', [])) for l in levers]
    exact_3 = sum(1 for c in option_counts if c == 3)
    violations = sum(1 for c in option_counts if c != 3)
    name_lens = [len(l.get('name', '')) for l in levers]
    conseq_lens = [len(l.get('consequences', '')) for l in levers]
    options_lens = [sum(len(o) for o in l.get('options', [])) for l in levers]
    review_lens = [len(l.get('review', '')) for l in levers]
    names = [l.get('name', '') for l in levers]
    unique_names = len(set(names))
    return {
        'lever_count': lever_count,
        'exact_3_options': exact_3,
        'option_violations': violations,
        'avg_name_len': sum(name_lens)/len(name_lens) if name_lens else 0,
        'avg_conseq_len': sum(conseq_lens)/len(conseq_lens) if conseq_lens else 0,
        'avg_options_len': sum(options_lens)/len(options_lens) if options_lens else 0,
        'avg_review_len': sum(review_lens)/len(review_lens) if review_lens else 0,
        'name_uniqueness': unique_names / lever_count if lever_count else 0,
    }

print('=== BASELINE ===')
bl_results = {}
for plan in plans:
    path = f'{base}/baseline/train/{plan}/002-11-deduplicated_levers_raw.json'
    result = analyze_file(path)
    bl_results[plan] = result
    print(f'{plan}: levers={result["lever_count"]}, opt_violations={result["option_violations"]}, avg_conseq={result["avg_conseq_len"]:.0f}, avg_review={result["avg_review_len"]:.0f}, name_uniq={result["name_uniqueness"]:.2f}')

avg_bl = {k: sum(bl_results[p][k] for p in plans)/len(plans) for k in bl_results[plans[0]].keys()}
print(f'BASELINE AVG: levers={avg_bl["lever_count"]:.1f}, opt_violations={avg_bl["option_violations"]:.1f}, avg_name={avg_bl["avg_name_len"]:.0f}, avg_conseq={avg_bl["avg_conseq_len"]:.0f}, avg_options={avg_bl["avg_options_len"]:.0f}, avg_review={avg_bl["avg_review_len"]:.0f}, name_uniq={avg_bl["name_uniqueness"]:.2f}')

print()
all_run_avgs = {}

for run_num, model in runs.items():
    print(f'=== RUN {run_num} ({model}) ===')
    run_results = {}
    for plan in plans:
        path = f'{base}/history/3/{run_num}_deduplicate_levers/outputs/{plan}/002-11-deduplicated_levers_raw.json'
        if os.path.exists(path):
            result = analyze_file(path)
            if result:
                run_results[plan] = result
                print(f'  {plan}: levers={result["lever_count"]}, opt_violations={result["option_violations"]}, avg_conseq={result["avg_conseq_len"]:.0f}, avg_review={result["avg_review_len"]:.0f}, name_uniq={result["name_uniqueness"]:.2f}')
        else:
            print(f'  {plan}: MISSING')
    if run_results:
        valid_plans = list(run_results.keys())
        avg_r = {k: sum(run_results[p][k] for p in valid_plans)/len(valid_plans) for k in run_results[valid_plans[0]].keys()}
        all_run_avgs[run_num] = (model, len(valid_plans), avg_r)
        print(f'  AVG({len(valid_plans)} plans): levers={avg_r["lever_count"]:.1f}, opt_violations={avg_r["option_violations"]:.1f}, avg_name={avg_r["avg_name_len"]:.0f}, avg_conseq={avg_r["avg_conseq_len"]:.0f}, avg_options={avg_r["avg_options_len"]:.0f}, avg_review={avg_r["avg_review_len"]:.0f}, name_uniq={avg_r["name_uniqueness"]:.2f}')

print()
print('=== SUMMARY TABLE ===')
print(f'{"Model":<40} {"Levers":>7} {"Opt_viol":>8} {"AvgName":>8} {"AvgConseq":>10} {"AvgOpts":>8} {"AvgRev":>8} {"NameUniq":>9}')
print(f'{"Baseline (gemini-2.0-flash)":<40} {avg_bl["lever_count"]:>7.1f} {avg_bl["option_violations"]:>8.1f} {avg_bl["avg_name_len"]:>8.0f} {avg_bl["avg_conseq_len"]:>10.0f} {avg_bl["avg_options_len"]:>8.0f} {avg_bl["avg_review_len"]:>8.0f} {avg_bl["name_uniqueness"]:>9.2f}')
for run_num, (model, n_plans, avg_r) in all_run_avgs.items():
    print(f'{model:<40} {avg_r["lever_count"]:>7.1f} {avg_r["option_violations"]:>8.1f} {avg_r["avg_name_len"]:>8.0f} {avg_r["avg_conseq_len"]:>10.0f} {avg_r["avg_options_len"]:>8.0f} {avg_r["avg_review_len"]:>8.0f} {avg_r["name_uniqueness"]:>9.2f}')
