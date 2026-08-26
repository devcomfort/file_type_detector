"""Build the supply-chain source manifest (JSON) and human-readable fixture-sources.md."""

import hashlib
import json
import os
import re
import sys

ROOT = "/mnt/workspace/projects/file_type_detector-backend-conformance"
sys.path.insert(0, ROOT)

COMMIT = "7354692a691e66380e6572c3a18e20ac99771f7d"
SAMPLE_FILES_REPO = "iamahsanmehmood/sample-files"

cand = json.load(
    open(os.path.join(ROOT, "tests/truth/backend_inventory_candidates.json"))
)
srcmd = open(os.path.join(ROOT, "tests/fixtures/SOURCES.md")).read()

dl_iam = set(
    re.findall(
        r"^- `sample\.([^`]+)` \(download\): Downloaded from iamahsanmehmood",
        srcmd,
        re.M,
    )
)
dl_op = set(
    re.findall(
        r"^- `sample\.([^`]+)` \(download\): Downloaded from openpreserve", srcmd, re.M
    )
)

tree_path = "/tmp/samplefiles-tree.json"
upstream_blobs = {}
if os.path.exists(tree_path):
    tree = json.load(open(tree_path))
    upstream_blobs = {t["path"]: t["sha"] for t in tree["tree"] if t["type"] == "blob"}

by_basename = {}
for path in upstream_blobs:
    by_basename.setdefault(os.path.basename(path), []).append(path)


def git_blob_sha(data):
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


manifest = {"schema_version": 1, "commit_pins": {}, "fixtures": {}}
md_lines = [
    "# Fixture Sources",
    "",
    f"Total fixtures: **{len(cand['records'])}**",
    "",
]

for r in cand["records"]:
    rid = r["id"]
    ext = r["probe_extension"].lstrip(".")
    status = r["ground_truth_review"]["status"]
    entry = {
        "sha256": r["sha256"],
        "probe_extension": r["probe_extension"],
        "status": status,
    }

    fixture_path = os.path.join(ROOT, r["fixture"])
    local_data = (
        open(fixture_path, "rb").read() if os.path.exists(fixture_path) else b""
    )

    # Check sample-files blob match
    paths = by_basename.get(f"sample.{ext}", [])
    hits = [p for p in paths if upstream_blobs.get(p) == git_blob_sha(local_data)]

    if ext in dl_op:
        entry["source"] = {
            "type": "external",
            "repo": "openpreserve/format-corpus",
            "license": "CC0",
            "blob_verified": False,
            "note": "corpus release URL pending reconstruction",
        }
    elif hits:
        url = (
            f"https://raw.githubusercontent.com/{SAMPLE_FILES_REPO}/{COMMIT}/{hits[0]}"
        )
        entry["source"] = {
            "type": "external",
            "repo": SAMPLE_FILES_REPO,
            "commit": COMMIT,
            "path": hits[0],
            "url": url,
            "license": "MIT (files CC0)",
            "blob_verified": True,
        }
    elif ext in dl_iam:
        entry["source"] = {
            "type": "external_unresolved",
            "repo": SAMPLE_FILES_REPO,
            "license": "MIT (files CC0)",
            "note": "path not found at pinned commit; needs history search or exclusion",
        }
    else:
        entry["source"] = {"type": "generated", "generator": "scripts.generators"}

    manifest["fixtures"][rid] = entry

# Build markdown
by_source_type = {}
for rid, entry in manifest["fixtures"].items():
    stype = entry["source"]["type"]
    by_source_type.setdefault(stype, []).append(rid)

md_lines.append("## Summary\n")
for stype, rids in sorted(by_source_type.items()):
    md_lines.append(f"- **{stype}**: {len(rids)} fixtures")

md_lines.append("\n## External Sources\n")

# Group external by repo
ext_by_repo = {}
for rid in sorted(by_source_type.get("external", [])):
    e = manifest["fixtures"][rid]["source"]
    ext_by_repo.setdefault(e["repo"], []).append((rid, e))

for repo, items in sorted(ext_by_repo.items()):
    license_str = items[0][1].get("license", "unknown")
    md_lines.append(f"### {repo}\n")
    md_lines.append(f"**License**: {license_str}\n")
    for rid, e in items:
        url = e.get("url", "N/A")
        verified = "✅ blob verified" if e.get("blob_verified") else "⚠️ unverified"
        md_lines.append(
            f"- `{rid.replace('sample-', '')}` — [source]({url}) ({verified})"
        )
    md_lines.append("")

# Unresolved externals
unresolved_exts = sorted(by_source_type.get("external_unresolved", []))
if unresolved_exts:
    md_lines.append("### Unresolved External Provenance\n")
    md_lines.append(
        "These fixtures are claimed to be from an external source but the exact path could not be verified at the pinned commit.\n"
    )
    for rid in unresolved_exts:
        md_lines.append(f"- `{rid}`")

md_lines.append("\n## Generated Fixtures\n")
gen_rids = sorted(by_source_type.get("generated", []))
md_lines.append(f"Total generated: {len(gen_rids)}\n")

manifest["summary"] = {
    "total": len(manifest["fixtures"]),
    "by_type": dict(by_source_type),
}

json.dump(manifest, open("/tmp/source_manifest_draft.json", "w"), indent=1)
open("/tmp/fixture_sources_md.txt", "w").write("\n".join(md_lines))
print(f"manifest: {len(manifest['fixtures'])} fixtures | types: {dict(by_source_type)}")
