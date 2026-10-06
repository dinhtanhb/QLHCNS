"""Vietnamese wording for non-negative, whole-dong draft amounts."""
from decimal import Decimal

DIGITS = ("không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín")
UNITS = ("", "nghìn", "triệu", "tỷ", "nghìn tỷ")


def amount_in_words(value):
    if value is None or value == "":
        return ""
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0 or amount != amount.to_integral_value() or amount > 9999999999999:
        raise ValueError("Amount must be a non-negative whole-dong value within the supported range.")
    number = int(amount)
    if number == 0:
        return "Không đồng chẵn"
    groups = []
    while number:
        groups.append(number % 1000)
        number //= 1000
    words = []
    for index in reversed(range(len(groups))):
        group = groups[index]
        if not group:
            continue
        hundreds, remainder = divmod(group, 100)
        tens, ones = divmod(remainder, 10)
        if hundreds or words:
            words.extend((DIGITS[hundreds], "trăm"))
        if tens:
            words.append("mười" if tens == 1 else DIGITS[tens] + " mươi")
        elif ones and (hundreds or words):
            words.append("linh")
        if ones:
            words.append("mốt" if ones == 1 and tens > 1 else "lăm" if ones == 5 and tens else DIGITS[ones])
        if UNITS[index]:
            words.append(UNITS[index])
    text = " ".join(words) + " đồng chẵn"
    return text[0].upper() + text[1:]
