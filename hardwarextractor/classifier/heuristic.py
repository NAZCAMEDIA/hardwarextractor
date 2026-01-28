from __future__ import annotations

import re
from typing import Tuple

from hardwarextractor.models.schemas import ComponentType


_PATTERNS = {
    ComponentType.CPU: [r"\bintel\b", r"\bamd\b", r"\bryzen\b", r"\bxeon\b", r"\bi[3579]-", r"\bthreadripper\b"],
    ComponentType.MAINBOARD: [r"\bmotherboard\b", r"\bmainboard\b", r"\bmb\b", r"\bz[0-9]{3}\b", r"\bb[0-9]{3}\b", r"\bx[0-9]{3}\b", r"\bprime\b", r"\brog\b"],
    ComponentType.RAM: [r"\bddr[3-5]\b", r"\bsodimm\b", r"\bdram\b", r"\bmemory\b", r"\bmt\/s\b"],
    ComponentType.GPU: [r"\brtx\b", r"\bgfx\b", r"\bradeon\b", r"\barc\b", r"\bgeforce\b", r"\bgpu\b"],
    ComponentType.DISK: [r"\bssd\b", r"\bhdd\b", r"\bnvme\b", r"\bm\.2\b", r"\bsata\b", r"\bseagate\b", r"\bwd\b", r"\bsamsung\b"],
}


def classify_component(input_normalized: str) -> Tuple[ComponentType, float]:
    best_type = ComponentType.GENERAL
    best_score = 0.0
    for component_type, patterns in _PATTERNS.items():
        score = 0.0
        for pattern in patterns:
            if re.search(pattern, input_normalized):
                score += 0.2
        if score > best_score:
            best_score = score
            best_type = component_type
    if best_score == 0.0:
        return ComponentType.GENERAL, 0.1
    return best_type, min(best_score, 0.95)
