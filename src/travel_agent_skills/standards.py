from __future__ import annotations

import re

VALID_SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VALID_STATUSES = {"draft", "review", "stable", "deprecated"}

