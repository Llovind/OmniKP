"""Calculate a scenario from explicit human inputs in one consistent currency."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
import shlex
import sys


PARAMETERS = (
    "jam_manual", "jam_gerbang", "tarif_per_jam", "biaya_llm_per_siklus",
    "biaya_tetap_per_bulan", "siklus_per_bulan",
)


def amount(value):
    try:
        decimal = Decimal(value)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError(f"Angka tidak valid: {value}") from error
    if not decimal.is_finite() or decimal < 0:
        raise argparse.ArgumentTypeError(f"Masukkan angka hingga dan nonnegatif: {value}")
    return Fraction(decimal)


def exact(value):
    """Display exact finite decimals and preserve repeating values as fractions."""
    if value is None:
        return "tidak tercapai"
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        return f"{value.numerator}/{value.denominator} (eksak)"
    places = max(twos, fives)
    digits = abs(value.numerator) * (10**places // value.denominator)
    sign = "-" if value < 0 else ""
    if places == 0:
        return f"{sign}{digits}"
    whole, fraction = divmod(digits, 10**places)
    return f"{sign}{whole}.{str(fraction).zfill(places)}"


def calculate(inputs):
    saving = (inputs["jam_manual"] - inputs["jam_gerbang"]) * inputs["tarif_per_jam"]
    saving -= inputs["biaya_llm_per_siklus"]
    fixed = inputs["biaya_tetap_per_bulan"]
    breakeven = fixed / saving if saving > 0 else None
    monthly = saving * inputs["siklus_per_bulan"] - fixed
    return saving, breakeven, monthly


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in PARAMETERS:
        parser.add_argument("--" + field, type=amount, required=True)
    parser.add_argument("--sensitivitas", nargs=4, action="append", default=[],
                        metavar=("PARAMETER", "MIN", "MAX", "LANGKAH"),
                        help="Ubah satu parameter per rentang. Opsi ini dapat diulang.")
    args = vars(parser.parse_args())
    ranges = []
    for key, low, high, step in args.pop("sensitivitas"):
        if key not in PARAMETERS:
            parser.error(f"Parameter sensitivitas tidak dikenal: {key}")
        try:
            low, high, step = map(amount, (low, high, step))
        except argparse.ArgumentTypeError as error:
            parser.error(str(error))
        if low > high or step <= 0:
            parser.error("Rentang membutuhkan MIN <= MAX dan LANGKAH > 0.")
        ranges.append((key, low, high, step))
    return args, ranges


def main():
    inputs, ranges = parse_args()
    saving, breakeven, monthly = calculate(inputs)
    print("Status input dan skenario: ASUMSI (nilai yang diberikan pengguna)")
    print("Timestamp UTC:", datetime.now(timezone.utc).isoformat())
    print("Perintah:", shlex.join([sys.executable, *sys.argv]))
    print("Sumber:", Path(__file__).resolve())
    print("Input:", ", ".join(f"{key}={exact(value)}" for key, value in inputs.items()))
    print("Rumus hemat = (jam_manual - jam_gerbang) × tarif_per_jam - biaya_llm_per_siklus")
    print("Rumus titik impas = biaya_tetap_per_bulan / hemat, jika hemat positif")
    print("Rumus neto bulanan = hemat × siklus_per_bulan - biaya_tetap_per_bulan")
    print("Hemat per siklus:", exact(saving))
    print("Titik impas (siklus per bulan):", exact(breakeven))
    if breakeven is None:
        print("Titik impas tidak dapat dihitung dengan penghematan per siklus nonpositif.")
    print("Neto per bulan:", exact(monthly))
    print()
    print("| Parameter | Nilai | Hemat per siklus | Titik impas siklus/bulan | Neto per bulan |")
    print("| --- | --- | --- | --- | --- |")
    print(f"| Skenario awal | | {exact(saving)} | {exact(breakeven)} | {exact(monthly)} |")
    for key, value, high, step in ranges:
        while value <= high:
            result = calculate({**inputs, key: value})
            print(f"| {key} | {exact(value)} | " + " | ".join(map(exact, result)) + " |")
            value += step


if __name__ == "__main__":
    main()
