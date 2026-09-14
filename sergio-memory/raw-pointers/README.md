# Source pointers

This directory contains provenance records, not source documents. Use one JSON file per source and
validate it against `../schemas/source-pointer.schema.json`.

Never put secrets or sensitive originals here. For a restricted source, use an opaque locator such
as `vault://legal/matter-2026-004/document-03`, a checksum calculated locally, and a pseudonymized
description.
