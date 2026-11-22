"""
Reproducible Human-Validated Evaluation Pipeline (Q1-Q8)
========================================================
Reads the team's human relevance judgements directly from:
    doc/evaluation/Relevance Judgement Q1-Q8.xlsx

Evaluates the live production v5 From-Scratch IR engine (`SearchService` +
`backend/artifacts/index.joblib`) and exports all report-ready CSV tables into:
    doc/evaluation/results/

Run from repository root:
    .\\backend\\.venv\\Scripts\\python.exe backend\\scripts\\run_human_evaluation.py
"""
from __future__ import annotations

import csv
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings
from app.services.search import SearchService

XLSX_PATH = ROOT_DIR / "doc" / "evaluation" / "Relevance Judgement Q1-Q8.xlsx"
OUT_DIR = ROOT_DIR / "doc" / "evaluation" / "results"

# Explicit adjudicator resolution for the single cross-sheet validator conflict:
# In Relevance Judgement Q1-Q8.xlsx, Q1:D002 was labeled 'tidak relevan' in Q1 (BASE)
# and 'relevan' in Q1 (EA). Confirmed by validator (Ale): final ground truth = relevan (1).
VALIDATOR_OVERRIDES: Dict[Tuple[str, str], Tuple[int, str]] = {
    ("Q1", "D002"): (1, "Resolved cross-sheet conflict (BASE=0, EA=1) -> relevan per validator"),
}

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def _col_to_idx(col_str: str) -> int:
    idx = 0
    for ch in col_str:
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx - 1


def _parse_cell_ref(ref: str) -> Tuple[int, int]:
    m = re.match(r"([A-Z]+)([0-9]+)", ref)
    assert m is not None, f"Invalid cell reference: {ref}"
    return int(m.group(2)), _col_to_idx(m.group(1))


def read_xlsx(path: Path) -> Dict[str, List[Tuple[int, List[Optional[str]]]]]:
    """Read all worksheets from an .xlsx archive using Python stdlib only."""
    sheets: Dict[str, List[Tuple[int, List[Optional[str]]]]] = {}
    with zipfile.ZipFile(path, "r") as z:
        shared: List[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("main:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['main']}}}t")))

        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid_to_target = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("pkg:Relationship", NS)
        }

        for sh in wb.findall("main:sheets/main:sheet", NS):
            name = sh.attrib["name"]
            rid = sh.attrib[f"{{{NS['r']}}}id"]
            target = rid_to_target[rid]
            if not target.startswith("xl/"):
                target = "xl/" + target.lstrip("/")
            ws = ET.fromstring(z.read(target))

            grid: Dict[int, Dict[int, str]] = defaultdict(dict)
            max_r, max_c = 0, 0
            for c in ws.findall(".//main:sheetData/main:row/main:c", NS):
                ref = c.attrib.get("r")
                if not ref:
                    continue
                r_idx, c_idx = _parse_cell_ref(ref)
                t = c.attrib.get("t")
                val: Optional[str] = None
                if t == "s":
                    v = c.find("main:v", NS)
                    if v is not None and v.text is not None:
                        val = shared[int(v.text)]
                elif t == "inlineStr":
                    is_el = c.find("main:is", NS)
                    if is_el is not None:
                        val = "".join(x.text or "" for x in is_el.iter(f"{{{NS['main']}}}t"))
                else:
                    v = c.find("main:v", NS)
                    if v is not None and v.text is not None:
                        val = v.text
                if val is not None:
                    grid[r_idx][c_idx] = val
                    max_r = max(max_r, r_idx)
                    max_c = max(max_c, c_idx)

            for mc in ws.findall(".//main:mergeCells/main:mergeCell", NS):
                rng = mc.attrib["ref"]
                if ":" in rng:
                    a, b = rng.split(":")
                    r1, c1 = _parse_cell_ref(a)
                    r2, c2 = _parse_cell_ref(b)
                    tl = grid.get(r1, {}).get(c1)
                    if tl is not None:
                        for rr in range(r1, r2 + 1):
                            for cc in range(c1, c2 + 1):
                                if cc not in grid[rr]:
                                    grid[rr][cc] = tl

            rows: List[Tuple[int, List[Optional[str]]]] = []
            for r in range(1, max_r + 1):
                row = [grid[r].get(c) for c in range(max_c + 1)]
                if any(x is not None and str(x).strip() != "" for x in row):
                    rows.append((r, row))
            sheets[name] = rows
    return sheets


def parse_binary_label(raw: Optional[str]) -> int:
    s = (raw or "").strip().lower()
    if s in ("relevan", "1", "yes", "ya"):
        return 1
    if s in ("tidak relevan", "0", "no", "tidak"):
        return 0
    raise ValueError(f"Unrecognized relevance label: {raw!r}")


def interpret_kappa(kappa: float) -> str:
    if kappa < 0.0:
        return "Poor"
    if kappa <= 0.20:
        return "Slight"
    if kappa <= 0.40:
        return "Fair"
    if kappa <= 0.60:
        return "Moderate"
    if kappa <= 0.80:
        return "Substantial"
    return "Almost Perfect"


def compute_cohens_kappa(pairs: Sequence[Tuple[int, int]]) -> Dict[str, Any]:
    n = len(pairs)
    if n == 0:
        raise ValueError("Cannot compute Cohen's Kappa on empty pairs.")
    a = sum(1 for x, y in pairs if x == 1 and y == 1)
    b = sum(1 for x, y in pairs if x == 1 and y == 0)
    c = sum(1 for x, y in pairs if x == 0 and y == 1)
    d = sum(1 for x, y in pairs if x == 0 and y == 0)
    po = (a + d) / n
    p1_yes = (a + b) / n
    p2_yes = (a + c) / n
    p1_no = (c + d) / n
    p2_no = (b + d) / n
    pe = p1_yes * p2_yes + p1_no * p2_no
    kappa = (po - pe) / (1.0 - pe) if abs(1.0 - pe) > 1e-12 else 1.0
    return {
        "n_items": n,
        "both_relevan_11": a,
        "j1_only_10": b,
        "j2_only_01": c,
        "both_tidak_00": d,
        "observed_agreement_po": round(po, 4),
        "chance_agreement_pe": round(pe, 4),
        "cohens_kappa": round(kappa, 4),
        "interpretation": interpret_kappa(kappa),
    }


def evaluate_ranking(ranked_doc_ids: Sequence[str], rel_set: Set[str]) -> Dict[str, float]:
    p5 = sum(1 for d in ranked_doc_ids[:5] if d in rel_set) / 5.0
    p10 = sum(1 for d in ranked_doc_ids[:10] if d in rel_set) / 10.0
    r5 = sum(1 for d in ranked_doc_ids[:5] if d in rel_set) / len(rel_set) if rel_set else 0.0
    r10 = sum(1 for d in ranked_doc_ids[:10] if d in rel_set) / len(rel_set) if rel_set else 0.0

    hits = 0
    sum_prec = 0.0
    rr = 0.0
    for idx, doc_id in enumerate(ranked_doc_ids, start=1):
        if doc_id in rel_set:
            hits += 1
            if rr == 0.0:
                rr = 1.0 / idx
            sum_prec += hits / idx
    ap = sum_prec / len(rel_set) if rel_set else 0.0

    return {
        "P@5": p5,
        "P@10": p10,
        "R@5": r5,
        "R@10": r10,
        "AP": ap,
        "RR": rr,
    }


def write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not XLSX_PATH.exists():
        raise FileNotFoundError(f"Input spreadsheet not found: {XLSX_PATH}")

    sheets = read_xlsx(XLSX_PATH)
    queries: List[Dict[str, str]] = []
    for _, row in sheets["Query (8)"][1:]:
        qid = (row[0] or "").strip()
        qtext = (row[1] or "").strip()
        qtype = (row[2] or "").strip()
        if qid:
            queries.append({"query_id": qid, "query_text": qtext, "query_group": qtype})

    # Parse all 16 judgement sheets (Q1..Q8 BASE and EA)
    raw_rows: List[Dict[str, Any]] = []
    by_q_doc: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for q in queries:
        qid = q["query_id"]
        for sys_tag in ("BASE", "EA"):
            sname = f"{qid} ({sys_tag})"
            for r_idx, row in sheets[sname][1:]:
                doc_id = (row[3] or "").strip() if len(row) > 3 else ""
                if not doc_id:
                    continue
                rec = {
                    "sheet": sname,
                    "sys": sys_tag,
                    "row": r_idx,
                    "query_id": qid,
                    "doc_id": doc_id,
                    "title": (row[4] or "").strip() if len(row) > 4 else "",
                    "j1": parse_binary_label(row[6] if len(row) > 6 else None),
                    "j2": parse_binary_label(row[7] if len(row) > 7 else None),
                    "val": parse_binary_label(row[8] if len(row) > 8 else None),
                }
                raw_rows.append(rec)
                by_q_doc[(qid, doc_id)].append(rec)

    # Consolidate deduplicated union pool (138 unique (query_id, doc_id) pairs)
    consolidated_rows: List[Dict[str, Any]] = []
    qrels: Dict[str, Set[str]] = {q["query_id"]: set() for q in queries}
    pool_sizes: Dict[str, int] = {q["query_id"]: 0 for q in queries}

    for q in queries:
        qid = q["query_id"]
        doc_ids_for_q = sorted(d for (q_, d) in by_q_doc.keys() if q_ == qid)
        pool_sizes[qid] = len(doc_ids_for_q)
        for doc_id in doc_ids_for_q:
            recs = by_q_doc[(qid, doc_id)]
            rec_base = next((r for r in recs if r["sys"] == "BASE"), None)
            rec_ea = next((r for r in recs if r["sys"] == "EA"), None)
            primary = rec_base or rec_ea
            assert primary is not None

            note = ""
            if (qid, doc_id) in VALIDATOR_OVERRIDES:
                final_val, note = VALIDATOR_OVERRIDES[(qid, doc_id)]
            else:
                vals = {r["val"] for r in recs}
                if len(vals) > 1:
                    raise ValueError(f"Unresolved validator conflict for {qid}:{doc_id}: {vals}")
                final_val = primary["val"]
                if rec_base and rec_ea and rec_base["j1"] != rec_ea["j1"]:
                    note = f"j1 differed across tabs (BASE={rec_base['j1']}, EA={rec_ea['j1']}); validator consistent={final_val}"

            if final_val == 1:
                qrels[qid].add(doc_id)

            consolidated_rows.append({
                "query_id": qid,
                "query_group": q["query_group"],
                "doc_id": doc_id,
                "title": primary["title"],
                "in_base_sheet": int(rec_base is not None),
                "in_ea_sheet": int(rec_ea is not None),
                "judge_1_base": rec_base["j1"] if rec_base else "",
                "judge_1_ea": rec_ea["j1"] if rec_ea else "",
                "judge_2_base": rec_base["j2"] if rec_base else "",
                "judge_2_ea": rec_ea["j2"] if rec_ea else "",
                "judge_1_primary": primary["j1"],
                "judge_2_primary": primary["j2"],
                "judges_agreed_primary": int(primary["j1"] == primary["j2"]),
                "validator_final": final_val,
                "resolution_note": note,
            })

    # 1. Cohen's Kappa Report (all 240 rows + 138 unique union pool + per-query)
    kappa_rows: List[Dict[str, Any]] = []
    k_all_raw = compute_cohens_kappa([(r["j1"], r["j2"]) for r in raw_rows])
    kappa_rows.append({"scope": "Overall (All 16 Sheets)", "query_id": "ALL", "query_group": "All (Q1-Q8)", **k_all_raw})

    k_all_dedup_base = compute_cohens_kappa([
        (r["judge_1_primary"], r["judge_2_primary"]) for r in consolidated_rows
    ])
    kappa_rows.append({"scope": "Overall (Unique Union Pool, BASE-first)", "query_id": "ALL", "query_group": "All (Q1-Q8)", **k_all_dedup_base})

    ea_first_pairs = []
    for r in consolidated_rows:
        j1 = r["judge_1_ea"] if r["judge_1_ea"] != "" else r["judge_1_base"]
        j2 = r["judge_2_ea"] if r["judge_2_ea"] != "" else r["judge_2_base"]
        ea_first_pairs.append((int(j1), int(j2)))
    k_all_dedup_ea = compute_cohens_kappa(ea_first_pairs)
    kappa_rows.append({"scope": "Overall (Unique Union Pool, EA-first)", "query_id": "ALL", "query_group": "All (Q1-Q8)", **k_all_dedup_ea})

    for q in queries:
        qid = q["query_id"]
        sub_dedup = [
            (r["judge_1_primary"], r["judge_2_primary"])
            for r in consolidated_rows
            if r["query_id"] == qid
        ]
        kr = compute_cohens_kappa(sub_dedup)
        kappa_rows.append({
            "scope": "Per-Query (Unique Union Pool)",
            "query_id": qid,
            "query_group": q["query_group"],
            **kr,
        })

    # Load production v5 SearchService
    svc = SearchService(get_settings())
    if not svc.try_load():
        raise RuntimeError("Failed to load backend/artifacts/index.joblib")

    # 2. Evaluate Baseline vs Entity-Aware (alpha=0.8, beta=0.2)
    qrels_export: List[Dict[str, Any]] = []
    per_query_rows: List[Dict[str, Any]] = []
    comparison_rows: List[Dict[str, Any]] = []
    base_metrics_list: List[Dict[str, float]] = []
    prop_metrics_list: List[Dict[str, float]] = []

    for q in queries:
        qid = q["query_id"]
        grp = q["query_group"]
        qtext = q["query_text"]
        rel_set = qrels[qid]

        base_res = svc.search(qtext, mode="baseline", top_k=60)
        prop_res = svc.search(qtext, mode="entity", top_k=60, alpha=0.8, beta=0.2)
        base_ranked = svc.rank(qtext, "baseline", 0.8, 0.2)
        prop_ranked = svc.rank(qtext, "entity", 0.8, 0.2)

        bm = evaluate_ranking(base_ranked, rel_set)
        pm = evaluate_ranking(prop_ranked, rel_set)
        base_metrics_list.append(bm)
        prop_metrics_list.append(pm)

        ent_str = "; ".join(
            f"{e['entity_id']}:{e['name']} ({e['category']})"
            for e in prop_res["recognized_entities"]
        ) or "NONE (Fallback)"

        qrels_export.append({
            "query_id": qid,
            "query_group": grp,
            "query_text": qtext,
            "detected_entities": ent_str,
            "pool_size": pool_sizes[qid],
            "num_relevant": len(rel_set),
            "relevant_doc_ids": ", ".join(sorted(rel_set)),
        })

        per_query_rows.append({
            "query_id": qid,
            "query_group": grp,
            "query_text": qtext,
            "detected_entities": ent_str,
            "num_relevant": len(rel_set),
            "baseline_P@5": round(bm["P@5"], 4),
            "proposed_P@5": round(pm["P@5"], 4),
            "delta_P@5": round(pm["P@5"] - bm["P@5"], 4),
            "baseline_P@10": round(bm["P@10"], 4),
            "proposed_P@10": round(pm["P@10"], 4),
            "delta_P@10": round(pm["P@10"] - bm["P@10"], 4),
            "baseline_R@5": round(bm["R@5"], 4),
            "proposed_R@5": round(pm["R@5"], 4),
            "delta_R@5": round(pm["R@5"] - bm["R@5"], 4),
            "baseline_R@10": round(bm["R@10"], 4),
            "proposed_R@10": round(pm["R@10"], 4),
            "delta_R@10": round(pm["R@10"] - bm["R@10"], 4),
            "baseline_AP": round(bm["AP"], 4),
            "proposed_AP": round(pm["AP"], 4),
            "delta_AP": round(pm["AP"] - bm["AP"], 4),
            "baseline_RR": round(bm["RR"], 4),
            "proposed_RR": round(pm["RR"], 4),
            "delta_RR": round(pm["RR"] - bm["RR"], 4),
        })

        # Top-15 side-by-side comparison
        for rank_i in range(15):
            br = base_res["results"][rank_i] if rank_i < len(base_res["results"]) else None
            pr = prop_res["results"][rank_i] if rank_i < len(prop_res["results"]) else None
            comparison_rows.append({
                "query_id": qid,
                "query_group": grp,
                "query_text": qtext,
                "rank": rank_i + 1,
                "baseline_doc_id": br["doc_id"] if br else "",
                "baseline_title": br["title"] if br else "",
                "baseline_S_text": round(br["text_score"], 4) if br else "",
                "baseline_is_relevant": int(br["doc_id"] in rel_set) if br else 0,
                "proposed_doc_id": pr["doc_id"] if pr else "",
                "proposed_title": pr["title"] if pr else "",
                "proposed_S_text": round(pr["text_score"], 4) if pr else "",
                "proposed_S_entity": round(pr["entity_score"], 4) if pr else "",
                "proposed_S_final": round(pr["score"], 4) if pr else "",
                "proposed_is_relevant": int(pr["doc_id"] in rel_set) if pr else 0,
            })

    # 3. Grouped Summary Metrics
    def build_summary(label: str, indices: Sequence[int]) -> List[Dict[str, Any]]:
        out = []
        for sys_label, src in [
            ("Baseline (TF-IDF + Cosine Similarity)", base_metrics_list),
            ("Proposed (TF-IDF + Entity-Aware, a=0.8, b=0.2)", prop_metrics_list),
        ]:
            sub = [src[i] for i in indices]
            n = len(sub)
            out.append({
                "query_subset": label,
                "system": sys_label,
                "num_queries": n,
                "Precision@5": round(sum(x["P@5"] for x in sub) / n, 4),
                "Precision@10": round(sum(x["P@10"] for x in sub) / n, 4),
                "Recall@5": round(sum(x["R@5"] for x in sub) / n, 4),
                "Recall@10": round(sum(x["R@10"] for x in sub) / n, 4),
                "MAP": round(sum(x["AP"] for x in sub) / n, 4),
                "MRR": round(sum(x["RR"] for x in sub) / n, 4),
            })
        return out

    summary_rows: List[Dict[str, Any]] = []
    summary_rows.extend(build_summary("All Queries (Q1-Q8)", list(range(8))))
    summary_rows.extend(build_summary("Entity-Based Queries (Q1-Q4)", [0, 1, 2, 3]))
    summary_rows.extend(build_summary("Subgroup: Entity Pendek (Q1-Q2)", [0, 1]))
    summary_rows.extend(build_summary("Subgroup: Entity Panjang (Q3-Q4)", [2, 3]))
    summary_rows.extend(build_summary("Non-Entity Queries / Fallback (Q5-Q8)", [4, 5, 6, 7]))
    summary_rows.extend(build_summary("Subgroup: Non-Entity Pendek (Q5-Q6)", [4, 5]))
    summary_rows.extend(build_summary("Subgroup: Non-Entity Panjang (Q7-Q8)", [6, 7]))

    # 4. Alpha-Beta Sensitivity Analysis
    sensitivity_rows: List[Dict[str, Any]] = []
    for a_val in [1.0, 0.9, 0.85, 0.8, 0.75, 0.7, 0.6, 0.5]:
        b_val = round(1.0 - a_val, 2)
        m_all: List[Dict[str, float]] = []
        m_ent: List[Dict[str, float]] = []
        for idx, q in enumerate(queries):
            mode = "baseline" if b_val == 0.0 else "entity"
            ranked = svc.rank(q["query_text"], mode, a_val, b_val)
            ev = evaluate_ranking(ranked, qrels[q["query_id"]])
            m_all.append(ev)
            if idx < 4:
                m_ent.append(ev)
        sensitivity_rows.append({
            "alpha": a_val,
            "beta": b_val,
            "overall_P@5": round(sum(x["P@5"] for x in m_all) / len(m_all), 4),
            "overall_P@10": round(sum(x["P@10"] for x in m_all) / len(m_all), 4),
            "overall_R@10": round(sum(x["R@10"] for x in m_all) / len(m_all), 4),
            "overall_MAP": round(sum(x["AP"] for x in m_all) / len(m_all), 4),
            "overall_MRR": round(sum(x["RR"] for x in m_all) / len(m_all), 4),
            "entity_P@5": round(sum(x["P@5"] for x in m_ent) / len(m_ent), 4),
            "entity_P@10": round(sum(x["P@10"] for x in m_ent) / len(m_ent), 4),
            "entity_R@10": round(sum(x["R@10"] for x in m_ent) / len(m_ent), 4),
            "entity_MAP": round(sum(x["AP"] for x in m_ent) / len(m_ent), 4),
            "entity_MRR": round(sum(x["RR"] for x in m_ent) / len(m_ent), 4),
        })

    # Write all 7 CSV outputs
    write_csv(OUT_DIR / "cohens_kappa_report.csv", list(kappa_rows[0].keys()), kappa_rows)
    write_csv(OUT_DIR / "human_judgements_consolidated.csv", list(consolidated_rows[0].keys()), consolidated_rows)
    write_csv(OUT_DIR / "evaluation_queries_qrels.csv", list(qrels_export[0].keys()), qrels_export)
    write_csv(OUT_DIR / "evaluation_metrics_per_query.csv", list(per_query_rows[0].keys()), per_query_rows)
    write_csv(OUT_DIR / "evaluation_metrics_summary.csv", list(summary_rows[0].keys()), summary_rows)
    write_csv(OUT_DIR / "ranking_comparison_baseline_vs_entity_aware.csv", list(comparison_rows[0].keys()), comparison_rows)
    write_csv(OUT_DIR / "alpha_beta_sensitivity.csv", list(sensitivity_rows[0].keys()), sensitivity_rows)

    print(f"Exported 7 evaluation CSVs to: {OUT_DIR}")
    print("\n--- COHEN'S KAPPA SUMMARY ---")
    for r in kappa_rows[:3]:
        print(f"  {r['scope']:40s} | n={r['n_items']:3d} | po={r['observed_agreement_po']:.4f} | pe={r['chance_agreement_pe']:.4f} | kappa={r['cohens_kappa']:.4f} ({r['interpretation']})")

    print("\n--- EVALUATION SUMMARY (FINAL, Q1:D002=relevan, Q5=20-doc pool) ---")
    for r in summary_rows:
        print(f"  {r['query_subset']:40s} | {r['system'][:8]:8s} | P@5={r['Precision@5']:.4f} P@10={r['Precision@10']:.4f} R@5={r['Recall@5']:.4f} R@10={r['Recall@10']:.4f} MAP={r['MAP']:.4f} MRR={r['MRR']:.4f}")

    print("\n--- PER-QUERY METRICS (Q1-Q8) ---")
    for r in per_query_rows:
        print(f"  {r['query_id']} [{r['query_group']:18s}] rel={r['num_relevant']:2d} | P@5: {r['baseline_P@5']:.4f}->{r['proposed_P@5']:.4f} | P@10: {r['baseline_P@10']:.4f}->{r['proposed_P@10']:.4f} | R@10: {r['baseline_R@10']:.4f}->{r['proposed_R@10']:.4f} | AP: {r['baseline_AP']:.4f}->{r['proposed_AP']:.4f} ({r['delta_AP']:+.4f}) | RR: {r['baseline_RR']:.4f}->{r['proposed_RR']:.4f}")


if __name__ == "__main__":
    main()

