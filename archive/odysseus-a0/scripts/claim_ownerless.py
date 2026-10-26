#!/usr/bin/env python3
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 64:47
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 6:2
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 31:2
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: claim_ownerless
#   module_name: claim_ownerless
#   module_kind: hmmm
#   summary: Claim all ownerless data for a specific user.
#   owner: hmmm
#   public_surface: claim_json_entries, main
#   internal_surface: none
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   tests: hmmm
#   rollout: hmmm
#   rollback: hmmm
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: claim_ownerless_boundaries
#   summary: Claim all ownerless data for a specific user.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: claim_ownerless
#   summary: Claim all ownerless data for a specific user.
#   exposes: claim_json_entries, main
# === END CAPABILITIES ===
"""Claim all ownerless data for a specific user.

Run once after enabling multi-user auth to assign existing data to the admin.

Usage:
    python scripts/claim_ownerless.py admin@example.com
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def claim_json_entries(entries, owner):
    count = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if not entry.get("owner"):
            entry["owner"] = owner
            count += 1
    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/claim_ownerless.py <username>")
        sys.exit(1)

    owner = sys.argv[1]
    print(f"Claiming all ownerless data for: {owner}\n")

    # 1. Memories (JSON files)
    for label, path in [
        ("memory.json", "data/memory.json"),
        ("skills.json", "data/skills.json"),
    ]:
        if not os.path.exists(path):
            print(f"  {label}: not found, skipping")
            continue
        with open(path, "r", encoding="utf-8") as f:
            entries = json.load(f)
        count = claim_json_entries(entries, owner)
        if count:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"  {label}: claimed {count} entries")

    # 2. Database tables (sessions, gallery, comparisons, documents)
    from core.database import SessionLocal, Session, Document
    try:
        from core.database import GalleryImage
    except ImportError:
        GalleryImage = None
    try:
        from core.database import Comparison
    except ImportError:
        Comparison = None

    db = SessionLocal()
    try:
        # Sessions
        count = db.query(Session).filter(Session.owner == None).update({"owner": owner})
        print(f"  sessions: claimed {count}")

        # Documents (have their own owner column; claim the ownerless ones,
        # mirroring the sessions/gallery/comparisons blocks). The old query set
        # session_id to itself — a no-op — and never set owner, so ownerless
        # documents stayed ownerless and invisible in the user's Library.
        count = db.query(Document).filter(Document.owner == None).update({"owner": owner})
        print(f"  documents: claimed {count}")

        # Gallery
        if GalleryImage:
            count = db.query(GalleryImage).filter(GalleryImage.owner == None).update({"owner": owner})
            print(f"  gallery: claimed {count}")

        # Comparisons
        if Comparison:
            count = db.query(Comparison).filter(Comparison.owner == None).update({"owner": owner})
            print(f"  comparisons: claimed {count}")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"  ERROR: {e}")
    finally:
        db.close()

    print(f"\nDone! All ownerless data now belongs to {owner}")
    print("Restart the server: sudo systemctl restart odysseus-ui")


if __name__ == "__main__":
    main()
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 64:47
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 6:2
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 31:2
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
