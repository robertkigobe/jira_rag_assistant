#!/usr/bin/env bash
# Publish the Jira Ticket Assistant to its Hugging Face Space. Every upload triggers a rebuild.
# First time only: set the ANTHROPIC_API_KEY secret in the Space's Settings.
set -euo pipefail

SPACE_REPO="rkigobe/jira-assistant"
FILES=(app.py core.py requirements.txt README.md)

cd "$(dirname "$0")"

if ! hf auth whoami >/dev/null 2>&1; then
  echo "Not logged in to Hugging Face. Run 'hf auth login' first." >&2
  exit 1
fi

# Creates the Space on the first run; does nothing if it already exists.
hf repo create "$SPACE_REPO" --repo-type space --space_sdk gradio --exist-ok

for f in "${FILES[@]}"; do
  hf upload "$SPACE_REPO" "$f" "$f" --repo-type space --commit-message "Deploy: update $f"
done

# The sample backlog lives at the repo root (shared with the notebook).
hf upload "$SPACE_REPO" ../jira_fictitious_data.csv sample_data/jira_fictitious_data.csv \
  --repo-type space --commit-message "Deploy: update sample backlog"

echo "Deployed. Space: https://huggingface.co/spaces/${SPACE_REPO}"
echo "App URL:  https://${SPACE_REPO/\//-}.hf.space"
