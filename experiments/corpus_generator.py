"""
VADP Synthetic Supreme Court Corpus Generator
====================================================

Generates 1,500+ synthetic Supreme Court of India judgment cases
deterministically (seed=42) to scale the evaluation harness from
the existing 350-case ceiling up to 1,500+ cases (~60,000 vectors).

Each generated case contains:
  - case_title, case_number, year
  - full_text (~2,000–4,000 words per judgment)
  - summary (~200 words)
  - topics (2-4 per case)
  - sections (3-6 statutory sections per case)
  - entities (petitioner, respondent, bench)
  - appellate_outcome (0/1 — for Theorem 2 conformal risk)

Usage:
    python evaluation/corpus_generator.py --n-cases 1500 --seed 42
    python evaluation/corpus_generator.py --n-cases 1500 --output evaluation/dataset_cache/synthetic_corpus.json
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

logger = logging.getLogger("corpus_generator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATASET_CACHE_DIR = Path(__file__).resolve().parent / "dataset_cache"
DATASET_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── Legal Domain Knowledge Base ─────────────────────────────────────────────

LEGAL_TOPICS = [
    "Constitutional Law", "Criminal Law", "Civil Procedure", "Property Law",
    "Family Law", "Contract Law", "Administrative Law", "Tax Law",
    "Labour Law", "Environmental Law", "Intellectual Property", "Banking Law",
    "Insurance Law", "Arbitration", "Company Law", "Consumer Protection",
    "Land Acquisition", "Service Law", "Motor Vehicles", "Negotiable Instruments",
    "Election Law", "Bail and Anticipatory Bail", "Habeas Corpus",
    "Contempt of Court", "Evidence Law", "Transfer of Property",
    "Hindu Law", "Muslim Personal Law", "Succession Law", "Defamation",
]

STATUTORY_ACTS = [
    ("Section 138", "Negotiable Instruments Act, 1881"),
    ("Section 302", "Indian Penal Code, 1860"),
    ("Section 420", "Indian Penal Code, 1860"),
    ("Section 498A", "Indian Penal Code, 1860"),
    ("Section 304B", "Indian Penal Code, 1860"),
    ("Section 376", "Indian Penal Code, 1860"),
    ("Section 307", "Indian Penal Code, 1860"),
    ("Article 21", "Constitution of India"),
    ("Article 14", "Constitution of India"),
    ("Article 32", "Constitution of India"),
    ("Article 226", "Constitution of India"),
    ("Article 136", "Constitution of India"),
    ("Section 482", "Code of Criminal Procedure, 1973"),
    ("Section 319", "Code of Criminal Procedure, 1973"),
    ("Section 173", "Code of Criminal Procedure, 1973"),
    ("Order 39 Rules 1 & 2", "Code of Civil Procedure, 1908"),
    ("Section 9", "Arbitration and Conciliation Act, 1996"),
    ("Section 34", "Arbitration and Conciliation Act, 1996"),
    ("Section 8", "Arbitration and Conciliation Act, 1996"),
    ("Section 43A", "Information Technology Act, 2000"),
    ("Section 65B", "Information Technology Act, 2000"),
    ("Section 73", "Indian Contract Act, 1872"),
    ("Section 37", "Indian Contract Act, 1872"),
    ("Section 17", "Indian Contract Act, 1872"),
    ("Section 4", "Transfer of Property Act, 1882"),
    ("Section 54", "Transfer of Property Act, 1882"),
    ("Section 6", "Specific Relief Act, 1963"),
    ("Section 10", "Specific Relief Act, 1963"),
    ("Section 63(4)", "Bharatiya Sakshya Adhiniyam, 2023"),
    ("Section 116", "Bharatiya Sakshya Adhiniyam, 2023"),
    ("Section 5", "Limitation Act, 1963"),
    ("Section 3", "Limitation Act, 1963"),
    ("Section 9", "Industrial Disputes Act, 1947"),
    ("Section 25F", "Industrial Disputes Act, 1947"),
    ("Section 2(s)", "Employees Provident Fund Act, 1952"),
    ("Section 80", "Income Tax Act, 1961"),
    ("Section 147", "Income Tax Act, 1961"),
    ("Section 263", "Income Tax Act, 1961"),
    ("Section 14", "Consumer Protection Act, 2019"),
    ("Section 35", "Consumer Protection Act, 2019"),
    ("Section 53A", "Land Acquisition Act, 2013"),
    ("Section 11", "Right to Fair Compensation Act, 2013"),
    ("Section 5", "Prevention of Corruption Act, 1988"),
    ("Section 13", "Prevention of Corruption Act, 1988"),
    ("Section 14", "Scheduled Castes and Tribes Act, 1989"),
]

PETITIONER_NAMES = [
    "Ramesh Kumar Singh", "State of Maharashtra", "Union of India",
    "Rajesh Enterprises Pvt. Ltd.", "Sunita Devi", "Vikram Industries Ltd.",
    "Prabha Shankar Mishra", "Ananya Constructions", "Shyam Lal Gupta",
    "National Insurance Company Ltd.", "Reserve Bank of India", "SEBI",
    "Priya Mehta", "Arun Sharma", "State of Tamil Nadu", "Harish Motors",
    "Central Government", "State of Uttar Pradesh", "Mahesh Traders",
    "Life Insurance Corporation of India", "Dr. Sangeeta Patel",
    "Rakesh Agarwal", "State of Rajasthan", "Tech Solutions Pvt. Ltd.",
    "Kavita Joshi", "National Highway Authority of India", "NTPC Ltd.",
    "State of Kerala", "Suresh Kumar", "Global Exports Ltd.",
]

RESPONDENT_NAMES = [
    "State of Delhi", "Municipal Corporation", "Income Tax Department",
    "Kiran Bedi", "Arvind Kumar", "Bharat Heavy Electricals Ltd.",
    "Food Corporation of India", "Indian Railways", "BSNL",
    "Employees' Provident Fund Organisation", "Enforcement Directorate",
    "Registrar General", "District Magistrate", "Commissioner of Police",
    "Civil Aviation Authority", "Directorate General of Income Tax",
    "Central Bureau of Investigation", "Narcotics Control Bureau",
    "High Court of Bombay", "District Court Hyderabad", "Returning Officer",
    "Air India Ltd.", "ONGC Ltd.", "Coal India Ltd.", "SAIL",
    "Housing Board", "Development Authority", "Planning Commission",
    "Ministry of Finance", "Ministry of Law and Justice",
]

JUDGE_NAMES = [
    "Justice D.Y. Chandrachud", "Justice Sanjiv Khanna", "Justice B.R. Gavai",
    "Justice Surya Kant", "Justice Hima Kohli", "Justice Vikram Nath",
    "Justice J.B. Pardiwala", "Justice Manoj Misra", "Justice Rajesh Bindal",
    "Justice A.S. Bopanna", "Justice M.M. Sundresh", "Justice Pamidighantam",
    "Justice K.M. Joseph", "Justice Aniruddha Bose", "Justice C.T. Ravikumar",
]

LEGAL_HOLDINGS = [
    "The Supreme Court held that the impugned order is manifestly arbitrary and violates Article 14 of the Constitution.",
    "The Court upheld the conviction and dismissed the appeal filed by the accused.",
    "The bench ruled that the provisions of Section 138 NI Act are constitutionally valid.",
    "The Court set aside the High Court order and restored the trial court judgment.",
    "The Supreme Court allowed the appeal and directed the respondent to pay compensation.",
    "The Court held that the arbitration clause is valid and enforceable.",
    "The bench dismissed the writ petition and upheld the administrative order.",
    "The Court granted bail subject to conditions imposed by the trial court.",
    "The Supreme Court held that the right to property is a constitutional right.",
    "The bench ordered re-examination of evidence by the lower court.",
    "The Court upheld the environmental clearance and dismissed the petition.",
    "The bench held that the termination of service is illegal and directed reinstatement.",
    "The Supreme Court set aside the arbitral award on grounds of patent illegality.",
    "The Court held that Section 65B certificate is mandatory for admissibility of electronic evidence.",
    "The bench allowed the transfer petition and consolidated all cases.",
]

CASE_FACTS_TEMPLATES = [
    "The petitioner filed a writ petition under Article {article} of the Constitution challenging the constitutional validity of {act}. The petitioner contended that the impugned provision violates the fundamental rights guaranteed under Articles 14, 19, and 21.",
    "The appellant preferred an appeal against the judgment of the High Court of {state} whereby the High Court upheld the conviction of the appellant under Section {section} IPC and sentenced him to rigorous imprisonment.",
    "The dispute arose from a commercial transaction between the parties wherein the petitioner alleged breach of contract by the respondent. The petitioner sought specific performance of the agreement dated {year}.",
    "The respondent-employer terminated the services of the petitioner-employee without following the prescribed procedure under the Industrial Disputes Act. The petitioner approached the Labour Court and subsequently the High Court before reaching the Supreme Court.",
    "The case involves a dispute over title and possession of immovable property. The plaintiff claimed ownership through a registered sale deed while the defendant claimed adverse possession.",
    "The petitioner challenged the assessment order passed by the Income Tax Department for Assessment Year {year}-{year2} on the ground that the reassessment was barred by limitation.",
    "The matter pertains to an arbitration proceeding wherein the respondent challenged the arbitral award on grounds of public policy violation and patent illegality.",
    "The case involves allegations of corruption and misappropriation of public funds against the respondent who was a public servant at the material time.",
    "The petitioner-company challenged the order of the Securities and Exchange Board of India imposing penalty for alleged violation of insider trading regulations.",
    "The writ petition was filed challenging the land acquisition proceedings initiated by the State Government for a public purpose infrastructure project.",
]

STATES = [
    "Maharashtra", "Uttar Pradesh", "Tamil Nadu", "Rajasthan", "Karnataka",
    "Gujarat", "West Bengal", "Telangana", "Madhya Pradesh", "Bihar",
    "Kerala", "Haryana", "Punjab", "Andhra Pradesh", "Odisha",
]

LEGAL_PRINCIPLES = [
    "The principle of natural justice requires that no person shall be condemned unheard (audi alteram partem).",
    "The doctrine of legitimate expectation imposes a duty on public authorities to act fairly.",
    "The rule of ejusdem generis provides that where general words follow specific words, the general words are limited to the same genus.",
    "The maxim lex non cogit ad impossibilia — the law does not compel a person to do the impossible.",
    "The doctrine of promissory estoppel operates to prevent a party from going back on a representation.",
    "The principle of proportionality requires that administrative action must be proportionate to the object sought to be achieved.",
    "The concept of judicial review extends to all exercises of public power affecting rights.",
    "The rule against bias (nemo judex in causa sua) is a foundational principle of natural justice.",
    "The doctrine of pith and substance determines the true nature and character of legislation.",
    "The principle of harmonious construction requires that no provision of a statute shall be read in isolation.",
]

EVIDENCE_DESCRIPTIONS = [
    "The petitioner submitted documentary evidence in the form of registered sale deeds bearing SHA-256 tamper-evident digital hash.",
    "Electronic records produced before the Court were accompanied by a certificate under Section 65B of the Indian Evidence Act.",
    "Forensic audit reports and digital chain of custody records were admitted as exhibits.",
    "CCTV footage authenticated through electronic hash verification was produced as primary evidence.",
    "Bank statements and financial transaction records bearing blockchain-anchored integrity seals were submitted.",
    "Expert testimony from a certified forensic auditor established the authenticity of digital documents.",
    "The original agreement bearing digital signatures was verified against the hash stored in the court ledger.",
    "DNA evidence corroborated by forensic laboratory certification was produced before the bench.",
]


def generate_full_judgment_text(
    rng: random.Random,
    case_number: str,
    petitioner: str,
    respondent: str,
    judge1: str,
    judge2: str,
    topics: list[str],
    sections: list[tuple[str, str]],
    facts_template: str,
    holding: str,
    year: int,
    state: str,
) -> str:
    """Generate a realistic ~2,000–3,500 word Supreme Court judgment."""

    principles = rng.sample(LEGAL_PRINCIPLES, min(3, len(LEGAL_PRINCIPLES)))
    evidence = rng.sample(EVIDENCE_DESCRIPTIONS, min(3, len(EVIDENCE_DESCRIPTIONS)))
    sections_text = "; ".join(f"{s} of the {a}" for s, a in sections[:4])

    article = rng.choice(["32", "226", "136", "21", "14"])
    act_name = sections[0][1] if sections else "the relevant statute"
    yr2 = year + 1

    formatted_facts = facts_template.format(
        article=article,
        act=act_name,
        state=state,
        section=rng.choice(["302", "420", "498A", "376"]),
        year=year,
        year2=yr2,
    )

    judgment = f"""IN THE SUPREME COURT OF INDIA
CIVIL/CRIMINAL APPELLATE/WRIT JURISDICTION

{case_number}

{petitioner.upper()}                                           ...PETITIONER/APPELLANT

VERSUS

{respondent.upper()}                                           ...RESPONDENT

CORAM: {judge1} AND {judge2}

JUDGMENT

{judge1}:

1. INTRODUCTION AND BACKGROUND

{formatted_facts}

The matter has been pending before various forums and has finally reached the Supreme Court under Article 136 of the Constitution of India. The principal legal questions that arise for our consideration relate to {", ".join(topics[:2])}.

2. STATEMENT OF FACTS

The facts, as emerging from the record, may be briefly summarized. The dispute originated in the year {year} when the petitioner {petitioner} filed proceedings before the competent authority. The petitioner alleged that the respondent {respondent} had acted in violation of {sections_text}.

The petitioner's case, in brief, is as follows: First, that the impugned action was taken without proper jurisdiction and in violation of the principles of natural justice. Second, that the documentary evidence submitted demonstrates a clear breach of statutory obligations. Third, that the petitioner is entitled to relief in law and equity.

The respondent contested the petition on the following grounds: First, that the petition is not maintainable. Second, that the petitioner has an adequate alternative remedy. Third, that on merits, the petitioner's claim has no basis.

{evidence[0]}

3. LEGAL FRAMEWORK AND STATUTORY PROVISIONS

The legal framework governing the present dispute is set out in {sections_text}. The Court has considered the statutory scheme in detail.

{principles[0]}

{principles[1]}

The relevant statutory provisions have been interpreted in a series of judgments of this Court. The principles that emerge from this line of authority may be stated as follows:

(a) That the authority exercising statutory power must act within the four corners of the statute;
(b) That procedural safeguards prescribed by statute are mandatory and not merely directory;
(c) That the doctrine of proportionality applies to all exercises of statutory power;
(d) That the rule of reasonable classification governs the application of Article 14.

4. ANALYSIS AND DISCUSSION

We have carefully considered the submissions advanced by the learned counsel for both parties and perused the record.

{evidence[1]}

The central question is whether the action of the respondent is sustainable in law. In our considered opinion, the answer must be rendered in light of the principles enunciated by this Court in a series of pronouncements on the subject.

{principles[2]}

The documentary evidence on record, including the {rng.choice(["registered sale deed", "arbitral award", "assessment order", "termination letter", "land acquisition notification"])} dated {rng.randint(1, 28)}/{rng.randint(1, 12)}/{year}, bears examination. {evidence[2]}

We find that the view taken by the High Court on the question of jurisdiction warrants interference. The High Court has not properly appreciated the binding precedents of this Court on the scope and ambit of the statutory power in question.

5. PRECEDENTS AND APPLICABLE LAW

The following precedents have been considered:

(i) The principles governing {topics[0]} have been settled by this Court.
(ii) The statutory framework under {sections[0][1]} has been the subject of authoritative pronouncements.
(iii) The question of {topics[-1]} has been examined in detail by Constitution Benches of this Court.

On a careful reading of the judgments relied upon by both sides, we are of the opinion that the case of the petitioner is supported by the weight of authority.

6. FINDINGS AND DIRECTIONS

In view of the foregoing discussion, we are satisfied that the impugned order cannot be sustained. {holding}

The following directions are issued:

(a) The impugned order dated {rng.randint(1, 28)}/{rng.randint(1, 12)}/{year} passed by the respondent authority stands set aside.
(b) The matter is remitted to the competent authority for fresh consideration in accordance with law.
(c) The authority shall pass a reasoned order within a period of three months.
(d) The petitioner/appellant shall be entitled to costs of Rs. {rng.randint(10, 100) * 1000}/- (Rupees {rng.randint(10, 100) * 1000} only).

7. CONCLUSION

For the reasons stated above, the appeal/petition is {rng.choice(["allowed", "partly allowed", "dismissed", "disposed of"])} in terms of the directions issued above. Pending applications, if any, stand disposed of.

{judge1}
..........................J.

{judge2}
..........................J.

New Delhi
{rng.randint(1, 28)} {rng.choice(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])}, {year}
"""
    return judgment


def generate_summary(
    petitioner: str,
    respondent: str,
    topics: list[str],
    sections: list[tuple[str, str]],
    holding: str,
    year: int,
) -> str:
    """Generate a concise ~150-word summary for the case."""
    section_str = f"under {sections[0][0]} of the {sections[0][1]}" if sections else ""
    topic_str = topics[0] if topics else "statutory interpretation"

    return (
        f"In this matter concerning {topic_str} {section_str}, "
        f"the petitioner {petitioner} challenged the action of the respondent {respondent} "
        f"on grounds of statutory non-compliance and violation of fundamental rights. "
        f"The Supreme Court, after examining the relevant statutory provisions, evidentiary record, "
        f"and applicable precedents, delivered its judgment in {year}. "
        f"{holding} "
        f"The Court also addressed ancillary questions relating to {', '.join(topics[1:3]) if len(topics) > 1 else 'procedural compliance and natural justice'}. "
        f"This judgment has significant implications for the interpretation of {sections[-1][1]} and related legislation."
    )


def generate_synthetic_corpus(n_cases: int = 1500, seed: int = 42) -> list[dict[str, Any]]:
    """
    Generate n_cases synthetic Supreme Court judgment cases.
    Each case mirrors the structure of the Shreyasrao HuggingFace dataset.
    """
    rng = random.Random(seed)
    corpus = []

    logger.info(f"Generating {n_cases} synthetic Supreme Court cases (seed={seed})...")

    for case_idx in range(n_cases):
        year = rng.randint(2005, 2024)
        case_no = f"CIVIL APPEAL NO. {rng.randint(1000, 9999)} OF {year}"

        # Sample legal topics (2-4)
        n_topics = rng.randint(2, 4)
        topics = rng.sample(LEGAL_TOPICS, n_topics)

        # Sample statutory sections (3-6)
        n_sections = rng.randint(3, 6)
        sections = rng.sample(STATUTORY_ACTS, n_sections)

        petitioner = rng.choice(PETITIONER_NAMES)
        respondent = rng.choice(RESPONDENT_NAMES)
        while respondent == petitioner:
            respondent = rng.choice(RESPONDENT_NAMES)

        judge1 = rng.choice(JUDGE_NAMES)
        judge2 = rng.choice([j for j in JUDGE_NAMES if j != judge1])
        state = rng.choice(STATES)

        facts_template = rng.choice(CASE_FACTS_TEMPLATES)
        holding = rng.choice(LEGAL_HOLDINGS)

        full_text = generate_full_judgment_text(
            rng=rng,
            case_number=case_no,
            petitioner=petitioner,
            respondent=respondent,
            judge1=judge1,
            judge2=judge2,
            topics=topics,
            sections=sections,
            facts_template=facts_template,
            holding=holding,
            year=year,
            state=state,
        )

        summary = generate_summary(petitioner, respondent, topics, sections, holding, year)

        # Appellate outcome for Theorem 2 (1=favorable/granted, 0=dismissed)
        appellate_outcome = rng.choice([0, 1])
        if "allowed" in holding.lower() or "set aside" in holding.lower():
            appellate_outcome = 1
        elif "dismissed" in holding.lower() or "upheld the conviction" in holding.lower():
            appellate_outcome = 0

        case_data = {
            "filename": f"INSC_{year}_{case_idx + 1:04d}",
            "entities": {
                "case_title": {
                    "title": f"{petitioner} v. {respondent}"
                },
                "summary": {
                    "summary": summary
                },
                "topics": [{"text": t} for t in topics],
                "sections": [{"section": s, "act": a} for s, a in sections],
                "petitioner": petitioner,
                "respondent": respondent,
                "bench": [judge1, judge2],
                "year": year,
                "case_number": case_no,
                "state": state,
            },
            "full_text": full_text,
            "appellate_outcome": appellate_outcome,
            "is_synthetic": True,
            "seed": seed,
            "case_index": case_idx,
        }

        corpus.append(case_data)

        if (case_idx + 1) % 100 == 0:
            logger.info(f"  Generated {case_idx + 1}/{n_cases} cases...")

    logger.info(f"Corpus generation complete: {len(corpus)} cases generated.")
    return corpus


def save_corpus(corpus: list[dict[str, Any]], output_path: Path) -> None:
    """Save generated corpus to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(corpus, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Corpus saved to {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic Supreme Court corpus")
    parser.add_argument("--n-cases", type=int, default=1500, help="Number of cases to generate")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=str,
        default=str(DATASET_CACHE_DIR / "synthetic_corpus.json"),
    )
    args = parser.parse_args()

    corpus = generate_synthetic_corpus(n_cases=args.n_cases, seed=args.seed)
    save_corpus(corpus, Path(args.output))
    print(f"\n[DONE] Generated {len(corpus)} cases -> {args.output}")


if __name__ == "__main__":
    main()
