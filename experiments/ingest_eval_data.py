"""
Evaluation Harness: Data Ingestion Module (Advanced Abstractive Query Synthesis)
================================================================================

Downloads/loads Indian Supreme Court Judgments dataset,
chunks texts using TextChunker, encodes using EmbeddingGenerator (all-MiniLM-L6-v2),
indexes into isolated FAISS evaluation vector store, and synthesizes pre-outcome, non-verbatim abstractive legal evaluation queries.

DO NOT TOUCH PRODUCTION INDEX. All indices stored under backend/evaluation/eval_faiss_index/
"""

from __future__ import annotations

import json
import logging
import random
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.rag.chunker import TextChunker
from app.rag.embeddings import EmbeddingGenerator

logger = logging.getLogger("eval_harness.ingest")

EVAL_INDEX_DIR = Path(__file__).resolve().parent / "eval_faiss_index"
DATASET_CACHE_DIR = Path(__file__).resolve().parent / "dataset_cache"


class EvalDataIngester:
    """Ingests Indian Supreme Court judgments into an isolated evaluation vector store."""

    HF_REPO_API = "https://huggingface.co/api/datasets/Shreyasrao/Indian-law-supreme-court-judgements-2016/tree/main/extracted_jsons"
    HF_RAW_BASE = "https://huggingface.co/datasets/Shreyasrao/Indian-law-supreme-court-judgements-2016/raw/main/"

    def __init__(self, index_name: str = "eval_legal_index") -> None:
        self.index_name = index_name
        self.eval_index_dir = EVAL_INDEX_DIR
        self.eval_index_dir.mkdir(parents=True, exist_ok=True)
        DATASET_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        self.index_file = self.eval_index_dir / f"{index_name}.index"
        self.id_map_file = self.eval_index_dir / f"{index_name}_id_map.npy"
        self.meta_map_file = self.eval_index_dir / f"{index_name}_meta_map.json"

        self.encoder = EmbeddingGenerator()
        self.dimension = self.encoder.dimension  # 384

    def fetch_judgment_list(self, max_cases: int = 100, seed: int = 42) -> list[str]:
        """Fetch list of available JSON files from HuggingFace dataset tree."""
        cache_file = DATASET_CACHE_DIR / "file_list.json"
        if cache_file.exists():
            try:
                files = json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                files = []
        else:
            files = []

        if not files:
            req = urllib.request.Request(self.HF_REPO_API, headers={"User-Agent": "Mozilla/5.0 EvaluationHarness/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                tree_data = json.loads(resp.read().decode("utf-8"))
                files = [f["path"] for f in tree_data if f.get("path", "").endswith(".json")]
            cache_file.write_text(json.dumps(files, indent=2), encoding="utf-8")

        random.seed(seed)
        shuffled = list(files)
        random.shuffle(shuffled)
        return shuffled[:max_cases]

    def download_judgment(self, json_rel_path: str) -> dict[str, Any] | None:
        """Download and cache single judgment JSON and its corresponding MD full text."""
        basename = Path(json_rel_path).name
        local_json = DATASET_CACHE_DIR / basename
        md_rel_path = json_rel_path.replace("extracted_jsons/", "extracted_mds/").replace(".json", ".md")
        local_md = DATASET_CACHE_DIR / Path(md_rel_path).name

        if not local_json.exists():
            url_json = self.HF_RAW_BASE + json_rel_path
            try:
                req = urllib.request.Request(url_json, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    local_json.write_text(resp.read().decode("utf-8"), encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to download JSON {json_rel_path}: {e}")
                return None

        if not local_md.exists():
            url_md = self.HF_RAW_BASE + md_rel_path
            try:
                req = urllib.request.Request(url_md, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    local_md.write_text(resp.read().decode("utf-8"), encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to download MD {md_rel_path}: {e}")

        try:
            data = json.loads(local_json.read_text(encoding="utf-8"))
            data["full_text"] = local_md.read_text(encoding="utf-8") if local_md.exists() else ""
            return data
        except Exception as e:
            logger.warning(f"Failed parsing {local_json}: {e}")
            return None

    def synthesize_abstractive_query(
        self,
        summary_text: str,
        topics: list[str],
        sections: list[str],
        case_title: str = "",
    ) -> str:
        """
        Synthesizes a clean, abstractive legal evaluation query representing a realistic user question
        (advocate, clerk, or judge) without knowing case identity.

        Strips:
          - Party/litigant names (e.g. "KISHAN GOPAL", "DEVIKA BISWAS", "VIDEOCON INDUSTRIES")
          - Judge names ("DIPAK MISRA", "ROHINTON NARIMAN", "JAGDISH KHEHAR", etc.)
          - OCR/header artifacts ("Converted", "PaddleOCR", "pages", "Page", "17s", "104s")
          - Case numbers, dates, months, and procedural headers
        
        Prefers:
          - Legal topic/area (e.g. "Motor Vehicles Act, 1988", "Domestic Violence")
          - Statutory section references (e.g. "Section 166")
          - Substantive legal issue / factual context rephrasing
        """
        topic_str = topics[0] if topics else "statutory interpretation"
        
        # Clean section string: take section number and act name
        section_str = ""
        if sections:
            sec_raw = sections[0]
            m_sec = re.search(r"(?:section|sec\.|s\.|art(?:icle)?\.?)\s*(\d+[A-Z]?(?:\([a-z0-9]+\))?)", sec_raw, re.IGNORECASE)
            m_act = re.search(r"([A-Z][A-Za-z\s]{3,}(?:Act|Code|Rules|Constitution)(?:,\s*\d{4})?)", sec_raw)
            if m_sec and m_act:
                section_str = f" under Section {m_sec.group(1)} of {m_act.group(1)}"
            elif m_act:
                section_str = f" under {m_act.group(1)}"
            elif m_sec:
                section_str = f" under Section {m_sec.group(1)}"

        # Extensive stop words set
        stop_words = {
            "the", "and", "for", "that", "this", "with", "from", "court", "supreme", "appeal", "held", "ruled",
            "dismissed", "upheld", "under", "which", "were", "been", "have", "has", "had", "holding", "case",
            "concerning", "regarding", "filed", "high", "civil", "criminal", "writ", "petition", "versus", "state",
            "union", "india", "others", "another", "appellant", "respondent", "petitioner", "applicant", "converted",
            "paddleocr", "page", "pages", "version", "january", "february", "march", "april", "may", "june", "july",
            "august", "september", "october", "november", "december", "nos", "number", "date", "dated", "order",
            "judgment", "bench", "honble", "justice", "lordship", "coram", "ltd", "pvt", "corp", "co", "ors", "anr",
            "alias", "thr", "lrs", "dead", "vs", "v", "jj", "j", "http", "https", "www", "html", "pdf", "txt", "md",
            # Common Indian SC judge names
            "dipak", "misra", "nariman", "shiva", "kirti", "sikri", "agrawal", "khehar", "nagappan", "kurian",
            "joseph", "rohinton", "lokur", "lalit", "roy", "amitava", "singh", "kumar", "arvind", "sardar", "nirmal",
            "bhatia", "balram", "yadav", "fulmaniya", "biswas", "devika", "videocon", "dinesh", "maheshwari", "bhushan",
            "nazeer", "gupta", "banumathi", "bhanumathi", "chandrachud", "ramana", "bobde", "gogoi", "bose", "patil",
            "umesh", "madan", "fali", "rf", "ak", "rk", "c", "br"
        }

        # Strip all proper noun words from case_title
        if case_title:
            title_words = set(re.findall(r"\b[a-zA-Z]{2,}\b", case_title.lower()))
            stop_words.update(title_words)

        # 1. Clean out procedural headers and case numbers
        cleaned = re.sub(
            r"\b(The Supreme Court|The High Court|The Court|Civil Appeal|Criminal Appeal|Writ Petition|Special Leave Petition|SLP|No\.\s*\d+)\b",
            "", summary_text, flags=re.IGNORECASE
        )
        
        # 2. Remove digits / numbers / years
        cleaned = re.sub(r"\b\d+\b", "", cleaned)

        # 3. Extract substantive tokens
        raw_tokens = re.findall(r"\b[A-Za-z]{4,}\b", cleaned)
        
        substantive_terms: list[str] = []
        seen = set()
        
        for w in raw_tokens:
            w_lower = w.lower()
            if (
                w_lower not in stop_words 
                and not w_lower.startswith("20") 
                and not w_lower.startswith("19")
                and len(w_lower) >= 4
            ):
                if w_lower not in seen:
                    seen.add(w_lower)
                    substantive_terms.append(w_lower)

        # Take top 3 substantive legal terms
        legal_issue_terms = substantive_terms[:3]
        
        if legal_issue_terms:
            issue_desc = " regarding " + " ".join(legal_issue_terms)
        else:
            issue_desc = " regarding procedural compliance and statutory principles"

        # Formulate abstract legal query
        query = f"In a legal dispute concerning {topic_str}{section_str}, what legal principles and statutory requirements govern{issue_desc}?"
        return query.strip()

    def build_eval_index(
        self, max_cases: int = 100, seed: int = 42
    ) -> tuple[faiss.IndexFlatIP, list[str], dict[str, dict[str, Any]], list[dict[str, Any]]]:
        """
        Build isolated FAISS evaluation index and extract ground-truth evaluation queries.
        
        Returns:
            (faiss_index, id_map, meta_map, eval_queries)
        """
        logger.info(f"Starting evaluation data ingestion (max_cases={max_cases}, seed={seed})...")
        file_paths = self.fetch_judgment_list(max_cases=max_cases, seed=seed)

        all_chunks: list[str] = []
        all_chunk_ids: list[str] = []
        meta_map: dict[str, dict[str, Any]] = {}
        eval_queries: list[dict[str, Any]] = []

        roles_pool = [["judge", "clerk"], ["judge", "advocate"], ["advocate"], ["clerk"]]

        for idx, rel_path in enumerate(file_paths):
            jdata = self.download_judgment(rel_path)
            if not jdata:
                continue

            filename = jdata.get("filename", Path(rel_path).stem)
            case_id = f"CASE_INSC_{filename.replace('.json', '')}"
            
            entities = jdata.get("entities", {})
            case_title = entities.get("case_title", {}).get("title", f"Supreme Court Case {filename}")
            summary_dict = entities.get("summary", {})
            summary_text = summary_dict.get("summary", "")
            topics = [t.get("text", "") for t in entities.get("topics", []) if t.get("text")]
            sections = [f"{s.get('section', '')} {s.get('act', '')}".strip() for s in entities.get("sections", [])]

            full_text = jdata.get("full_text", "")
            if not full_text:
                full_text = jdata.get("raw_text_preview", "")

            if not full_text or len(full_text.strip()) < 100:
                continue

            chunks = TextChunker.chunk_text(full_text, chunk_size_chars=1500, overlap_chars=200)
            if not chunks:
                continue

            assigned_roles = roles_pool[idx % len(roles_pool)]
            case_chunk_ids = []

            for c_idx, chunk_content in enumerate(chunks):
                chunk_id = f"{case_id}_chk_{c_idx}"
                all_chunks.append(chunk_content)
                all_chunk_ids.append(chunk_id)
                case_chunk_ids.append(chunk_id)

                meta_map[chunk_id] = {
                    "chunk_id": chunk_id,
                    "case_id": case_id,
                    "case_title": case_title,
                    "chunk_index": c_idx,
                    "allowed_roles": assigned_roles,
                    "content": chunk_content,
                    "topics": topics,
                    "sections": sections,
                }

            primary_chunks = set(case_chunk_ids[:2])
            all_case_chunks = set(case_chunk_ids)

            if summary_text and len(summary_text.strip()) > 30:
                abstractive_q = self.synthesize_abstractive_query(summary_text, topics, sections, case_title=case_title)
                
                eval_queries.append({
                    "query_id": f"QRY_{case_id}",
                    "case_id": case_id,
                    "case_title": case_title,
                    "query_text": abstractive_q,
                    "verbatim_summary": summary_text[:300],
                    "relevant_case_id": case_id,
                    "primary_relevant_chunk_ids": primary_chunks,
                    "relevant_chunk_ids": all_case_chunks,
                    "summary_text": summary_text,
                    "topics": topics,
                    "sections": sections,
                    "required_role": assigned_roles[0],
                })

        if self.index_file.exists() and self.id_map_file.exists() and self.meta_map_file.exists():
            logger.info(f"Loading existing evaluation FAISS index from {self.index_file}...")
            index = faiss.read_index(str(self.index_file))
            id_map = list(np.load(str(self.id_map_file)))
            meta_map = json.loads(self.meta_map_file.read_text(encoding="utf-8"))
            return index, id_map, meta_map, eval_queries

        logger.info(f"Ingested {len(all_chunks)} chunks across {len(file_paths)} cases. Encoding embeddings...")

        embeddings = self.encoder.encode(all_chunks)
        faiss.normalize_L2(embeddings)

        index = faiss.IndexFlatIP(self.dimension)
        index.add(embeddings)

        faiss.write_index(index, str(self.index_file))
        np.save(str(self.id_map_file), np.array(all_chunk_ids))
        self.meta_map_file.write_text(json.dumps(meta_map, indent=2), encoding="utf-8")

        logger.info(f"Persisted evaluation index to {self.index_file} ({index.ntotal} vectors).")
        return index, all_chunk_ids, meta_map, eval_queries
