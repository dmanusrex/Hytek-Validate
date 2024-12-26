# Utility Functions

import re


def time_from_str(s: str) -> int:
    m = re.match(r"(\d+:)?(\d{1,2})\.(\d{2})", s)
    if not m:
        return 0  # Invalid time
    time = int(m[3]) + 100 * int(m[2])
    if m[1]:
        time += (60 * 100) * int(m[1][:-1])
    return time


def format_from_cs(centiseconds) -> str:
    try:
        c = centiseconds % 100
        s = (centiseconds // 100) % 60
        m = centiseconds // (100 * 60)

        parts = [
            f"{m:d}:" if m else "",
            f"{s:02d}.{c:02d}",
        ]

        return "".join(parts)
    except:
        return "0:00.00"

def hytek_stroke_code_to_text(stroke_code: str) -> str:
    if stroke_code == "A":
        return "Free"
    elif stroke_code == "B":
        return "Back"
    elif stroke_code == "C":
        return "Breast"
    elif stroke_code == "D":
        return "Fly"
    else:
        return "IM"
        
if __name__ == "__main__":
    print(time_from_str("1:23.45"))
    print(time_from_str("23.45"))
    print(time_from_str("1.23"))
    print(time_from_str("123.45"))  # Invalid
    print(time_from_str("1:23.456"))  # Invalid
    # centiseconds tests
    print(format(83))
    print(format(1234))
    print(format(12345))
    print(format(123456))
    print(format(1234567))
    print(format(12345678))  # Invalid
