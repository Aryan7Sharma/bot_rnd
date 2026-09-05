#!/usr/bin/env bash
# Cron target for the Phase 1 daily run: ingest -> score -> digest.
set -euo pipefail
cd "$(dirname "$0")/.."

kriyon-bd ingest-ted
kriyon-bd score
kriyon-bd run-digest
