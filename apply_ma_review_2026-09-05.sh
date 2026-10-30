#!/usr/bin/env bash
# script_path: apply_ma_review_2026-09-05.sh
# description: Applies pending docs-ma updates from ma_review_2026-09-05.md.
set -euo pipefail

# Applies the pending docs-ma updates from ma_review_2026-09-05.md
# (verdicts re-verified 2026-09-08: no commits in protolib/whisker/governance since 09-05).
#
# Dry-run by default — prints every `docs` call. Run with --apply to execute.
# Requires the workdocs server (docs service status / doc server) on localhost:9004.
#
# Closes/merges use `docs ma d` per the review's apply note. If you prefer
# soft-close, swap apply_ma::del() body for:
#   docs ma m '{"datetime":"...","status":"closed"}'.

APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

apply_ma::run() {
    if (( APPLY )); then
        docs "$@"
    else
        printf 'DRY-RUN: docs'; printf ' %q' "$@"; printf '\n\n'
    fi
}

apply_ma::mod() {
    # apply_ma::mod <datetime> <description> [extra jq object, e.g. '{priority:"medium"}']
    local dt="$1" desc="$2" extra="${3:-{\}}"
    apply_ma::run ma m "$(jq -n \
        --arg d "$dt" --arg t "$desc" --argjson x "$extra" \
        '{datetime:$d, description:$t} + $x')"
}

apply_ma::del() {
    # apply_ma::del <datetime>
    apply_ma::run ma d "$(jq -n --arg d "$1" '{datetime:$d}')"
}

R="reviewed: 2026-09-08"

# ============================== protolib ==============================
# P1, P2: resolved by landed code (2026-08-24 cS sweep; conftest c8 exemption)
apply_ma::del 2026-07-09_13-41-27.579010
apply_ma::del 2026-07-19_05-33-34.979169

# P3 rewrite: premise inverted
_d="REWRITTEN 2026-09-05: premise inverted. code_style_python.md now EXISTS"
_d+=" (.claude/rules/, cited by 4 skills); kwargs.md absent AND unreferenced"
_d+=" (self-resolved). New live dangle: developer_guidelines.md absent from"
_d+=" protolib+governance but still @ref-ed by code_style_python.md:18,"
_d+=" architecture_python.md:18, code_skeleton_python.md:27. Action: retarget"
_d+=" those 3 refs (~3 LOC); separately repoint the 4 clone pr records (docs pr m)."
_d+=$'\n\n'"$R"
apply_ma::mod 2026-07-27_11-38-51.134602 "$_d"

# P4+P5 merge: keep P4 (merged text), delete P5
_d="Merged w/ 2026-07-27_11-38-58.837722 (2026-09-05). protolib 2026-04"
_d+=" pr-cluster cleanup, docs-only: (1) clone-atomic premise re-confirmed at"
_d+=" HEAD 4bd7e03 (clone.py:261 shutil.copytree, no params.yml on clone path)"
_d+=" — docs ch a then docs pr d on pr 2026-04-18_08-50-38.628353. (2) 3 pr"
_d+=" descriptions truncated at 500-char cap"
_d+=" (2026-04-14_09-18-00.049696/.241207/.310858) — docs pr m concise rewrite."
_d+=" Pure docs ops."
_d+=$'\n\n'"$R"
apply_ma::mod 2026-07-27_11-38-58.800741 "$_d"
apply_ma::del 2026-07-27_11-38-58.837722

# ============================== whisker ===============================
# W1 rewrite
_d="Thinking-model output suppressed only on ollama wire (llm.py:143 think:False);"
_d+=" openai flavor (llm.py:137-140) sends no suppression and _parse_llm_response"
_d+=" has no <think> stripping, so remote reasoning models fail parsing. Decide:"
_d+=" defensive <think> strip (~3 LOC, no behavior change) vs full"
_d+=" thinking-model support (latency implications for push-to-talk)."
_d+=$'\n\n'"$R"
apply_ma::mod 2026-04-10_10-59-44.362109 "$_d"

# W2 keep (updated refs; blocked on human confirm)
_d="Two vocab cases abstain at Tier 1 (cls_bayes.py:143, theta=0.6"
_d+=" settings.py:167); test_semantic_cases_abstain accepts by design; cascade"
_d+=" routes them at Tier 2/3. WAD — close unless corpus enrichment wanted"
_d+=" (~/.whisker/classifier/corpus/translate.training.md, docs-side only)."
_d+=" Do NOT lower the 0.6 threshold. BLOCKED ON HUMAN CONFIRM."
_d+=$'\n\n'"$R"
apply_ma::mod 2026-06-30_12-09-57.186805 "$_d"

# W3 rewrite: blocker stale
_d="prompt.build() (prompt.py:153-160, c37 insert) survives via"
_d+=" router._llm_route (router.py:15) and unmapped-template fallback"
_d+=" (prompt.py:176); pipeline.py already migrated, so in-code note at"
_d+=" prompt.py:143 is stale (fix comment). Retiring build() needs a routes.yaml"
_d+=" entry for the Tier-3 router prompt + stress/edge-case selector re-run"
_d+=" (render() emits single user message, routing accuracy may shift)."
_d+=" Alternative: keep as documented permanent shim."
_d+=$'\n\n'"$R"
apply_ma::mod 2026-07-01_11-04-56.170775 "$_d"

# W4 rewrite: reclassify docs-only -> small code cleanup
_d="Reclassified docs-only -> small code cleanup (2026-09-05). Pipeline"
_d+=" 5-stage decomposition done (pipeline.py:28-76), assistant.py gone, but"
_d+=" core/template_selector.py STILL EXISTS (96 lines, deprecated header,"
_d+=" runtime-dead, imported by 3 test files). Pending: delete/repoint tests"
_d+=" — KEEP stress/edge-case routing corpora (needed for prompt.build"
_d+=" migration) — then docs ch a + docs pr d. No CHANGELOG file in repo."
_d+=$'\n\n'"$R"
apply_ma::mod 2026-07-27_11-38-58.758504 "$_d"

# ============================= governance =============================
# Closes: resolved by landed code (spot-check anchors in ma_review_2026-09-05.md)
apply_ma::del 2026-05-25_05-22-11.255816   # G1 Docstring._parse (successor below)
apply_ma::del 2026-05-26_09-53-09.544248   # G3 --format json landed
apply_ma::del 2026-07-05_15-30-04.539374   # G5 c26 fixer + regression test
apply_ma::del 2026-07-17_05-30-47.699512   # G6 shell helpers premise wrong
apply_ma::del 2026-07-28_12-35-05.086048   # G8 ScanScope landed
apply_ma::del 2026-08-07_05-09-58.357375   # G9 0 c37 in core/+helpers
apply_ma::del 2026-08-11_05-13-03.713244   # G10 expose_api reflowed, max 92 ch

# G7 merged rewrite (absorbs 08-16 dup), priority -> medium
_d="src/governance/app/base.py is 495 lines vs c3 target 300 / MAX 500 — 5"
_d+=" lines from hard error (was 367 on 08-16). Split at the"
_d+=" orchestration/dispatch seam: extract source-run/repo-pass driver or"
_d+=" suppression lane (_allowed/_suppressed_m/_pattern_exempt) into its own"
_d+=" module. Supersedes duplicate 2026-08-16_05-14-31.925331."
_d+=$'\n\n'"$R"
apply_ma::mod 2026-07-27_11-48-41.933530 "$_d" '{"priority":"medium"}'
apply_ma::del 2026-08-16_05-14-31.925331   # G11 dup of G7

# G2 rewrite (close after docstring note is made)
_d="WAD: BaseSchema.set_fields kw-only test_meth feeds the example field"
_d+=" BaseSchema has and OpenaiSchema lacks (function_to_json.py:41/49 vs :104);"
_d+=" pinned by test_function_to_json.py:147-156. Docs-only: record c38 exception"
_d+=" in module docstring, then close. Drop old refactor action"
_d+=" (behavior-changing, breaks 2 tests)."
_d+=$'\n\n'"$R"
apply_ma::mod 2026-05-26_05-11-33.455613 "$_d"

# G4 rewrite: detection landed, fixer missing
_d="Detection landed: b9 (app/blueprint/helpers/b9.py:23-43 + pipes.py PipeTable"
_d+=" VO) checks pipe tables in the bpm lane, but no auto_correct (only"
_d+=" c24/c24_1/c26/c28 have fixers). Add fixer on top of PipeTable (pad rows,"
_d+=" insert missing separator), gate behind gov fix (rewrites .md)."
_d+=" Alternative: leave advisory."
_d+=$'\n\n'"$R"
apply_ma::mod 2026-05-26_10-35-15.548233 "$_d"

# G12 rewrite: stale numbers, sync-owned
_d="core/creator/clone.py: clone 363 / upstream 373 lines vs c3 target 300"
_d+=" (grew via scaffold_blueprint; next sync widens clone). Sync-owned — split"
_d+=" upstream in protolib (seam: scaffold/setup phase vs collect-copy-transform),"
_d+=" then proto-admin sync."
_d+=$'\n\n'"$R"
apply_ma::mod 2026-08-16_05-14-42.012123 "$_d"

# G1 successor (new issue).
_t="Five app-owned front-matter readers still bound the YAML head with"
_t+=" ds.split('\\n\\n',1)[0], truncating block scalars with internal blanks"
_t+=" (bug already fixed in helpers/docstrings.py): c90_1.py:30,"
_t+=" system/c90_2.py:57, cS_desc.py:51, step_headers.py:77, bpm/tree.py:167."
_t+=" Route through Docstring or port _head_end; add block-scalar regression test"
_t+=" to test_docstrings.py (fix currently unprotected)."
_t+=$'\n\n'"$R"
apply_ma::run -r governance ma a \
    "$(jq -n --arg t "$_t" '{repo:"governance", description:$t}')"

if (( ! APPLY )); then
    echo "Dry run complete. Re-run with --apply to execute against localhost:9004."
    echo "Afterwards: refresh all_ma.json and archive ma_review_2026-09-05.md + this."
fi
