"""Bài luyện 7 — Sửa lỗi. File này CỐ Ý có hai lỗi. Chạy thử, đọc thông báo
(tên file, dòng, gợi ý), sửa rồi chạy lại cho tới khi BIP tới rally_point."""


def target_name(ctx):
    for loc in ctx.locations():
        if loc["kind"] == "rally":
            name = loc["name"]
    # Lỗi 1: hàm quên return


def run(ctx):
    target = target_name(ctx)
    ctx.move_to(target, "BIP")  # Lỗi 2: sai thứ tự tham số
