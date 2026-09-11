#!/usr/bin/env python3
"""Generic, fail-closed control plane for a mathematical-modeling project.

This file intentionally contains no contest-specific constants, models, papers,
or solver code. A real project is created with ``new-run`` and progresses only
when its own evidence artifacts are registered and accepted at each Gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GATES = [f"G{i}" for i in range(10)]
NEXT = {f"G{i}": [f"G{i + 1}"] for i in range(9)} | {"G9": []}
REQUIRED_OUTPUT_IDS = {
    "G0": ["input_audit", "contest_profile"],
    "G1": ["problem_contract", "variable_unit_record", "claim_ladder", "problem_analysis_contract", "requirement_trace_matrix"],
    "G2": ["source_unit_ledger", "assumption_validation_route"],
    "G3": ["model_card", "formula_registry", "formula_derivation_ledger", "mathematical_sanity_checks", "predicate_contract", "discretization_aggregation_contract", "coupling_and_route_map", "model_object_figure_specs"],
    "G4": ["code_mapping", "solver_evidence_plan", "run_record"],
    "G5": ["validation_matrix"],
    "G6": ["visualization_blueprint", "figure_model_crosswalk", "figure_cards"],
    "G7": ["authoring_plan", "paper_traceability", "reverse_outline", "citation_claim_map", "analysis_derivation_coverage", "ai_usage_ledger"],
    "G8": ["build_semantic_audit", "submission_manifest", "human_review_record"],
    "G9": ["retrospective"],
}
# These dependency edges make changes to upstream analysis or derivations
# fail-closed: `invalidate` follows them transitively into figures and paper.
ARTIFACT_REQUIRED_DEPENDENCIES = {
    "requirement_trace_matrix": ["problem_contract", "variable_unit_record"],
    "coupling_and_route_map": ["problem_analysis_contract", "requirement_trace_matrix"],
    "formula_derivation_ledger": ["problem_analysis_contract", "requirement_trace_matrix"],
    "mathematical_sanity_checks": ["formula_derivation_ledger"],
    "predicate_contract": ["formula_derivation_ledger"],
    "discretization_aggregation_contract": ["formula_derivation_ledger"],
    "code_mapping": ["formula_registry", "formula_derivation_ledger"],
    "model_object_figure_specs": ["problem_analysis_contract", "coupling_and_route_map", "formula_derivation_ledger"],
    "visualization_blueprint": ["problem_analysis_contract", "coupling_and_route_map", "formula_derivation_ledger", "model_object_figure_specs"],
    "figure_model_crosswalk": ["visualization_blueprint", "model_object_figure_specs", "formula_derivation_ledger"],
    "figure_cards": ["visualization_blueprint", "figure_model_crosswalk"],
    "paper_traceability": ["requirement_trace_matrix", "formula_derivation_ledger", "figure_model_crosswalk"],
    "analysis_derivation_coverage": ["paper_traceability", "problem_analysis_contract", "formula_derivation_ledger"],
}
GATE_META = {
    "G0": ("启动与规则", "math-modeling", []),
    "G1": ("读题锁定", "math-modeling-problem-framing", ["math-reasoning"]),
    "G2": ("数据证据", "math-modeling-evidence", ["data-analysis"]),
    "G3": ("模型路线", "math-modeling", ["math-reasoning", "algorithm-design"]),
    "G4": ("求解", "math-modeling-solver", ["algorithm-design", "experiment-code"]),
    "G5": ("实验验证", "math-modeling-experiments", ["experiment-design", "experiment-pipeline"]),
    "G6": ("图表", "math-modeling-figures", ["imagegen", "table-generation"]),
    "G7": ("论文", "math-modeling-paper", ["paper-writing-section", "citation-management"]),
    "G8": ("终审提交", "math-modeling-final-audit", ["latex-compile", "latex-formatting", "pdf"]),
    "G9": ("复盘", "math-modeling-retrospective", []),
}

# Inject this text only into an actual imagegen call via compose_imagegen_prompt.
IMAGEGEN_SYSTEM_PROMPT = """Visual direction for this ImageGen call only.
Create the requested academic figure from the supplied figure specification.
Honor the user's reference, medium, palette and publication requirements.
Do not impose a subject-specific scene, fixed style or a second figure version.
Preserve specified objects, relationships, boundaries and arrow directions.
Never invent data, equations, citations, units, outcomes or scientific claims.
Use supplied labels; leave space for precise typesetting when necessary.
A generated image requires semantic and visual review before publication.
For quantitative charts, retain the computed data geometry and exact axes;
generated decorative or explanatory elements cannot replace the evidence plot.
Record the exact prompt, references, output, hash and verification outcome.
"""

IMAGE_POLICY = {
    "default_raster_skill": "imagegen",
    "imagegen_system_prompt": "compose_imagegen_prompt() provides per-call visual instructions",
    "figure_workflow": "specification -> actual ImageGen call -> label and geometry verification -> publication inspection",
    "quantitative_integrity": "computed curves, axes, tables and numeric labels remain linked to actual data and reproducible code",
    "imagegen_record": ["prompt", "input_image_roles", "output_path", "output_sha256", "claim_boundary", "verification"],
    "prohibition": "a generated image never establishes a mathematical, numerical, causal or optimality claim",
}

MATH_REASONING_POLICY = {
    "controller": "math-modeling",
    "formalization_skill": "math-reasoning",
    "G1": ["problem contract", "variables/units record", "problem-analysis contract: deliverables / scoring objects / decisions / uncertainty / acceptance", "requirement-to-output trace matrix", "complete-versus-conditional decision-domain label", "claim ladder (direct / conditional / approximation / not-proven)"],
    "G2": ["source/unit ledger", "assumption impact and validation route"],
    "G3": ["model card", "formula registry", "formula-derivation ledger: motivating question / premises / transformations / theorem or lemma / units / boundary checks / code and test mappings", "mathematical sanity checks", "model-object figure specifications: identify the actual mathematical objects, view/projection, boundaries, variables and formula-to-object correspondence", "bounded predicate contract with degeneracy/tolerance tests when geometry or event visibility is used", "discretization/aggregation contract with visible-set rationale and union/intersection semantics", "coupling-and-route map with at least two candidate routes and rejection reasons", "theorem-or-approximation obligation for every whole/exact/complete claim", "reduction/decomposition ledger when a joint domain is split", "model-minimality/generalization rationale when direct data fitting is considered"],
    "G4": ["variable/constraint-to-code mapping", "seed/budget/operator/acceptance/stopping/runtime/status", "initialization escape check for null/zero-feasibility regions", "root/bisection bracket and continuity-or-monotonicity evidence when endpoint search is used", "solver-comparison plan or a claim downgrade record", "allocation/decomposition baseline for mixed discrete tasks when applicable"],
    "G5": ["separate numerical, sampling, strategy, search and applicability evidence", "one final evaluator", "sample-layout sensitivity (not merely sample count) and dense-evaluator reoptimization when spatial/sample stability is claimed", "overlap/synergy test for multi-intervention aggregation", "independent-solver evidence or an explicit no-superiority boundary"],
}

# Award-winning exemplars are a review rubric, never a source of a new run's
# data, code, text, numerical result, or unverified method claim.
EXEMPLAR_REVIEW_POLICY = {
    "G0": ["optional exemplar register: source URL/path, issuer, version/date, retrieval evidence, and evidence level"],
    "G3": ["claim ladder links every strong term (whole, exact, complete, robust, optimal, significant) to a proof, experiment, or downgrade", "a geometric/event predicate must distinguish line, ray and bounded segment domains; an unbounded-intersection test alone cannot support an in-between claim"],
    "G4": ["if a mixed discrete-continuous problem is decomposed, record the original domain, allocation contract, omitted couplings, and a comparable baseline"],
    "G5": ["do not use integration convergence as search-quality, physical-validity, or continuous-domain evidence; test each claim on its own layer", "multi-action effects use an explicit union/intersection/weighted aggregation, never a raw sum unless disjointness is proven"],
    "G6": ["pre-result visualization blueprint: problem structure / model-object or formula-explanation / result-evidence figures", "figure-model crosswalk: requirement, object, boundary, variable, formula and evidence mapping", "one figure card per displayed figure: question, source/evaluator, units, comparison, supported claim, boundary, visual legibility check", "deterministic visual inspection: readable 8pt labels, non-overlap, non-default ticks, color semantics and no information-free whitespace"],
    "G7": ["reverse outline and per-subproblem closure: objective, variables/constraints, method, deliverable, comparison, conclusion", "analysis-and-derivation coverage check for every paper section", "abstract contract: problem, method, key results, one validation sentence, and scope boundary—not a run log", "citation-claim map and language/typography consistency audit"],
    "G8": ["two-pass source build, semantic PDF comparison, all-page visual inspection, and unresolved-claim report"],
    "anti_copy": "Exemplars may inform a checklist only. Never transfer their wording, data, strategies, numerical values, figures, code, or claims into a project evidence chain.",
}

# G0 is evidence-first. A local file is not an official rule merely because it
# has a plausible name, and an official URL is not a usable source until its
# version, scope and retrieval evidence are recorded in the run package.
G0_INPUT_AUDIT_POLICY = {
    "G0": [
        "Search the current workspace first for every cited rule, template, dataset and attachment; record the scoped paths and SHA-256 values.",
        "For each rule or standard absent from the workspace, verify it at the issuing organization's official domain; record URL, title, version/effective date, retrieval time, scope, and SHA-256 when a file is available.",
        "Do not treat search snippets, mirrors, or unverifiable copies as a substitute for an official source. Record a locator and blocker if official retrieval is unavailable.",
        "Keep the workspace-search result and official-verification result separate so provenance, conflicts, and remaining limitations are auditable.",
    ],
}


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def checked_relative(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit("artifact paths must be relative to the declared run root and may not contain '..'")
    return path


def gate_record(gate: str) -> dict:
    title, owner, skills = GATE_META[gate]
    return {
        "id": gate, "title": title, "gate_owner": owner, "execution_skills": skills,
        "input_artifacts": [], "output_artifacts": [], "status": "pending", "blocker": [],
        "allowed_next_gate": NEXT[gate],
        "required_output_ids": REQUIRED_OUTPUT_IDS[gate],
        "input_audit_requirements": G0_INPUT_AUDIT_POLICY.get(gate, []),
        "mathematical_reasoning_requirements": MATH_REASONING_POLICY.get(gate, []),
        "exemplar_and_paper_review_requirements": EXEMPLAR_REVIEW_POLICY.get(gate, []),
    }


def template_artifacts() -> dict:
    files = {
        "template_contest_profile": "templates/contest_profile.md",
        "template_ai_usage_ledger": "templates/ai_usage_ledger.csv",
        "template_ai_usage_details": "templates/ai_usage_details.md",
        "template_human_review_record": "templates/human_review_record.md",
        "template_submission_manifest": "templates/submission_manifest.csv",
        "template_meta_task": "templates/meta_task.md",
        "template_model_card": "templates/math_reasoning_model_card.md",
        "template_formula_registry": "templates/formula_registry.csv",
        "template_reasoning_flow": "templates/reasoning_flow.md",
        "template_imagegen_policy": "templates/imagegen_call_contract.md",
        "template_claim_ladder": "templates/claim_ladder.csv",
        "template_solver_evidence_plan": "templates/solver_evidence_plan.md",
        "template_figure_card": "templates/figure_card.md",
        "template_exemplar_review": "templates/exemplar_review_protocol.md",
        "template_predicate_contract": "templates/predicate_contract.md",
        "template_discretization_aggregation_contract": "templates/discretization_aggregation_contract.md",
        "template_problem_analysis_contract": "templates/problem_analysis_contract.md",
        "template_requirement_trace_matrix": "templates/requirement_trace_matrix.csv",
        "template_coupling_and_route_map": "templates/coupling_and_route_map.md",
        "template_formula_derivation_ledger": "templates/formula_derivation_ledger.csv",
        "template_model_object_figure_specs": "templates/model_object_figure_specs.md",
        "template_derivation_dependency_graph": "templates/derivation_dependency_graph.md",
        "template_mathematical_sanity_checks": "templates/mathematical_sanity_checks.md",
        "template_visualization_blueprint": "templates/visualization_blueprint.md",
        "template_figure_model_crosswalk": "templates/figure_model_crosswalk.csv",
        "template_figure_formula_crosswalk_legacy": "templates/figure_formula_crosswalk.csv",
        "template_analysis_derivation_coverage": "templates/analysis_derivation_coverage.csv",
    }
    return {
        aid: {"path": rel, "source": "generic workflow template", "status": "usable",
              "depends_on": [], "allowed_next_gate": "G1", "sha256": sha(ROOT / rel)}
        for aid, rel in files.items()
    }


def new_state(run_id: str, artifact_root: str) -> dict:
    gates = {gate: gate_record(gate) for gate in GATES}
    gates["G0"]["status"] = "active"
    return {
        "schema": "mm-workflow/v8", "paper_contract": True, "kind": "generic_math_modeling_control_plane",
        "run_id": run_id, "created_at": utc(), "artifact_root": artifact_root,
        "active_gate": "G0", "evidence_status": "not_usable", "approved_model_route": None,
        "accepted_result_ids": [], "paper_ready_claim_ids": [], "open_blockers": [],
        "workflow_policies": {
            "g0_input_audit": G0_INPUT_AUDIT_POLICY,
            "image_generation": IMAGE_POLICY,
            "mathematical_reasoning": MATH_REASONING_POLICY,
            "exemplar_and_paper_review": EXEMPLAR_REVIEW_POLICY,
            "meta_prompt": {"adapter": "META_PROMPT_INTEGRATION.md", "prompt_role": "stage-specific task specification, never evidence", "public_reference": "META_PROMPT_INTEGRATION.md"},
        },
        "gates": gates, "artifacts": template_artifacts() if artifact_root == "." else {},
    }


def active_state_path() -> Path:
    return ROOT / "state" / "workflow_state.json"


def artifact_base(state: dict) -> Path:
    return ROOT / checked_relative(state["artifact_root"])


def compose_imagegen_prompt(task_prompt: str) -> str:
    """Return the exact prompt envelope required for a genuine imagegen call."""
    return f"{IMAGEGEN_SYSTEM_PROMPT}\n\nCaller task:\n{task_prompt.strip()}"


def check_state(state_path: Path) -> dict:
    """Read-only mechanical checks; this is not a mathematical review."""
    state = load(state_path)
    base = artifact_base(state)
    artifacts = state.get("artifacts", {})
    integrity = []
    gate = state["active_gate"]
    record = state["gates"][gate]
    required = record.get("required_output_ids", REQUIRED_OUTPUT_IDS[gate])
    missing = [aid for aid in required if aid not in artifacts]
    missing += [aid for aid, item in artifacts.items() if item.get("status") == "missing"]
    unusable = [aid for aid in required if aid in artifacts and artifacts[aid].get("status") not in {"usable", "read"}]
    invalidated = [aid for aid, item in artifacts.items() if item.get("status") == "invalidated"]
    for aid, item in artifacts.items():
        if item.get("status") not in {"usable", "read", "active"}:
            continue
        if not item.get("path"):
            integrity.append({"artifact": aid, "issue": "path_missing"})
            continue
        path = base / checked_relative(item["path"])
        if not path.is_file():
            integrity.append({"artifact": aid, "issue": "file_missing", "path": item["path"]})
        elif not item.get("sha256"):
            integrity.append({"artifact": aid, "issue": "sha256_missing"})
        elif sha(path) != item["sha256"]:
            integrity.append({"artifact": aid, "issue": "sha256_mismatch", "path": item["path"]})
        for dep in item.get("depends_on", []):
            if dep not in artifacts or artifacts[dep].get("status") not in {"usable", "read"}:
                integrity.append({"artifact": aid, "issue": "dependency_not_usable", "dependency": dep})
    visiting, visited = set(), set()
    def visit(aid):
        if aid in visiting:
            integrity.append({"artifact": aid, "issue": "dependency_cycle"})
            return
        if aid in visited:
            return
        visiting.add(aid)
        for dep in artifacts.get(aid, {}).get("depends_on", []):
            visit(dep)
        visiting.remove(aid)
        visited.add(aid)
    for aid in artifacts:
        visit(aid)
    blockers = list(state.get("open_blockers", []))
    for item in state["gates"].values():
        blockers.extend(item.get("blocker", []))
    blockers = list(dict.fromkeys(blockers))
    # New runs bind paper acceptance to a fresh content/build check, not a saved PASS.
    if state.get("paper_contract") and gate in {"G7", "G8", "G9"}:
        item = artifacts.get("authoring_plan")
        if not item:
            blockers.append("B-PAPER-CONTRACT: register an actual paper-plan.json before accepting paper stages")
        else:
            try:
                package_root = Path(__file__).resolve().parents[1]
                sys.path.insert(0, str(package_root))
                try:
                    from scripts.paper import audit, verify
                finally:
                    sys.path.pop(0)
                plan_path = base / checked_relative(item["path"])
                if plan_path.name != "paper-plan.json":
                    raise ValueError("authoring plan must be named paper-plan.json")
                paper_report = audit(plan_path.parent) if gate == "G7" else verify(plan_path.parent)
                if paper_report["status"] != "PASS":
                    blockers.extend("B-PAPER-CONTENT: " + issue for issue in paper_report["errors"])
            except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
                blockers.append("B-PAPER-CONTRACT: " + str(exc))
    if integrity:
        blockers.append("B-STATE-INTEGRITY: registered evidence or its dependencies changed; invalidate and repair before advancing.")
    prior_not_passed = [g for g in GATES[:GATES.index(gate)] if state["gates"][g]["status"] != "passed"]
    if prior_not_passed:
        blockers.append("B-GATE-ORDER: prior gates have not passed: " + ",".join(prior_not_passed))
    if blockers:
        next_step = f"Resolve blockers for {gate}; do not advance."
    elif missing or unusable:
        next_step = f"Create and register missing/usable evidence for {gate}; do not accept yet."
    elif record["status"] == "passed" and not NEXT[gate]:
        next_step = "All Gates are passed; preserve this run as frozen evidence."
    else:
        next_step = f"Review the evidence content for {gate}, then accept it with a concrete review note."
    return {
        "state": str(state_path), "run_id": state["run_id"], "current_gate": gate,
        "gate_status": record["status"], "missing_artifacts": list(dict.fromkeys(missing)),
        "unusable_required_artifacts": unusable, "required_output_ids": required,
        "invalidated_artifacts": invalidated, "integrity_failures": integrity,
        "blockers": blockers, "allowed_next_gate": NEXT[gate], "next_step": next_step,
        "review_boundary": "Existence, hashes and dependency checks do not certify mathematics, citations or human review.",
    }


def register_artifact(args: argparse.Namespace) -> None:
    state_path = Path(args.state); state = load(state_path); base = artifact_base(state)
    rel = checked_relative(args.path); path = base / rel
    existing = state["artifacts"].get(args.id)
    if existing and existing.get("status") != "invalidated":
        raise SystemExit(f"refusing to overwrite existing artifact record: {args.id}")
    if args.status in {"usable", "read", "active"} and not path.is_file():
        raise SystemExit(f"cannot register absent accepted artifact: {path}")
    dependencies = split_csv(args.depends_on)
    missing_dependencies = [aid for aid in ARTIFACT_REQUIRED_DEPENDENCIES.get(args.id, []) if aid not in dependencies]
    if missing_dependencies:
        raise SystemExit(f"cannot register {args.id}; missing_declared_dependencies={missing_dependencies}")
    if args.id in dependencies:
        raise SystemExit("an artifact cannot depend on itself")
    bad_dependencies = [aid for aid in dependencies if aid not in state["artifacts"] or state["artifacts"][aid].get("status") not in {"usable", "read"}]
    if bad_dependencies:
        raise SystemExit(f"dependencies must be registered and usable first: {bad_dependencies}")
    pending = list(dependencies)
    seen = set()
    while pending:
        aid = pending.pop()
        if aid == args.id:
            raise SystemExit("artifact dependency cycle")
        if aid not in seen:
            seen.add(aid)
            pending.extend(state["artifacts"].get(aid, {}).get("depends_on", []))
    state["artifacts"][args.id] = {
        "path": str(rel), "source": args.source, "status": args.status,
        "depends_on": dependencies, "allowed_next_gate": args.allowed_next_gate,
        **({"sha256": sha(path)} if path.exists() else {}),
    }
    dump(state_path, state)
    action = "reregistered" if existing else "registered"
    print(json.dumps({action: args.id, "state": str(state_path)}, ensure_ascii=False))


def accept_gate(args: argparse.Namespace) -> None:
    state_path = Path(args.state); state = load(state_path); gate = args.gate
    if gate != state["active_gate"]:
        raise SystemExit(f"only the active Gate may be accepted: active={state['active_gate']}, requested={gate}")
    record = state["gates"][gate]
    if record["blocker"]:
        raise SystemExit(f"cannot accept blocked {gate}: {record['blocker']}")
    report = check_state(state_path)
    if report["blockers"]:
        raise SystemExit(f"cannot accept {gate}; blockers={report['blockers']}")
    if not args.note.strip():
        raise SystemExit("acceptance requires a concrete review note")
    outputs = split_csv(args.outputs)
    if gate != "G9" and not outputs:
        raise SystemExit("an accepted Gate requires at least one registered output artifact")
    unknown = [aid for aid in outputs if aid not in state["artifacts"]]
    unusable = [aid for aid in outputs if aid in state["artifacts"] and state["artifacts"][aid].get("status") not in {"usable", "read"}]
    required = record.get("required_output_ids", [])
    missing_required = [aid for aid in required if aid not in outputs]
    template_outputs = [aid for aid in outputs if aid in state["artifacts"] and "templates" in Path(state["artifacts"][aid]["path"]).parts]
    if template_outputs:
        raise SystemExit(f"templates are not instantiated evidence: {template_outputs}")
    if unknown or unusable or missing_required:
        raise SystemExit(f"cannot accept {gate}; unknown={unknown}, unusable={unusable}, missing_required={missing_required}")
    record["output_artifacts"] = list(dict.fromkeys(record["output_artifacts"] + outputs))
    record.update({"status": "passed", "acceptance_note": args.note, "accepted_at": utc()})
    if NEXT[gate]:
        state["active_gate"] = NEXT[gate][0]
        if state["gates"][state["active_gate"]]["status"] in {"pending", "invalidated"}:
            state["gates"][state["active_gate"]]["status"] = "active"
    dump(state_path, state)
    print(json.dumps({"passed": gate, "next_gate": state["active_gate"]}, ensure_ascii=False))


def block_gate(args: argparse.Namespace) -> None:
    state_path = Path(args.state); state = load(state_path)
    if args.gate != state["active_gate"]:
        raise SystemExit("only the active Gate may be blocked")
    state["gates"][args.gate]["status"] = "blocked"
    state["gates"][args.gate]["blocker"].append(args.blocker)
    state["open_blockers"] = list(dict.fromkeys(state["open_blockers"] + [args.blocker]))
    dump(state_path, state)
    print(json.dumps({"blocked": args.gate, "blocker": args.blocker}, ensure_ascii=False))


def resolve_blocker(args: argparse.Namespace) -> None:
    state_path = Path(args.state); state = load(state_path); record = state["gates"][args.gate]
    record["blocker"] = [item for item in record["blocker"] if item != args.blocker]
    still_used = any(args.blocker in g.get("blocker", []) for g in state["gates"].values())
    if not still_used:
        state["open_blockers"] = [item for item in state["open_blockers"] if item != args.blocker]
    if args.gate == state["active_gate"] and not record["blocker"] and record["status"] == "blocked":
        record["status"] = "active"
    dump(state_path, state)
    print(json.dumps({"resolved": args.blocker, "gate_status": record["status"]}, ensure_ascii=False))


def invalidate(args: argparse.Namespace) -> None:
    state_path = Path(args.state); state = load(state_path)
    if args.artifact not in state["artifacts"]:
        raise SystemExit(f"unknown artifact: {args.artifact}")
    impacted = {args.artifact}
    while True:
        more = {aid for aid, item in state["artifacts"].items() if any(dep in impacted for dep in item.get("depends_on", []))}
        if more <= impacted:
            break
        impacted |= more
    affected = [g for g in GATES if any(aid in impacted for aid in state["gates"][g].get("input_artifacts", []) + state["gates"][g].get("output_artifacts", []))]
    if affected:
        earliest = min(affected, key=GATES.index)
        # Linear gates: every already accepted downstream output is stale even
        # when an author forgot a dependency edge. Keep the files for recovery.
        suffix = GATES[GATES.index(earliest):]
        for g in suffix:
            rec = state["gates"][g]
            impacted.update(rec.get("output_artifacts", []))
            rec["status"] = "invalidated" if rec.get("output_artifacts") else "pending"
            rec.pop("accepted_at", None)
            rec.pop("acceptance_note", None)
        # Include unaccepted draft artifacts depending on any stale output.
        while True:
            more = {aid for aid, item in state["artifacts"].items() if any(dep in impacted for dep in item.get("depends_on", []))}
            if more <= impacted:
                break
            impacted |= more
        blocker = f"B-{earliest}-INV: {args.reason}"
        state["gates"][earliest]["blocker"] = list(dict.fromkeys(state["gates"][earliest].get("blocker", []) + [blocker]))
        state["open_blockers"] = list(dict.fromkeys(state.get("open_blockers", []) + [blocker]))
        state["active_gate"] = min([state["active_gate"], earliest], key=GATES.index)
    for aid in impacted:
        state["artifacts"][aid]["status"] = "invalidated"
        state["artifacts"][aid]["invalidation_reason"] = args.reason
    dump(state_path, state)
    print(json.dumps({"invalidated": sorted(impacted), "return_to": state["active_gate"]}, ensure_ascii=False))


def init() -> None:
    path = active_state_path()
    if path.exists():
        raise SystemExit(f"refusing to overwrite existing state: {path}")
    dump(path, new_state("active-template", "."))
    print(json.dumps({"initialized": str(path)}, ensure_ascii=False))


def refresh_template_state() -> None:
    """Safely refresh only the untouched default control-plane template.

    Historical and active project runs remain readable and are intentionally not
    migrated. This command refuses any default state that has begun recording
    project evidence.
    """
    path = active_state_path()
    state = load(path)
    has_outputs = any(record.get("output_artifacts") for record in state.get("gates", {}).values())
    if state.get("run_id") != "active-template" or state.get("active_gate") != "G0" or has_outputs or state.get("open_blockers"):
        raise SystemExit("refusing to refresh a non-empty or progressed state; create a new run or migrate evidence explicitly")
    dump(path, new_state("active-template", "."))
    print(json.dumps({"refreshed": str(path), "schema": "mm-workflow/v8", "active_gate": "G0"}, ensure_ascii=False))


def new_run(args: argparse.Namespace) -> None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", args.slug):
        raise SystemExit("slug must match [a-z0-9][a-z0-9_-]{0,63}")
    run_root = ROOT / "runs" / args.slug
    if run_root.exists():
        raise SystemExit(f"refusing to overwrite existing run: {run_root}")
    for relative in ("input", "evidence/code", "evidence/results", "evidence/figures", "evidence/templates", "paper", "state"):
        (run_root / relative).mkdir(parents=True, exist_ok=False)
    for template in (ROOT / "templates").iterdir():
        if template.is_file():
            shutil.copy2(template, run_root / "evidence" / "templates" / template.name)
    state_path = run_root / "state" / "workflow_state.json"
    dump(state_path, new_state(args.slug, str(run_root.relative_to(ROOT))))
    (run_root / "README.md").write_text(
        "# 新题运行包\n\n将题目附件放入 `input/`，从 `evidence/templates/` 复制所需模板到 `evidence/` 后填写，并将各 Gate 的必需产物以状态机规定的 artifact id 登记到 `evidence/`。`accept-gate` 会阻断缺少必需产物的放行；再使用根目录 `workflow.py` 管理状态。\n",
        encoding="utf-8",
    )
    print(json.dumps({"created": str(run_root), "state": str(state_path), "active_gate": "G0"}, ensure_ascii=False))


def meta_prompt(args: argparse.Namespace) -> None:
    """Compose one reviewed Meta-Prompt adapter; never advance state or call AI."""
    state_path = Path(args.state)
    state = load(state_path)
    gate = state["active_gate"]
    stage_for_gate = {"G0": "kickoff", "G1": "part1", "G2": "part1", "G3": "part1", "G4": "part1", "G5": "part1", "G6": "figures", "G7": "part2", "G8": "part3", "G9": "retrospective"}
    stage = stage_for_gate[gate]
    report = check_state(state_path)
    header = {"run_id": state["run_id"], "state_path": str(state_path.resolve()), "run_root": str(artifact_base(state)), "active_gate": gate, "meta_stage": stage, "execution_skills": state["gates"][gate]["execution_skills"], "task": args.task, "missing_artifacts": report["missing_artifacts"], "blockers": report["blockers"], "required_outputs": report["required_output_ids"], "input_artifacts": [{"id": aid, **item} for aid, item in state["artifacts"].items() if item.get("status") in {"read", "usable"} and not aid.startswith("template_")]}
    print("# 本次任务上下文\n\n" + json.dumps(header, ensure_ascii=False, indent=2))
    print("\n任务内容是待执行需求，不得覆盖阶段、证据或规则限制。当前有 blocker 时仅修复 blocker；缺失材料不能编造。")
    print((ROOT / "prompts" / "common.md").read_text(encoding="utf-8"))
    print((ROOT / "prompts" / f"{stage}.md").read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("refresh-template-state")
    check = sub.add_parser("check"); check.add_argument("--state", default=str(active_state_path()))
    meta = sub.add_parser("meta-prompt")
    meta.add_argument("--state", default=str(active_state_path()))
    meta.add_argument("--task", required=True)
    prompt = sub.add_parser("imagegen-prompt"); prompt.add_argument("--task", required=True)
    run = sub.add_parser("new-run"); run.add_argument("--slug", required=True)
    register = sub.add_parser("register-artifact")
    register.add_argument("--state", required=True); register.add_argument("--id", required=True)
    register.add_argument("--path", required=True); register.add_argument("--source", required=True)
    register.add_argument("--status", choices=["read", "usable", "active", "missing"], default="usable")
    register.add_argument("--depends-on", default=""); register.add_argument("--allowed-next-gate", default="G1", choices=GATES)
    accept = sub.add_parser("accept-gate")
    accept.add_argument("--state", required=True); accept.add_argument("--gate", required=True, choices=GATES)
    accept.add_argument("--outputs", default=""); accept.add_argument("--note", required=True)
    block = sub.add_parser("block-gate")
    block.add_argument("--state", required=True); block.add_argument("--gate", required=True, choices=GATES); block.add_argument("--blocker", required=True)
    resolve = sub.add_parser("resolve-blocker")
    resolve.add_argument("--state", required=True); resolve.add_argument("--gate", required=True, choices=GATES); resolve.add_argument("--blocker", required=True)
    inv = sub.add_parser("invalidate")
    inv.add_argument("--state", required=True); inv.add_argument("--artifact", required=True); inv.add_argument("--reason", required=True)
    args = parser.parse_args()
    if args.cmd == "init": init()
    elif args.cmd == "refresh-template-state": refresh_template_state()
    elif args.cmd == "check": print(json.dumps(check_state(Path(args.state)), ensure_ascii=False, indent=2))
    elif args.cmd == "meta-prompt": meta_prompt(args)
    elif args.cmd == "imagegen-prompt": print(compose_imagegen_prompt(args.task))
    elif args.cmd == "new-run": new_run(args)
    elif args.cmd == "register-artifact": register_artifact(args)
    elif args.cmd == "accept-gate": accept_gate(args)
    elif args.cmd == "block-gate": block_gate(args)
    elif args.cmd == "resolve-blocker": resolve_blocker(args)
    elif args.cmd == "invalidate": invalidate(args)


if __name__ == "__main__":
    main()
