"""Moderation admin (SPEC §15.5), run on the server next to the API (no AI anywhere):

  python -m borer_api.admin list              reported or hidden cases, with their texts
  python -m borer_api.admin delete <case id>  delete a case and everything in it
  python -m borer_api.admin restore <case id> make a hidden case visible again

Run: cd api && PYTHONPATH=src:../sim/src uv run python -m borer_api.admin ... [--db path]
"""
import argparse
import sys
import time
from pathlib import Path

from borer_api.app import DB
from borer_api.cases import Store


def when(t: float | None) -> str:
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(t)) if t else "-"


def listing(store: Store) -> list[str]:
    out = []
    for c in store.reported():
        out += [f"{c['id']}  opened {when(c['created_at'])}  {c['status']}  "
                f"reports {c['reports']}  hidden {when(c['hidden_at'])}",
                f"  topic: {c['topic'] or '-'}  names: {c['name_a']} / {c['name_b']}",
                f"  A: {c['text_a']}", f"  B: {c['text_b'] or '-'}"]
    return out or ["no reported or hidden cases"]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="borer_api.admin", description="HaBorer moderation")
    p.add_argument("command", choices=["list", "delete", "restore"])
    p.add_argument("case_id", nargs="?")
    p.add_argument("--db", default=DB)
    args = p.parse_args(argv)
    if not Path(args.db).exists():
        print(f"no database at {args.db}")
        return 1
    if args.command != "list" and not args.case_id:
        p.error(f"{args.command} needs a case id")
    store = Store(args.db)
    try:
        if args.command == "list":
            print("\n".join(listing(store)))
            return 0
        done = getattr(store, args.command)(args.case_id)
        print(f"{args.command} {args.case_id}: {'done' if done else 'no such case (or not hidden)'}")
        return 0 if done else 1
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
