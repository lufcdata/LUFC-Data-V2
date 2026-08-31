from pathlib import Path
import importlib.util

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "build_normalized_import.py"
spec = importlib.util.spec_from_file_location("build_normalized_import", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_competition_normalisation():
    assert mod.canonical_comp("Play-Off", mod.date(2009, 5, 14))[:2] == ("Play-Offs", "Play-Offs")
    assert mod.canonical_comp("Play-Offs", mod.date(2009, 5, 14))[:2] == ("Play-Offs", "Play-Offs")
    assert mod.canonical_comp("Associate Members Cup", mod.date(1989, 1, 1))[:2] == ("EFL Trophy", "Associate Members' Cup")
    assert mod.canonical_comp("Associate Members Cup", mod.date(2009, 1, 1))[:2] == ("EFL Trophy", "Football League Trophy")


def test_date_parser_handles_current_mixed_format():
    assert mod.parse_date("2026-03-08").isoformat() == "2026-03-08"
    assert mod.parse_date("15/03/2026").isoformat() == "2026-03-15"


def test_own_goal_variants():
    assert mod.is_own_goal({"Goal Scorer": "Phil King (0.G.)", "Goal Type": "Own Goal"})
    assert mod.is_own_goal({"Goal Scorer": "Jack Hodgson (O.G.)", "Goal Type": ""})
