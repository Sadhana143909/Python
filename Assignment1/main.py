
from decimal import Decimal

RATE_CARDS = {
    "normal": {
        "base_rate": Decimal("30.00"),
        "step_value": Decimal("0.40")
    },
    "apr_jun": {
        "base_rate": Decimal("32.00"),
        "step_value": Decimal("0.45")
    }
}

def rate_per_litre(fat, snf, season):
    fat = Decimal(str(fat))
    snf = Decimal(str(snf))

    card = RATE_CARDS[season]

    fat_steps = round((fat - Decimal("3.50")) / Decimal("0.10"))
    snf_steps = round((snf - Decimal("8.50")) / Decimal("0.10"))

    rate = card["base_rate"] + (
        (fat_steps + snf_steps) * card["step_value"]
    )

    return rate.quantize(Decimal("0.01"))


def bonus(litres):
    if litres > 500:
        return Decimal("0.50") * Decimal(str(litres))
    return Decimal("0.00")


def payout(litres, fat, snf, season):
    rate = rate_per_litre(fat, snf, season)
    amount = Decimal(str(litres)) * rate

    return amount.quantize(Decimal("0.01"))


def ten_day_total(entries, season):
    total_litres = 0
    total_payment = Decimal("0.00")

    for litres, fat, snf in entries:
        total_litres += litres
        total_payment += payout(litres, fat, snf, season)

    total_payment += bonus(total_litres)

    return total_payment


# Main program
entries = [
    (200, 4.0, 9.0),
    (180, 3.8, 8.8),
    (150, 4.2, 9.2)
]

season = "normal"

print("Rate per litre:", rate_per_litre(4.0, 9.0, season))
print("Bonus:", bonus(530))
print("Payout:", payout(200, 4.0, 9.0, season))
print("Ten Day Total:", ten_day_total(entries, season))
