from __future__ import annotations

from pathlib import Path

import frontmatter
import networkx as nx

from .schema import IrNode


def load_one(path: Path) -> IrNode:
    post = frontmatter.load(path)
    data = dict(post.metadata)
    data.setdefault("body", [{"kind": "prose", "text": post.content}])
    return IrNode.model_validate(data)


def load_all(root: Path) -> list[IrNode]:
    if not root.exists():
        return []
    return [load_one(p) for p in root.rglob("*.md")]


def lint(nodes: list[IrNode]) -> list[str]:
    problems: list[str] = []
    by_id = {n.id: n for n in nodes}
    g: nx.DiGraph[str] = nx.DiGraph()
    for n in nodes:
        g.add_node(n.id)
        for p in n.prerequisites:
            if p not in by_id:
                problems.append(f"{n.id}: missing prereq {p}")
            g.add_edge(p, n.id)
    for cycle in nx.simple_cycles(g):
        problems.append(f"prereq cycle: {' -> '.join(cycle)}")
    orphans = [n.id for n in nodes if g.in_degree(n.id) == 0 and g.out_degree(n.id) == 0]
    if len(nodes) > 1 and len(orphans) > len(nodes) * 0.2:
        problems.append(f"{len(orphans)} orphan nodes (>20%)")
    return problems
