"""Kết quả trả về của mọi công cụ hành động."""

import copy


class ActionResult:
    """Kết quả một thao tác.

    Thuộc tính (chỉ đọc):
        ok: True nếu thao tác được chấp nhận.
        reason: mã ngắn tiếng Anh, ví dụ "ok", "missing_card", "low_battery".
        message: giải thích tiếng Việt.
        data: dict bản sao thông tin thêm (ví dụ "cost", "path").

    Có thể dùng trực tiếp trong if:
        result = ctx.open_gate("BIP", "gate_A")
        if not result:
            print(result.reason, result.message)
    """

    __slots__ = ("_ok", "_reason", "_message", "_data")

    def __init__(self, ok, reason, message, data=None):
        self._ok = bool(ok)
        self._reason = reason
        self._message = message
        self._data = copy.deepcopy(data or {})

    @property
    def ok(self):
        return self._ok

    @property
    def reason(self):
        return self._reason

    @property
    def message(self):
        return self._message

    @property
    def data(self):
        return copy.deepcopy(self._data)

    def __bool__(self):
        return self._ok

    def __repr__(self):
        return f"ActionResult(ok={self._ok}, reason={self._reason!r}, message={self._message!r})"
