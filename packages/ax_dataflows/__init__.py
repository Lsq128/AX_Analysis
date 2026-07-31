"""A-share and domestic data adapters for AX_Analysis."""

from ax_dataflows.inject import apply_a_share_vendors
from ax_dataflows.register import register_vendors
from ax_dataflows.symbols import is_a_share, to_akshare_code

__all__ = [
    "apply_a_share_vendors",
    "is_a_share",
    "register_vendors",
    "to_akshare_code",
]
