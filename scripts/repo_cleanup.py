#!/usr/bin/env python3
"""
Herramienta para auditar duplicados de documentación y scripts.

Características principales:
  * Indexa archivos .md y .py que están fuera de la estructura whitelist,
    además de documentos no permitidos dentro de docs/ y scripts/.
  * Calcula similitud por hash exacto, coseno TF-IDF y Jaccard.
  * Agrupa near-duplicados utilizando Union-Find.
  * Determina candidato canónico por grupo (documentos: más extenso/reciente;
    scripts: mayor cantidad de referencias desde api/, apps/,
    yolo_carla_pipeline/ y tests/).
  * Genera un reporte JSON con la información necesaria para tomar acciones.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent

# Estructura whitelisted solicitada
WHITELIST_DIRS = {
    ".github",
    "api",
    "apps",
    "config",
    "data",
    "docker",
    "docs",
    "scripts",
    "tests",
    "yolo_carla_pipeline",
    "legacy",
}

WHITELIST_FILES = {
    "README.md",
    "MANUAL_PASO_A_PASO.md",
    "CHANGELOG.md",
    "docker-compose.yml",
    "DEPLOYMENT.md",
    ".env.example",
}

# Documentos permitidos en docs/
DOCS_ALLOWED = {
    "INSTALACION.md",
    "ARQUITECTURA.md",
    "DESARROLLO.md",
    "USO_API_Y_FRONTEND.md",
}

# Directorios desde donde se consideran referencias activas a scripts.
REFERENCE_DIRS = [
    ROOT / "api",
    ROOT / "apps",
    ROOT / "yolo_carla_pipeline",
    ROOT / "tests",
]

SIMILARITY_THRESHOLD = 0.85

TOKEN_REGEX = re.compile(r"[a-z0-9áéíóúñü]+", re.IGNORECASE)


@dataclass
class FileInfo:
    path: str
    extension: str
    size: int
    mtime: float
    sha256: str
    word_count: int
    tokens: List[str]
    token_set: Set[str]
    references: int = 0

    @property
    def category(self) -> str:
        return "script" if self.extension == ".py" else "doc"


class UnionFind:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}

    def find(self, item: str) -> str:
        if item not in self.parent:
            self.parent[item] = item
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, a: str, b: str) -> None:
        root_a = self.find(a)
        root_b = self.find(b)
        if root_a == root_b:
            return
        # Unión simple: raíz lexicográficamente menor
        if root_a < root_b:
            self.parent[root_b] = root_a
        else:
            self.parent[root_a] = root_b


def should_index(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if rel.parts[0] == ".git":
        return False
    if any(part.startswith(".") for part in rel.parts):
        return False
    if rel.suffix.lower() not in (".md", ".py"):
        return False

    top = rel.parts[0]
    filename = rel.name

    # Archivos en raíz permitidos
    if len(rel.parts) == 1 and filename in WHITELIST_FILES:
        return False

    # Documentos permitidos dentro de docs/
    if top == "docs" and filename in DOCS_ALLOWED and len(rel.parts) == 2:
        return False

    # scripts/repo_cleanup.py debe excluirse para evitar auto-referencias
    if rel == Path("scripts/repo_cleanup.py"):
        return False

    # Cualquier otro archivo dentro del whitelist pero no explícitamente permitido se analiza.
    if top in WHITELIST_DIRS:
        return True

    # Si está fuera del whitelist, definitivamente se analiza.
    return True


def tokenize(text: str) -> List[str]:
    return TOKEN_REGEX.findall(text.lower())


def compute_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def collect_reference_index() -> Dict[str, str]:
    reference_texts: Dict[str, str] = {}
    for directory in REFERENCE_DIRS:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file():
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                reference_texts[str(path)] = text
    return reference_texts


def count_references(basename: str, reference_index: Dict[str, str]) -> int:
    pattern = re.compile(rf"\b{re.escape(basename)}\b")
    count = 0
    for text in reference_index.values():
        count += len(pattern.findall(text))
    return count


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    shared = set(vec_a.keys()) & set(vec_b.keys())
    numerator = sum(vec_a[token] * vec_b[token] for token in shared)
    if numerator == 0:
        return 0.0
    norm_a = math.sqrt(sum(value * value for value in vec_a.values()))
    norm_b = math.sqrt(sum(value * value for value in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return numerator / (norm_a * norm_b)


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def build_tfidf_vectors(files: List[FileInfo]) -> Dict[str, Dict[str, float]]:
    if not files:
        return {}
    doc_freq: Counter[str] = Counter()
    for info in files:
        doc_freq.update(set(info.tokens))

    total_docs = len(files)
    vectors: Dict[str, Dict[str, float]] = {}

    for info in files:
        tf = Counter(info.tokens)
        total_terms = sum(tf.values()) or 1
        vec: Dict[str, float] = {}
        for token, count in tf.items():
            df = doc_freq[token]
            idf = math.log((1 + total_docs) / (1 + df)) + 1
            tfidf = (count / total_terms) * idf
            vec[token] = tfidf
        vectors[info.path] = vec
    return vectors


def family_label(path: Path) -> str:
    name = path.stem.lower()
    if "_" in name:
        prefix = name.split("_", 1)[0]
        if len(prefix) >= 3:
            return prefix
    if "-" in name:
        prefix = name.split("-", 1)[0]
        if len(prefix) >= 3:
            return prefix
    return name[:8]


def choose_canonical(group: List[FileInfo]) -> FileInfo:
    scripts = [info for info in group if info.category == "script"]
    docs = [info for info in group if info.category == "doc"]

    if scripts:
        scripts.sort(
            key=lambda info: (
                info.references,
                info.word_count,
                info.mtime,
            ),
            reverse=True,
        )
        return scripts[0]

    docs.sort(
        key=lambda info: (
            info.word_count,
            info.mtime,
        ),
        reverse=True,
    )
    return docs[0]


def analyze_files(threshold: float) -> Dict[str, object]:
    reference_index = collect_reference_index()

    indexed_files: List[FileInfo] = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if not should_index(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        tokens = tokenize(text)
        info = FileInfo(
            path=str(path.relative_to(ROOT)),
            extension=path.suffix.lower(),
            size=path.stat().st_size,
            mtime=path.stat().st_mtime,
            sha256=compute_sha256(text),
            word_count=len(tokens),
            tokens=tokens,
            token_set=set(tokens),
        )
        if info.category == "script":
            basename = Path(info.path).stem
            info.references = count_references(basename, reference_index)
        indexed_files.append(info)

    print(f"[repo_cleanup] Archivos indexados: {len(indexed_files)}")

    vectors = build_tfidf_vectors(indexed_files)
    uf = UnionFind()
    similarities: Dict[Tuple[str, str], Dict[str, float]] = {}

    grouped: Dict[Tuple[str, str], List[FileInfo]] = defaultdict(list)
    for info in indexed_files:
        fam = family_label(Path(info.path))
        grouped[(info.category, fam)].append(info)

    print(f"[repo_cleanup] Grupos preliminares: {len(grouped)}")

    for (_, _), members in grouped.items():
        if len(members) == 1:
            # Nada que comparar
            member = members[0]
            if member.category == "script" and member.references == 0:
                # Seguimos detectando scripts huérfanos más abajo
                pass
            continue

        for i, info_a in enumerate(members):
            for info_b in members[i + 1 :]:
                pair = (info_a.path, info_b.path)
                record = {
                    "hash_equal": info_a.sha256 == info_b.sha256,
                    "cosine": 0.0,
                    "jaccard": 0.0,
                }

                if record["hash_equal"]:
                    uf.union(info_a.path, info_b.path)
                    similarities[pair] = record
                    continue

                vec_a = vectors.get(info_a.path, {})
                vec_b = vectors.get(info_b.path, {})
                record["cosine"] = cosine_similarity(vec_a, vec_b)
                record["jaccard"] = jaccard_similarity(info_a.token_set, info_b.token_set)
                if (
                    record["cosine"] >= threshold
                    or record["jaccard"] >= threshold
                ):
                    uf.union(info_a.path, info_b.path)
                    similarities[pair] = record

    clusters: Dict[str, List[FileInfo]] = defaultdict(list)
    for info in indexed_files:
        root_id = uf.find(info.path)
        clusters[root_id].append(info)

    print(f"[repo_cleanup] Clusters detectados: {len(clusters)}")

    groups_output = []
    orphan_scripts = []

    for cluster_id, members in clusters.items():
        if len(members) == 1:
            member = members[0]
            if member.category == "script" and member.references == 0:
                orphan_scripts.append(member.path)
            continue

        canonical = choose_canonical(members)
        group_similarities = []

        for info in members:
            if info.path == canonical.path:
                continue
            key = tuple(sorted([info.path, canonical.path]))
            data = similarities.get(key)
            if data is None:
                # Intentar recuperar con el orden original
                key = (canonical.path, info.path)
                data = similarities.get(key)
            if data:
                group_similarities.append(
                    {
                        "target": info.path,
                        "hash_equal": data["hash_equal"],
                        "cosine": round(data["cosine"], 4),
                        "jaccard": round(data["jaccard"], 4),
                    }
                )

        groups_output.append(
            {
                "group_id": cluster_id,
                "family": family_label(Path(cluster_id)),
                "canonical": {
                    "path": canonical.path,
                    "category": canonical.category,
                    "references": canonical.references,
                    "word_count": canonical.word_count,
                    "size": canonical.size,
                },
                "members": sorted(
                    [
                        {
                            "path": info.path,
                            "category": info.category,
                            "references": info.references,
                            "word_count": info.word_count,
                            "size": info.size,
                            "sha256": info.sha256,
                        }
                        for info in members
                    ],
                    key=lambda entry: entry["path"],
                ),
                "similar_to_canonical": group_similarities,
            }
        )

    groups_output.sort(key=lambda g: (g["family"], g["canonical"]["path"]))
    orphan_scripts.sort()

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "threshold": threshold,
        "indexed_files": len(indexed_files),
        "groups": groups_output,
        "orphan_scripts": orphan_scripts,
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analiza duplicados de documentación y scripts fuera del whitelist."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=SIMILARITY_THRESHOLD,
        help="Umbral de similitud para considerar near-duplicados (default: 0.85).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(ROOT / "legacy" / "cleanup" / "duplicates_report.json"),
        help="Ruta del archivo JSON de salida.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Imprime un resumen legible en consola.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    result = analyze_files(args.threshold)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.summary:
        print(f"Archivos indexados: {result['indexed_files']}")
        print(f"Grupos detectados: {len(result['groups'])}")
        if result["orphan_scripts"]:
            print("Scripts huérfanos:")
            for item in result["orphan_scripts"]:
                print(f"  - {item}")
        else:
            print("Sin scripts huérfanos detectados.")

    print(f"Reporte generado en {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

