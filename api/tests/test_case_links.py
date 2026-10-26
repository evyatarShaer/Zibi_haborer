"""Personal links (P2B-6): B bound to the first page that opens it, never to A's device or a
crawler; the daily rate limit; response allowlists (no table data, no public arguments)."""
import json

from apikit import as_b, decided, device, open_case
from borer_api import routes, views
from borer_sim import taste
from fake import OK, TEXT_B

PUBLIC = {"id", "status", "topic", "name_a", "name_b", "no_show", "error_message", "hearings"}
PERSONAL = PUBLIC | {"you", "text_a",
            "text_b", "deadline_in_s", "can_appeal", "appeal_closes_in_s"}
HEARING = {"n", "appealed_by", "status", "wait_h", "mood", "outcome", "winner", "winner_name",
           "appetite"}


def test_first_opener_is_b_others_get_taken(client):
    case = open_case(client)
    b, other = as_b(client, case), device(client)
    assert b.post(f"/api/b/{case['b']}/open").status_code == 200  # again: still B
    for r in (other.post(f"/api/b/{case['b']}/open"), other.get(f"/api/b/{case['b']}"),
              other.post(f"/api/b/{case['b']}/submit", json={"text_b": TEXT_B})):
        assert r.status_code == 403 and r.json()["error"] == views.TAKEN
    assert b.post(f"/api/b/{case['b']}/submit", json={"text_b": TEXT_B}).status_code == 200


def test_a_device_is_never_bound_as_b(client):
    case = open_case(client)
    r = client.post(f"/api/b/{case['b']}/open")
    assert r.status_code == 409 and r.json()["error"] == views.OWN_LINK
    assert client.get(f"/api/b/{case['b']}").status_code == 403
    as_b(client, case)  # B's link is still free for B


def test_crawler_get_does_not_claim_b(client):
    case = open_case(client)
    crawler = device(client)
    crawler.get(case["link_b"])          # WhatsApp's preview fetch: no JS
    crawler.get(f"/api/b/{case['b']}")   # even a GET of the API
    assert crawler.post(f"/api/b/{case['b']}/open").status_code == 200  # a real page could
    case2 = open_case(client)
    device(client).get(case2["link_b"])
    as_b(client, case2)


def test_twenty_cases_per_ip_per_day(client, clock):
    for _ in range(routes.PER_DAY):
        open_case(client)
    r = client.post("/api/case", json=OK)
    assert r.status_code == 429 and r.json()["error"] == views.LIMIT
    clock.t += 24 * 3600
    open_case(client)


def test_responses_allowlisted(client):
    case = open_case(client)
    waiting_a = client.get(f"/api/a/{case['a']}").json()
    assert set(waiting_a) == PERSONAL | {"link_b", "nudge"}
    b, a = decided(client, case)
    assert set(a) == PERSONAL and set(a["hearings"][0]) == HEARING
    pub = client.get(f"/api/c/{case['case_id']}").json()
    assert set(pub) == PUBLIC
    assert set(pub["hearings"][0]) == {"n", "appealed_by", "status", "outcome", "winner",
                                       "winner_name"}
    brain = client.get(f"/api/a/{case['a']}/brain/0").json()
    assert set(brain) == {"bin_ms", "mn9_hz", "mood", "seed", "sim_version", "platform"}
    everything = json.dumps([waiting_a, a, b.get(f"/api/b/{case['b']}").json(), pub, brain],
                            ensure_ascii=False)
    groups = {name.split(":")[1].split("/")[0] for name, _ in taste.TABLE.values()}
    assert not any(g in everything for g in groups) and "metrics" not in everything
    assert "hash" not in everything and case["a"] not in json.dumps([b.get(f"/api/b/{case['b']}").json()])
    public = json.dumps(pub, ensure_ascii=False)
    assert OK["text_a"] not in public and TEXT_B not in public and "mood" not in public
