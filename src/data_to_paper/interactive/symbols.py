from typing import Optional


class Symbols:
    CHECK_SYMBOL = '✅'
    CROSS_SYMBOL = '❌'
    WARNING_SYMBOL = '⚠️'
    INFO_SYMBOL = 'ℹ️'

    @staticmethod
    def get_is_ok_symbol(is_ok: Optional[bool]) -> str:
        if is_ok is None:
            return Symbols.WARNING_SYMBOL
        return Symbols.CHECK_SYMBOL if is_ok else Symbols.CROSS_SYMBOL
