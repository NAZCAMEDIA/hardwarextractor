from __future__ import annotations

import re
from typing import Tuple

from hardwarextractor.models.schemas import ComponentType


_PATTERNS = {
    ComponentType.CPU: [
        # Marcas principales
        r"\bintel\b", r"\bamd\b",
        # Líneas de producto
        r"\bryzen\b", r"\bxeon\b", r"\bthreadripper\b", r"\bepyc\b",
        r"\bathlon\b", r"\bopteron\b", r"\bcore\b",
        # Modelos Intel Core
        r"\bi[3579]-", r"\bi[3579]\s+[0-9]{4,5}",
        # Modelos numéricos (12700K, 5900X, 7950X)
        r"\b[0-9]{4,5}[kfxu]?\b",
        # Términos genéricos
        r"\bprocessor\b", r"\bcpu\b",
    ],
    ComponentType.RAM: [
        # Tipos de memoria
        r"\bddr[3-5]\b", r"\bsodimm\b", r"\bdimm\b", r"\bdram\b",
        r"\bmemory\b", r"\bmt\/s\b", r"\bmhz\b",
        # Marcas principales
        r"\bcorsair\b", r"\bkingston\b", r"\bgskill\b", r"\bg\.skill\b",
        r"\bcrucial\b", r"\bteamgroup\b", r"\bteam\s*group\b",
        r"\bpatriot\b", r"\blexar\b", r"\badata\b",
        # Part numbers típicos
        r"\bcmk[0-9]+[a-z0-9]*\b", r"\bcmw[0-9]+[a-z0-9]*\b", r"\bcmt[0-9]+[a-z0-9]*\b",  # Corsair
        r"\bkf[45][0-9]{2}\b", r"\bkf[45]-\b",  # Kingston Fury
        r"\bf[45]-[0-9]+\b",  # G.Skill
        r"\bct[0-9]+\b",  # Crucial
        # Líneas de producto
        r"\bvengeance\b", r"\bdominator\b", r"\bfury\b",
        r"\btrident\b", r"\bripjaws\b", r"\bballistix\b",
        r"\bhyperx\b", r"\bpredator\b", r"\bbeast\b",
    ],
    ComponentType.GPU: [
        # Marcas principales
        r"\bnvidia\b", r"\bamd\b", r"\bintel\b",
        # Líneas NVIDIA
        r"\bgeforce\b", r"\brtx\b", r"\bgtx\b", r"\bquadro\b", r"\btitan\b",
        # Líneas AMD
        r"\bradeon\b", r"\brx\s*[0-9]{4}\b", r"\bfirepro\b",
        # Intel
        r"\barc\b", r"\ba[0-9]{3}\b",
        # Sufijos de modelo
        r"\b[0-9]{4}\s*ti\b", r"\b[0-9]{4}\s*super\b",
        # Término genérico
        r"\bgpu\b", r"\bgfx\b", r"\bgraphics\b",
    ],
    ComponentType.MAINBOARD: [
        # Términos genéricos
        r"\bmotherboard\b", r"\bmainboard\b", r"\bplaca\s*base\b",
        # Chipsets Intel
        r"\bz[0-9]{3}\b", r"\bb[0-9]{3}\b", r"\bh[0-9]{3}\b",
        r"\bx[0-9]{3}\b", r"\bw[0-9]{3}\b",
        # Chipsets AMD
        r"\ba[0-9]{3}\b", r"\bx[0-9]{3}e?\b",
        # Marcas
        r"\basus\b", r"\bmsi\b", r"\bgigabyte\b", r"\basrock\b",
        # Líneas de producto
        r"\bprime\b", r"\brog\b", r"\bstrix\b", r"\btuf\b",
        r"\baorus\b", r"\bmeg\b", r"\bmpg\b", r"\bmag\b",
        r"\bphantom\b", r"\bsteel\b", r"\btaichi\b",
        # Formatos
        r"\batx\b", r"\bmicro\s*atx\b", r"\bmini\s*itx\b", r"\be-atx\b",
    ],
    ComponentType.DISK: [
        # Tipos de disco
        r"\bssd\b", r"\bhdd\b", r"\bnvme\b", r"\bm\.2\b", r"\bsata\b",
        # Marcas principales
        r"\bsamsung\b", r"\bseagate\b", r"\bwd\b", r"\bwestern\s*digital\b",
        r"\bcrucial\b", r"\bkingston\b", r"\bkioxia\b", r"\bsk\s*hynix\b",
        r"\bsandisk\b", r"\btoshiba\b", r"\bphison\b",
        # Líneas de producto Samsung
        r"\bevo\b", r"\bqvo\b", r"\b9[789]0\s*pro\b", r"\b8[678]0\b",
        # Líneas WD
        r"\bsn[0-9]{3}\b", r"\bblack\b", r"\bblue\b", r"\bred\b", r"\bgold\b",
        # Líneas Seagate
        r"\bbarracuda\b", r"\bironwolf\b", r"\bfirecuda\b", r"\bexos\b",
        # Capacidades
        r"\b[0-9]+\s*[gt]b\b", r"\b[0-9]+\s*tb\b",
        # Interfaces
        r"\bpcie\b", r"\bgen[345]\b",
    ],
}


def classify_component(input_normalized: str) -> Tuple[ComponentType, float]:
    """Clasifica un componente basado en patrones heurísticos.

    Returns:
        Tuple con (ComponentType, confianza entre 0.0 y 0.95)
    """
    best_type = ComponentType.GENERAL
    best_score = 0.0
    best_matches = 0

    for component_type, patterns in _PATTERNS.items():
        matches = 0
        for pattern in patterns:
            if re.search(pattern, input_normalized, re.IGNORECASE):
                matches += 1

        if matches > 0:
            # Scoring mejorado: base + incremento por cada match adicional
            # 1 match = 0.35, 2 = 0.50, 3 = 0.65, 4 = 0.80, 5+ = 0.95
            score = min(0.35 + (matches - 1) * 0.15, 0.95)

            if score > best_score or (score == best_score and matches > best_matches):
                best_score = score
                best_type = component_type
                best_matches = matches

    if best_score == 0.0:
        return ComponentType.GENERAL, 0.1

    return best_type, best_score
