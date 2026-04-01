import json, os, re

def analyze_run(run_dir):
    plans_dir = run_dir + '/outputs'
    if not os.path.exists(plans_dir):
        return None
    plans = os.listdir(plans_dir)
    results = {}
    for plan in plans:
        lever_file = plans_dir + '/' + plan + '/002-10-potential_levers.json'
        if not os.path.exists(lever_file):
            results[plan] = None
            continue
        with open(lever_file) as f:
            data = json.load(f)
        levers = data if isinstance(data, list) else data.get('levers', [])
        lever_stats = []
        for lev in levers:
            cons = lev.get('consequences', '') or ''
            opts = lev.get('options', [])
            if isinstance(opts, list) and opts and isinstance(opts[0], dict):
                opt_text = ' '.join([o.get('description', '') for o in opts])
            elif isinstance(opts, list):
                opt_text = ' '.join([str(o) for o in opts])
            else:
                opt_text = str(opts)
            rev = lev.get('review', lev.get('review_lever', '')) or ''
            lever_stats.append({
                'name': lev.get('name', ''),
                'cons_len': len(cons),
                'opt_len': len(opt_text),
                'rev_len': len(rev),
                'num_options': len(opts) if isinstance(opts, list) else 1,
                'cons_text': cons[:200],
                'rev_text': rev[:200],
                'review_is_consequence_repeat': cons.strip()[:50].lower() in rev.lower() if cons and rev else False,
                'has_fabricated_numbers': bool(re.search(r'\d+%|\d+\s*percent|\$\d+|\d+x\b', cons + rev + opt_text, re.I))
            })
        results[plan] = lever_stats
    return results

print('=== AFTER RUNS (39-45) ===')
after_base = '/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/5'
after_models = {39:'llama3.1', 40:'gpt-oss-20b', 41:'gpt-5-nano', 42:'qwen3-30b', 43:'gpt-4o-mini', 44:'gemini-2.0-flash', 45:'haiku-4.5'}
all_after = {}
for i in range(39, 46):
    run_dir = after_base + '/' + str(i) + '_identify_potential_levers'
    res = analyze_run(run_dir)
    all_after[i] = res
    if res is None:
        print('Run ' + str(i) + ' (' + after_models[i] + '): NO DATA')
        continue
    lever_counts = [len(v) for v in res.values() if v is not None]
    missing = sum(1 for v in res.values() if v is None)
    all_levers = [l for v in res.values() if v for l in v]
    total = len(all_levers)
    if total == 0:
        print('Run ' + str(i) + ' (' + after_models[i] + '): 0 levers')
        continue
    avg_c = sum(l['cons_len'] for l in all_levers) / total
    avg_o = sum(l['opt_len'] for l in all_levers) / total
    avg_r = sum(l['rev_len'] for l in all_levers) / total
    template_locks = sum(1 for l in all_levers if l['review_is_consequence_repeat'])
    fab_nums = sum(1 for l in all_levers if l['has_fabricated_numbers'])
    avg_opts = sum(l['num_options'] for l in all_levers) / total
    print('Run %d (%s): %d/%d levers, missing=%d, avg_cons=%.0f, avg_opt=%.0f, avg_rev=%.0f, template_lock=%d/%d, fab_nums=%d/%d, avg_opts=%.1f' % (
        i, after_models[i], sum(lever_counts), len(res)*5, missing, avg_c, avg_o, avg_r, template_locks, total, fab_nums, total, avg_opts))

print()
print('=== BEFORE RUNS (87-93) ===')
before_base = '/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/2'
before_models = {87:'llama3.1', 88:'gpt-oss-20b', 89:'gpt-5-nano', 90:'qwen3-30b', 91:'gpt-4o-mini', 92:'gemini-2.0-flash', 93:'haiku-4.5'}
all_before = {}
for i in range(87, 94):
    run_dir = before_base + '/' + str(i) + '_identify_potential_levers'
    res = analyze_run(run_dir)
    all_before[i] = res
    if res is None:
        print('Run ' + str(i) + ' (' + before_models[i] + '): NO DATA')
        continue
    lever_counts = [len(v) for v in res.values() if v is not None]
    missing = sum(1 for v in res.values() if v is None)
    all_levers = [l for v in res.values() if v for l in v]
    total = len(all_levers)
    if total == 0:
        print('Run ' + str(i) + ' (' + before_models[i] + '): 0 levers')
        continue
    avg_c = sum(l['cons_len'] for l in all_levers) / total
    avg_o = sum(l['opt_len'] for l in all_levers) / total
    avg_r = sum(l['rev_len'] for l in all_levers) / total
    template_locks = sum(1 for l in all_levers if l['review_is_consequence_repeat'])
    fab_nums = sum(1 for l in all_levers if l['has_fabricated_numbers'])
    avg_opts = sum(l['num_options'] for l in all_levers) / total
    print('Run %d (%s): %d/%d levers, missing=%d, avg_cons=%.0f, avg_opt=%.0f, avg_rev=%.0f, template_lock=%d/%d, fab_nums=%d/%d, avg_opts=%.1f' % (
        i, before_models[i], sum(lever_counts), len(res)*5, missing, avg_c, avg_o, avg_r, template_locks, total, fab_nums, total, avg_opts))

print()
print('=== PER-MODEL COMPARISON ===')
model_map = {
    'llama3.1': (39, 87),
    'gpt-oss-20b': (40, 88),
    'gpt-5-nano': (41, 89),
    'qwen3-30b': (42, 90),
    'gpt-4o-mini': (43, 91),
    'gemini-2.0-flash': (44, 92),
    'haiku-4.5': (45, 93)
}

def get_stats(res):
    if not res:
        return None
    all_levers = [l for v in res.values() if v for l in v]
    total = len(all_levers)
    if total == 0:
        return None
    return {
        'count': total,
        'plans_success': sum(1 for v in res.values() if v is not None),
        'avg_cons': sum(l['cons_len'] for l in all_levers) / total,
        'avg_opt': sum(l['opt_len'] for l in all_levers) / total,
        'avg_rev': sum(l['rev_len'] for l in all_levers) / total,
        'template_locks': sum(1 for l in all_levers if l['review_is_consequence_repeat']),
        'fab_nums': sum(1 for l in all_levers if l['has_fabricated_numbers']),
    }

for model, runs in model_map.items():
    after_run, before_run = runs
    after_stats = get_stats(all_after.get(after_run))
    before_stats = get_stats(all_before.get(before_run))
    if after_stats and before_stats:
        rev_delta = after_stats['avg_rev'] - before_stats['avg_rev']
        cons_delta = after_stats['avg_cons'] - before_stats['avg_cons']
        print('%s: rev_len before=%.0f after=%.0f delta=%+.0f | cons_len before=%.0f after=%.0f delta=%+.0f | template_lock before=%d/%d after=%d/%d' % (
            model, before_stats['avg_rev'], after_stats['avg_rev'], rev_delta,
            before_stats['avg_cons'], after_stats['avg_cons'], cons_delta,
            before_stats['template_locks'], before_stats['count'],
            after_stats['template_locks'], after_stats['count']))

print()
print('=== QWEN3-30B REVIEW FIELD SAMPLES ===')
qwen_after = all_after.get(42, {})
qwen_before = all_before.get(90, {})
print('AFTER (run 42):')
if qwen_after:
    all_levers = [l for v in qwen_after.values() if v for l in v]
    for l in all_levers[:5]:
        print('  name: ' + l['name'])
        print('  review: ' + l['rev_text'][:200])
        print()
print('BEFORE (run 90):')
if qwen_before:
    all_levers = [l for v in qwen_before.values() if v for l in v]
    for l in all_levers[:5]:
        print('  name: ' + l['name'])
        print('  review: ' + l['rev_text'][:200])
        print()
