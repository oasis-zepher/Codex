from __future__ import annotations

import unittest

from codex_research_assist.ranker import (
    collect_zotero_semantic_scores,
    rank_candidates,
    score_map_match,
)


def _candidate(title: str, abstract: str, categories: list[str] | None = None, interest_ids: list[str] | None = None) -> dict:
    return {
        "paper": {
            "title": title,
            "abstract": abstract,
            "categories": categories or [],
        },
        "triage": {
            "matched_interest_ids": interest_ids or [],
        },
        "candidate": {
            "candidate_id": title.lower().replace(" ", "-")[:30],
        },
        "review": {
            "review_status": "pending",
            "recommendation": "unset",
        },
    }


def _profile(interests: list[dict] | None = None) -> dict:
    return {
        "profile_id": "test",
        "interests": interests or [
            {
                "interest_id": "pinn",
                "label": "PINN",
                "enabled": True,
                "categories": ["cs.LG"],
                "method_keywords": ["PINN", "physics-informed"],
                "query_aliases": ["physics-informed neural network"],
            },
            {
                "interest_id": "marl",
                "label": "Multi-agent RL",
                "enabled": True,
                "categories": ["cs.MA"],
                "method_keywords": ["multi-agent reinforcement learning"],
                "query_aliases": ["MARL"],
            },
        ],
    }


class ScoreMapMatchTest(unittest.TestCase):
    def test_strong_keyword_match(self) -> None:
        candidate = _candidate("PINN for Fluid Dynamics", "Physics-informed neural network applied to Navier-Stokes.", ["cs.LG"])
        score = score_map_match(candidate, _profile())
        self.assertGreater(score, 0.5)

    def test_weak_match_scores_low(self) -> None:
        candidate = _candidate("Cooking Recipe Generator", "A neural model for generating recipes from ingredients.")
        score = score_map_match(candidate, _profile())
        self.assertLess(score, 0.3)

    def test_empty_paper_scores_zero(self) -> None:
        candidate = _candidate("", "")
        score = score_map_match(candidate, _profile())
        self.assertEqual(score, 0.0)

    def test_category_match_contributes(self) -> None:
        candidate = _candidate("Some Paper", "Generic abstract about methods.", ["cs.LG"])
        score_with_category = score_map_match(candidate, _profile())
        candidate_no_cat = _candidate("Some Paper", "Generic abstract about methods.", [])
        score_no_category = score_map_match(candidate_no_cat, _profile())
        self.assertGreaterEqual(score_with_category, score_no_category)

    def test_disabled_interest_is_skipped(self) -> None:
        profile = _profile([
            {"interest_id": "off", "label": "Disabled", "enabled": False, "method_keywords": ["PINN"], "categories": ["cs.LG"]},
        ])
        candidate = _candidate("PINN for Fluid", "Physics-informed neural network.", ["cs.LG"])
        score = score_map_match(candidate, profile)
        self.assertEqual(score, 0.0)


class RankCandidatesTest(unittest.TestCase):
    def test_ranking_sorts_by_total_descending(self) -> None:
        strong = _candidate("PINN Optimization", "Physics-informed neural network optimization for PDEs.", ["cs.LG"], ["pinn"])
        weak = _candidate("Cooking Robots", "A robot that cooks food using basic sensors.")
        medium = _candidate("Multi-agent Planning", "Multi-agent reinforcement learning for cooperative tasks.", ["cs.MA"], ["marl"])
        ranked = rank_candidates([weak, strong, medium], _profile())
        ids = [c["candidate"]["candidate_id"] for c in ranked]
        self.assertEqual(ids[0], strong["candidate"]["candidate_id"])

    def test_low_map_match_penalty_applied(self) -> None:
        candidate = _candidate("Unrelated Paper", "About cooking and recipes.", [])
        ranked = rank_candidates([candidate], _profile())
        scores = ranked[0]["_scores"]
        self.assertTrue(scores["penalty_applied"])
        self.assertLess(scores["total"], 0.3)

    def test_scores_structure(self) -> None:
        candidate = _candidate("PINN Paper", "Physics-informed neural network.", ["cs.LG"])
        ranked = rank_candidates([candidate], _profile())
        scores = ranked[0]["_scores"]
        self.assertIn("map_match", scores)
        self.assertIn("zotero_semantic", scores)
        self.assertIn("total", scores)
        self.assertIn("model", scores)
        self.assertEqual(scores["model"], "map_semantic_v1")
        self.assertIn("weights", scores)
        self.assertIn("penalty_applied", scores)
        self.assertIn("semantic_available", scores)

    def test_without_semantic_uses_map_only(self) -> None:
        candidate = _candidate("PINN Paper", "Physics-informed neural network.", ["cs.LG"])
        ranked = rank_candidates([candidate], _profile(), semantic_search_fn=None)
        scores = ranked[0]["_scores"]
        self.assertFalse(scores["semantic_available"])
        self.assertEqual(scores["total"], scores["map_match"])


class SemanticScoresTest(unittest.TestCase):
    def test_collect_returns_empty_when_no_fn(self) -> None:
        candidates = [_candidate("Test", "Abstract")]
        scores, evidence = collect_zotero_semantic_scores(candidates, semantic_search_fn=None)
        self.assertEqual(scores, {})
        self.assertEqual(evidence, {})

    def test_collect_handles_exception_gracefully(self) -> None:
        def failing_fn(query: str, limit: int) -> dict:
            raise RuntimeError("db error")

        candidates = [_candidate("Test", "Abstract")]
        scores, evidence = collect_zotero_semantic_scores(candidates, semantic_search_fn=failing_fn)
        self.assertEqual(scores, {})

    def test_collect_with_mock_results(self) -> None:
        def mock_fn(query: str, limit: int) -> dict:
            return {
                "results": [
                    {"item_key": "ABC", "distance": 0.5, "metadata": {"title": "Nearby Paper", "collections": "ML"}},
                ]
            }

        candidates = [_candidate("Test Paper", "Abstract about testing.")]
        scores, evidence = collect_zotero_semantic_scores(candidates, semantic_search_fn=mock_fn)
        self.assertEqual(len(scores), 1)
        cid = list(scores.keys())[0]
        self.assertGreater(scores[cid], 0.0)
        self.assertIn(cid, evidence)
        self.assertEqual(evidence[cid]["count"], 1)
        self.assertEqual(evidence[cid]["top_title"], "Nearby Paper")


if __name__ == "__main__":
    unittest.main()
