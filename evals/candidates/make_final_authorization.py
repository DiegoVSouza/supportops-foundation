"""Write the single-use authorization of the final split, bound to the current candidate.

Run it only after the owner has said, in their own words, to run the final split, and pass
that sentence verbatim with --owner-reply: the file records the reply as the authority, so
it must never be invented. The authorization names exactly the 60 protected confirmation
calls (20 final cases x 3 trials) and the sha256 of the prompt, schema, dataset and rubric
that are in the working tree now; editing any of them afterwards closes the final split.

  python evals/candidates/make_final_authorization.py --campaign free-final-c1 \\
      --owner-reply "<the owner's sentence>"
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
LAB = PROJECT.parents[1]
sys.path.insert(0, str(PROJECT))

from scripts.campaign_execution import (  # noqa: E402
    HOLDOUT_AUTHORIZATION,
    HOLDOUT_BOUND_FILES,
    allocation_for,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True)
    parser.add_argument(
        "--owner-reply", required=True, help="the owner's authorizing sentence, verbatim"
    )
    args = parser.parse_args()
    if not re.fullmatch(r"free-final-[a-z0-9]{1,20}", args.campaign):
        raise SystemExit("campaign must look like free-final-c1")
    policy = json.loads(
        (LAB / "shared/policies/groq-free-campaign.json").read_text(encoding="utf-8")
    )
    path = LAB / HOLDOUT_AUTHORIZATION
    if path.exists():
        raise SystemExit(f"{path} already exists: the final split is single use")
    authorization = {
        "authorization_id": "p00-final-run-v1",
        "authority": "explicit_user_reply",
        "project": "p00",
        "stage": "holdout",
        "campaign": args.campaign,
        "max_calls": 60,
        "trials_per_case": 3,
        "single_use": True,
        "authorized_paid_spend_usd": "0.00",
        "owner_total_loss_cap_usd": "5.00",
        "policy_requests": allocation_for(policy)["policy"]["requests"],
        "independent_review": "WAIVED_BY_OWNER",
        "owner_reply": args.owner_reply,
        "note": "One run only. Editing the prompt, schema, dataset or rubric after this file is written closes the final split.",
        **{
            field: hashlib.sha256((PROJECT / relative).read_bytes()).hexdigest()
            for field, relative in HOLDOUT_BOUND_FILES.items()
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(authorization, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(LAB)} for {args.campaign}")


if __name__ == "__main__":
    main()
