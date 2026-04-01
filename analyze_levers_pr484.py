import json, os, re

base = '/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab'
plans = ['20250321_silo', '20250329_gta_game', '20260308_sovereign_identity', '20260310_hong_kong_game', '20260311_parasomnia_research_unit']

RUNS_BEFORE = ['2/87', '2/88', '2/89', '2/90', '2/91', '2/92', '2/93']
RUNS_AFTER  = ['5/53', '5/54', '5/55', '5/56', '5/57', '5/58', '5/59']
MODELS      = ['ollama-llama3.1', 'openrouter-openai-gpt-oss-20b', 'openai-gpt-5-nano',
               'openrouter-qwen3-30b-a3b', 'openrouter-openai-gpt-4o-mini',
               'openrouter-gemini-2.0-flash-001', 'anthropic-claude-haiku-4-5-pinned']

def load_levers(run_prefix):
    levers = []
    for plan in plans:
        p = f'{base}/history/{run_prefix}_identify_potential_levers/outputs/{plan}/002-10-potential_levers.json'
        if os.path.exists(p):
            with open(p) as f:
                d = json.load(f)
            if isinstance(d, list):
                for item in d:
                    item['_plan'] = plan
                levers.extend(d)
    return levers

def count_per_plan(run_prefix):
    result = {}
    for plan in plans:
        p = f'{base}/history/{run_prefix}_identify_potential_levers/outputs/{plan}/002-10-potential_levers.json'
        if os.path.exists(p):
            with open(p) as f:
                d = json.load(f)
            result[plan] = len(d) if isinstance(d, list) else 0
        else:
            result[plan] = None
    return result

LOCK_PATTERN = re.compile(r'none of the three options|all three options', re.IGNORECASE)
FAB_PATTERN  = re.compile(r'\b\d+[-\s]*(?:to|-)\s*\d+\s*%|\b\d+\s*%', re.IGNORECASE)

def metrics(levers):
    if not levers:
        return {}

    locked = 0
    fab_count = 0
    review_lens, cons_lens, opts_lens = [], [], []
    opt_counts = []
    for lev in levers:
        r = lev.get('review', '')
        c = lev.get('consequences', '')
        o = lev.get('options', [])
        opts_text = ' '.join(o) if isinstance(o, list) else str(o)
        review_lens.append(len(r))
        cons_lens.append(len(c))
        opts_lens.append(len(opts_text))
        opt_counts.append(len(o) if isinstance(o, list) else 0)
        if LOCK_PATTERN.search(r):
            locked += 1
        full_text = r + c + opts_text
        fab_count += len(FAB_PATTERN.findall(full_text))

    return {
        'count': len(levers),
        'avg_review_len': sum(review_lens)/len(review_lens),
        'avg_cons_len': sum(cons_lens)/len(cons_lens),
        'avg_opts_len': sum(opts_lens)/len(opts_lens),
        'avg_opt_count': sum(opt_counts)/len(opt_counts),
        'template_lock': locked,
        'template_lock_pct': 100*locked/len(levers),
        'fabricated_numbers': fab_count,
        'fab_per_lever': fab_count/len(levers),
    }

print('TEMPLATE LOCK ANALYSIS: PR #484 (Remove template-lock anchor from review_lever)')
print()
print('MODEL-BY-MODEL: TEMPLATE LOCK ("none/all of the three options")')
print()
print(f"{'Model':<42} {'Before Run':^6}  {'Lock-B':^12}  {'After Run':^6}  {'Lock-A':^12}")
print('-' * 80)
for rb, ra, m in zip(RUNS_BEFORE, RUNS_AFTER, MODELS):
    before = metrics(load_levers(rb))
    after = metrics(load_levers(ra))
    if not before or not after:
        print(f"{m:<42}  NO DATA")
        continue
    tb = f"{before['template_lock']}/{before['count']} ({before['template_lock_pct']:.0f}%)"
    ta = f"{after['template_lock']}/{after['count']} ({after['template_lock_pct']:.0f}%)"
    print(f"{m:<42} {rb:^6}   {tb:<14} {ra:^6}   {ta:<14}")

print()
print('FIELD LENGTH COMPARISON (avg chars per lever)')
print()
print(f"{'Model':<42} {'Review-B':>9} {'Review-A':>9} {'Cons-B':>9} {'Cons-A':>9} {'Opts-B':>9} {'Opts-A':>9}")
print('-' * 100)
for rb, ra, m in zip(RUNS_BEFORE, RUNS_AFTER, MODELS):
    before = metrics(load_levers(rb))
    after = metrics(load_levers(ra))
    if not before or not after:
        continue
    print(f"{m:<42} {before['avg_review_len']:>9.0f} {after['avg_review_len']:>9.0f} {before['avg_cons_len']:>9.0f} {after['avg_cons_len']:>9.0f} {before['avg_opts_len']:>9.0f} {after['avg_opts_len']:>9.0f}")

print()
print('LEVER COUNT PER PLAN (haiku only: run 93 vs run 59)')
print()
b93 = count_per_plan('2/93')
a59 = count_per_plan('5/59')
for plan in plans:
    b = b93.get(plan, 'N/A')
    a = a59.get(plan, 'N/A')
    print(f"  {plan}: before={b}, after={a}")

print()
print('SAMPLE REVIEWS: BEFORE (run 93, haiku) - first 5 template-lock examples')
before_haiku = load_levers('2/93')
count = 0
for lev in before_haiku:
    r = lev.get('review', '')
    if LOCK_PATTERN.search(r) and count < 5:
        print(f"  [{lev.get('_plan','')}] {lev.get('name','')}")
        print(f"    {r[:250]}")
        count += 1

print()
print('SAMPLE REVIEWS: AFTER (run 59, haiku) - first 5 levers')
after_haiku = load_levers('5/59')
for lev in after_haiku[:5]:
    r = lev.get('review', '')
    print(f"  [{lev.get('_plan','')}] {lev.get('name','')}")
    print(f"    {r[:250]}")

print()
print('FABRICATED NUMBER CLAIMS (% figures)')
print()
print(f"{'Model':<42} {'FabNums-B':>10} {'FabNums-A':>10} {'PerLever-B':>12} {'PerLever-A':>12}")
print('-' * 90)
for rb, ra, m in zip(RUNS_BEFORE, RUNS_AFTER, MODELS):
    before = metrics(load_levers(rb))
    after = metrics(load_levers(ra))
    if not before or not after:
        continue
    print(f"{m:<42} {before['fabricated_numbers']:>10} {after['fabricated_numbers']:>10} {before['fab_per_lever']:>12.2f} {after['fab_per_lever']:>12.2f}")

print()
print('OPTION COUNT CONSISTENCY (avg options per lever, expected ~3)')
print()
print(f"{'Model':<42} {'AvgOpts-B':>10} {'AvgOpts-A':>10}")
print('-' * 65)
for rb, ra, m in zip(RUNS_BEFORE, RUNS_AFTER, MODELS):
    before = metrics(load_levers(rb))
    after = metrics(load_levers(ra))
    if not before or not after:
        continue
    print(f"{m:<42} {before['avg_opt_count']:>10.2f} {after['avg_opt_count']:>10.2f}")
