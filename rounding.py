from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN

# Input:  A decimal or binary number (as a string), plus a target number of
#         significant digits (decimal) or significant bits (binary) to keep,
#         counted from the first nonzero digit/bit.
# Output: The same value rounded four ways:
#   i.)   Truncated               (round toward zero        / "chop")
#   ii.)  Rounded-up              (round toward +infinity    / ceiling)
#   iii.) Rounded-down            (round toward -infinity    / floor)
#   iv.)  Round-to-nearest,       (IEEE 754 default rounding mode)
#         ties-to-even
#
# These are the same four rounding modes used by IEEE 754 itself, so this
# module intentionally mirrors the vocabulary used in converter.py.


# ---------------------------------------------------------------------------
# Decimal rounding
# ---------------------------------------------------------------------------

def round_decimal(value, digits):
    """
    value: decimal number
    digits: number of significant digits to keep

    Returns four IEEE-754 rounding modes using significant digits.
    """
    digits = _validate_target(digits, unit="significant digits")

    if digits == 0:
        raise ValueError("Target significant digits must be at least 1.")

    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f'"{value}" is not a valid decimal number.')

    if not number.is_finite():
        raise ValueError("Infinity and NaN cannot be rounded.")

    if number.is_zero():
        return {
            "truncated": "0",
            "rounded_up": "0",
            "rounded_down": "0",
            "ties_to_even": "0",
        }

    # Position of the most significant digit.
    exponent = number.adjusted()

    # Quantum corresponding to the desired significant digits.
    quantum = Decimal(f"1e{exponent - digits + 1}")

    return {
        "truncated": _format_decimal(number.quantize(quantum, rounding=ROUND_DOWN)),
        "rounded_up": _format_decimal(number.quantize(quantum, rounding=ROUND_CEILING)),
        "rounded_down": _format_decimal(number.quantize(quantum, rounding=ROUND_FLOOR)),
        "ties_to_even": _format_decimal(number.quantize(quantum, rounding=ROUND_HALF_EVEN)),
    }


def _format_decimal(dec):
    if dec.is_zero():
        dec = dec.copy_abs()  # normalize -0 -> 0 for a plain rounding demo
    return format(dec, "f")


# ---------------------------------------------------------------------------
# Binary rounding
# ---------------------------------------------------------------------------

def round_binary(value, bits):
    """
    value: a binary number as a string, optionally signed, with an optional
           fractional part, e.g. "1010.1101", "-0.101", "11", "+1.1"
    bits:  number of significant bits to keep, counted from the leading 1
           (mirrors round_decimal's "significant digits", just in base 2)

    Returns four IEEE-754 rounding modes using significant bits.
    """
    bits = _validate_target(bits, unit="bits")

    if bits == 0:
        raise ValueError("Target significant bits must be at least 1.")

    sign, integer_bits, frac_bits = _parse_binary(value)
    combined = integer_bits + frac_bits
    intlen = len(integer_bits)

    first_one = combined.find("1")
    if first_one == -1:
        # The value is exactly zero -- every rounding mode agrees.
        exact = _assemble_binary("", integer_bits, frac_bits)
        return {
            "truncated": exact,
            "rounded_up": exact,
            "rounded_down": exact,
            "ties_to_even": exact,
        }

    significant_available = len(combined) - first_one

    if bits >= significant_available:
        # Fewer significant bits present than requested -- nothing to discard.
        exact = _assemble_binary(sign, integer_bits, frac_bits)
        return {
            "truncated": exact,
            "rounded_up": exact,
            "rounded_down": exact,
            "ties_to_even": exact,
        }

    window_end = first_one + bits
    kept_prefix = combined[:window_end]
    discarded = combined[window_end:]
    has_extra = "1" in discarded

    if window_end <= intlen:
        # The cut falls inside the integer part itself; the dropped low-order
        # integer bits must be re-zeroed (not just chopped off) to keep the
        # remaining bits at their original place value.
        keep_integer = kept_prefix.ljust(intlen, "0")
        keep_frac = ""
    else:
        keep_integer = combined[:intlen]
        keep_frac = combined[intlen:window_end]

    truncated = _assemble_binary(sign, keep_integer, keep_frac)
    incremented = _assemble_binary(sign, *_increment_magnitude(keep_integer, keep_frac))

    if sign == "-":
        rounded_up = truncated                          # toward zero = toward +inf for negatives
        rounded_down = incremented if has_extra else truncated
    else:
        rounded_up = incremented if has_extra else truncated
        rounded_down = truncated                         # toward zero = toward -inf for non-negatives

    ties_to_even = _round_half_even_binary(kept_prefix, discarded, truncated, incremented)

    return {
        "truncated": truncated,
        "rounded_up": rounded_up,
        "rounded_down": rounded_down,
        "ties_to_even": ties_to_even,
    }


def _round_half_even_binary(kept_prefix, discarded, truncated, incremented):
    first_discarded = discarded[0]

    if first_discarded == "0":
        return truncated  # less than halfway -> round down (toward zero)

    if "1" in discarded[1:]:
        return incremented  # more than halfway -> round away from zero

    # Exactly halfway -> round to even: look at the last kept (significant) bit.
    last_kept = kept_prefix[-1]
    return incremented if last_kept == "1" else truncated


def _increment_magnitude(integer_bits, frac_bits):
    """Adds one unit at the position just past frac_bits, e.g. incrementing
    the bits kept after rounding. Returns (new_integer_bits, new_frac_bits)."""
    combined = (integer_bits or "0") + frac_bits
    as_int = int(combined, 2) + 1
    width = len(combined)
    new_bits = format(as_int, f"0{width}b")  # grows by 1 char on carry-out

    frac_len = len(frac_bits)
    if frac_len == 0:
        return new_bits, ""

    new_integer = new_bits[:-frac_len] or "0"
    new_frac = new_bits[-frac_len:]
    return new_integer, new_frac


def _parse_binary(value):
    text = str(value).strip()
    if not text:
        raise ValueError("Enter a binary number first.")

    sign = ""
    if text[0] in "+-":
        sign = "-" if text[0] == "-" else ""
        text = text[1:]

    if text.count(".") > 1:
        raise ValueError(f'"{value}" is not a valid binary number.')

    integer_part, _, frac_part = text.partition(".")
    integer_part = integer_part or "0"

    if not integer_part.strip("01") == "" or not frac_part.strip("01") == "":
        raise ValueError(f'"{value}" is not a valid binary number (use only 0 and 1).')

    integer_part = integer_part.lstrip("0") or "0"

    if integer_part == "0" and frac_part == "" and sign:
        sign = ""  # avoid a stray "-0"

    return sign, integer_part, frac_part


def _assemble_binary(sign, integer_bits, frac_bits):
    body = integer_bits if not frac_bits else f"{integer_bits}.{frac_bits}"
    return f"{sign}{body}"


# ---------------------------------------------------------------------------
# Shared validation
# ---------------------------------------------------------------------------

def _validate_target(target, unit):
    try:
        target_int = int(target)
    except (TypeError, ValueError):
        raise ValueError(f"Target number of {unit} must be a whole number.")

    if target_int < 0:
        raise ValueError(f"Target number of {unit} cannot be negative.")

    return target_int
