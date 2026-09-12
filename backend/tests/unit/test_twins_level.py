"""relaxation_level describes the best twin, not the loosest level used to fill k (data's 12:32 BREAKING)."""

from tastespace.engine.twins import LADDER, find_twins


def test_level_reflects_best_twin_not_the_fill(fx_state, monkeypatch):
    m = fx_state.model
    i = m.index["fx_noodle_soup"]
    d = m.dists_to(m.Z[i])
    cross = [j for j in range(len(m.ids)) if m.courses[j] == "savory" and m.cuisines[j] != m.cuisines[i]]
    best = min(d[j] for j in cross)
    # only the closest cross-cuisine dish is in the strict band; the other two slots need the loosest level
    monkeypatch.setattr(type(m), "similarity_pct", lambda self, dist, course: 95.0 if abs(dist - best) < 1e-9 else 10.0)
    res = find_twins(fx_state, "fx_noodle_soup", 3)
    assert len(res.twins) == 3 and res.twins[0].similarity_pct == 95.0
    assert res.relaxation_level == 0 and res.relaxation_note == LADDER[0][1]  # was 3 before the fix
