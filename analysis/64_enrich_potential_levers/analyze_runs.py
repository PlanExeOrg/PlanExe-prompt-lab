import json, os

def analyze_runs(run_ids, base, plans):
    for run in run_ids:
        total_errors = 0
        unknown_id_errors = 0
        incomplete_errors = 0
        total_characterized = 0
        meta_model = "unknown"
        meta_fp = f'{base}/{run}_enrich_potential_levers/meta.json'
        if os.path.exists(meta_fp):
            with open(meta_fp) as f:
                m = json.load(f)
            meta_model = m.get('model', {}).get('primary', 'unknown')
        for plan in plans:
            fp = f'{base}/{run}_enrich_potential_levers/outputs/{plan}/002-12-enriched_levers_raw.json'
            if not os.path.exists(fp):
                continue
            with open(fp) as f:
                d = json.load(f)
            errors = d.get('errors', [])
            total_errors += len(errors)
            unknown_id_errors += sum(1 for e in errors if e.get('type') == 'unknown_lever_id')
            incomplete_errors += sum(1 for e in errors if e.get('type') == 'incomplete')
            total_characterized += len(d.get('characterized_levers', []))
        print(f'Run {run} ({meta_model}): characterized={total_characterized}, errors={total_errors} (unknown_id={unknown_id_errors}, incomplete={incomplete_errors})')

base = '/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/4'
plans = ['20250321_silo', '20250329_gta_game', '20260308_sovereign_identity', '20260310_hong_kong_game', '20260311_parasomnia_research_unit']

print("=== CURRENT RUNS (after PR #464) ===")
analyze_runs(['55', '56', '57', '58', '59', '60', '61'], base, plans)

print()
print("=== PREVIOUS RUNS (before PR #464, used in analysis/60) ===")
analyze_runs(['27', '28', '29', '30', '31', '32', '33'], base, plans)
