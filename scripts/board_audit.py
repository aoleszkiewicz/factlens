#!/usr/bin/env python3
"""Audit the kanban board against the issues it claims to describe.

The board is only readable while its columns tell the truth. This script names every
place where they stop doing so, so drift is a red build rather than a slow decay.

    python3 scripts/board_audit.py          # report, exit 1 on drift
    python3 scripts/board_audit.py --quiet  # exit code only

Reads GitHub through `gh`; makes no writes. It walks the sub-issue and dependency
edges one issue at a time, so a full pass takes a couple of minutes — run it in the
background rather than waiting on it.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict

REPO = "aoleszkiewicz/factlens"
OWNER = "aoleszkiewicz"
PROJECT = "1"
WIP_LIMIT = 2

ACTIVE = {"Sprint", "In Progress", "Review"}


def gh(args: list[str], tries: int = 4) -> str:
    last = ""
    for attempt in range(tries):
        run = subprocess.run(["gh", *args], capture_output=True, text=True)
        if run.returncode == 0:
            return run.stdout
        last = run.stderr
        time.sleep(1.5 * (attempt + 1))
    raise SystemExit(f"gh {' '.join(args)} failed:\n{last}")


def load():
    board = json.loads(gh(["project", "item-list", PROJECT, "--owner", OWNER,
                           "--limit", "200", "--format", "json"]))["items"]
    issues = json.loads(gh(["issue", "list", "--state", "all", "--limit", "300",
                            "--json", "number,title,state,labels,body"]))

    cards = {}
    for item in board:
        number = item.get("content", {}).get("number")
        if number:
            cards[number] = item

    parent, children = {}, defaultdict(list)
    blockers = {}
    for number in sorted(issues, key=lambda i: i["number"]):
        n = number["number"]
        subs = gh(["api", f"repos/{REPO}/issues/{n}/sub_issues", "--jq", ".[].number"])
        for kid in (int(x) for x in subs.split()):
            parent[kid] = n
            children[n].append(kid)
        blocked_by = gh(["api", f"repos/{REPO}/issues/{n}/dependencies/blocked_by",
                         "--jq", ".[].number"])
        blockers[n] = [int(x) for x in blocked_by.split()]

    return cards, {i["number"]: i for i in issues}, parent, dict(children), blockers


def roll_up(kids: list[int], status_of: dict[int, str]) -> str:
    """The status a parent must show, given its children. Done > Blocked > In Progress."""
    statuses = [status_of.get(k, "Backlog") for k in kids]
    if all(s == "Done" for s in statuses):
        return "Done"
    unfinished = [s for s in statuses if s != "Done"]
    if unfinished and all(s == "Blocked" for s in unfinished):
        return "Blocked"
    if any(s in ACTIVE or s == "Done" for s in statuses):
        return "In Progress"
    return "Backlog"


def audit() -> list[str]:
    cards, issues, parent, children, blockers = load()
    status_of = {n: c.get("status") or "—" for n, c in cards.items()}
    findings: list[str] = []

    def note(kind: str, msg: str) -> None:
        findings.append(f"[{kind}] {msg}")

    for n, issue in issues.items():
        if n not in cards:
            note("off-board", f"#{n} is not on the board — {issue['title'][:60]}")

    for n, status in status_of.items():
        issue = issues.get(n)
        if not issue:
            continue
        closed = issue["state"] == "CLOSED"
        if status == "Done" and not closed:
            note("not-closed", f"#{n} sits in Done but the issue is still open")
        if closed and status != "Done":
            note("closed-elsewhere", f"#{n} is closed but the board says {status}")

        label = next((l["name"] for l in issue["labels"]
                      if l["name"].startswith("status:")), None)
        want = "status:" + status.lower().replace(" ", "-")
        if status != "—" and label != want:
            note("label-drift", f"#{n} board={status} but label={label or 'none'}")

        if status == "Done" and "- [ ]" in (issue["body"] or ""):
            left = (issue["body"] or "").count("- [ ]")
            note("unticked", f"#{n} is Done with {left} unticked acceptance box(es)")

        open_blockers = [b for b in blockers.get(n, [])
                         if issues.get(b, {}).get("state") == "OPEN"]
        if open_blockers and status not in {"Blocked", "Done"}:
            note("should-be-blocked",
                 f"#{n} is {status} but waits on {', '.join('#'+str(b) for b in open_blockers)}")
        # A parent may legitimately be Blocked without an edge of its own, when every
        # unfinished child is blocked.
        inherits_block = (n in children
                          and roll_up(children[n], status_of) == "Blocked")
        if status == "Blocked" and not open_blockers and not inherits_block:
            note("stale-block", f"#{n} sits in Blocked with no open blocker — "
                                "record the dependency or move the card")

    for n, kids in children.items():
        if n not in status_of:
            continue
        want = roll_up(kids, status_of)
        have = status_of[n]
        # A parent whose own acceptance criteria are unticked is not Done, however
        # complete its children are.
        if want == "Done" and "- [ ]" in (issues.get(n, {}).get("body") or ""):
            want = "In Progress"
        own_blocked = [b for b in blockers.get(n, [])
                       if issues.get(b, {}).get("state") == "OPEN"]
        if own_blocked:
            want = "Blocked"
        if have != want:
            kid_states = ", ".join(f"#{k}:{status_of.get(k, '—')}" for k in kids)
            note("roll-up", f"#{n} shows {have}, children imply {want} ({kid_states})")

    wip = [n for n, s in status_of.items() if s == "In Progress"
           and (issues.get(n, {}).get("labels") and
                any(l["name"] == "task" for l in issues[n]["labels"]))]
    if len(wip) > WIP_LIMIT:
        note("wip", f"{len(wip)} tasks In Progress, limit is {WIP_LIMIT}: "
                    + ", ".join(f"#{n}" for n in wip))

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true", help="exit code only")
    args = ap.parse_args()

    findings = audit()
    if not args.quiet:
        if findings:
            print(f"Board audit — {len(findings)} finding(s):\n")
            for f in sorted(findings):
                print(" ", f)
        else:
            print("Board audit — clean.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
