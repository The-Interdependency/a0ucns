# 17:10
"""
disk_flip — provisional dual operation on UCNSObject.

hmmm: spec law "disk_flip(open-mark) = close-mark" not yet verified
      against ucns_v04.multiply. Provisional: swap n_dec and n_min.
      Provisional status propagates to any consumer of this module.
"""
from __future__ import annotations

try:
    from ucns_v04 import UCNSObject
    _EDCMBONE_AVAILABLE = True
except ImportError:
    _EDCMBONE_AVAILABLE = False


def disk_flip(obj) -> object:
    """
    Return the disk-dual of obj.

    Provisional: swap n_dec and n_min; pass anchors_pos and faces_pos through.
    """
    if not _EDCMBONE_AVAILABLE:
        raise RuntimeError(
            "edcmbone not importable. Resolve edcmbone issue #46."
        )
    return UCNSObject(
        n_dec=obj.n_min,
        n_min=obj.n_dec,
        anchors_pos=obj.anchors_pos,
        faces_pos=obj.faces_pos,
    )
# 17:10
