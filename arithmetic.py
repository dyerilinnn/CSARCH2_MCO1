import struct

from converter import decimal_to_ieee754, round_mantissa

# Input:  Two operands, each given as a decimal number or an IEEE 754
#         single-precision hex word (e.g. "3.14159" or "0x40490FDB"), plus
#         an operation: "addition" or "multiplication".
# Output: A step-by-step trace of the bit-level operation, and the final
#         result (including special cases: NaN, Infinity, zero, over/underflow)
#         in binary (spaced), hex, and decimal.
#
# The rounding step reuses converter.py's round_mantissa, so arithmetic
# results are rounded the same way (round-to-nearest, ties-to-even) as a
# plain decimal-to-binary conversion.


# ---------------------------------------------------------------------------
# Parsing operands
# ---------------------------------------------------------------------------

def parse_operand(raw_value, fmt):
    """
    raw_value: the operand as typed by the user
    fmt: "decimal" or "hex"

    Returns the operand as an assembled dict (see _assemble).
    """
    if fmt == "hex":
        bits32 = _parse_hex(raw_value)
        sign = (bits32 >> 31) & 1
        exponent_bits = format((bits32 >> 23) & 0xFF, "08b")
        mantissa_bits = format(bits32 & 0x7FFFFF, "023b")
        return _assemble(sign, exponent_bits, mantissa_bits)

    if fmt == "decimal":
        if not str(raw_value).strip():
            raise ValueError("Enter a decimal value first.")
        try:
            converted = decimal_to_ieee754(raw_value)
        except (TypeError, ValueError):
            raise ValueError(f'"{raw_value}" is not a valid decimal number.')
        sign_bit, exponent_bits, mantissa_bits = converted["binary"].split(" ")
        return _assemble(int(sign_bit), exponent_bits, mantissa_bits)

    raise ValueError('format must be "decimal" or "hex".')


def _parse_hex(raw_value):
    text = str(raw_value).strip()
    if text.lower().startswith("0x"):
        text = text[2:]

    if not text:
        raise ValueError("Enter a hexadecimal value first.")
    if len(text) > 8:
        raise ValueError(f'"{raw_value}" is too long for a 32-bit single-precision hex value (max 8 hex digits).')

    try:
        return int(text, 16)
    except ValueError:
        raise ValueError(f'"{raw_value}" is not a valid hexadecimal number.')


# ---------------------------------------------------------------------------
# Assembling / categorizing a 32-bit result
# ---------------------------------------------------------------------------

def _assemble(sign, exponent_bits, mantissa_bits):
    full_binary = str(sign) + exponent_bits + mantissa_bits
    bits32 = int(full_binary, 2)
    value = struct.unpack(">f", struct.pack(">I", bits32))[0]

    return {
        "sign": sign,
        "exponent_bits": exponent_bits,
        "mantissa_bits": mantissa_bits,
        "binary": f"{sign} {exponent_bits} {mantissa_bits}",
        "hex": "0x" + format(bits32, "08X"),
        "decimal": _format_value(value),
        "category": _categorize(exponent_bits, mantissa_bits),
    }


def _categorize(exponent_bits, mantissa_bits):
    if exponent_bits == "1" * 8:
        return "infinity" if mantissa_bits == "0" * 23 else "nan"
    if exponent_bits == "0" * 8:
        return "zero" if mantissa_bits == "0" * 23 else "subnormal"
    return "normal"


def _format_value(value):
    if value != value:  # NaN
        return "NaN"
    if value == float("inf"):
        return "Infinity"
    if value == float("-inf"):
        return "-Infinity"
    return repr(value)


def _nan_result():
    return _assemble(0, "1" * 8, "1" + "0" * 22)  # canonical quiet NaN


def _infinity_result(sign):
    return _assemble(sign, "1" * 8, "0" * 23)


def _zero_result(sign):
    return _assemble(sign, "0" * 8, "0" * 23)


# ---------------------------------------------------------------------------
# Shared: normalize + round + assemble a raw (unrounded) arithmetic result
# ---------------------------------------------------------------------------

def _pack_result(sign, exponent, mantissa_bits_unrounded, steps):
    """
    sign: 0 or 1
    exponent: unbiased exponent of the leading (implicit) 1 bit
    mantissa_bits_unrounded: arbitrary-length bits after that leading 1
    """
    rounded, carry = round_mantissa(mantissa_bits_unrounded, 23)
    steps.append({
        "title": "Round (ties-to-even)",
        "detail": (
            f"Unrounded mantissa: 1.{mantissa_bits_unrounded or '0'} x 2^{exponent}. "
            f"Rounded to 23 bits: {rounded}"
            + (" (rounding carried into the next power of two)" if carry else ".")
        ),
    })

    if carry:
        exponent += 1
        rounded = "0" * 23

    biased = exponent + 127

    if biased >= 255:
        steps.append({"title": "Overflow", "detail": f"Biased exponent {biased} >= 255 -> result is Infinity."})
        return _infinity_result(sign)

    if biased <= 0:
        shift = -biased
        full = "1" + mantissa_bits_unrounded
        shifted = "0" * shift + full
        if shift > len(shifted):
            steps.append({"title": "Underflow", "detail": "Result is too small to represent -> rounds to zero."})
            return _zero_result(sign)

        sub_rounded, sub_carry = round_mantissa(shifted, 23)
        steps.append({
            "title": "Subnormal result",
            "detail": f"Biased exponent {biased} <= 0 -> result is subnormal (denormalized), shifted right by {shift} bit(s).",
        })
        if sub_carry:
            return _assemble(sign, format(1, "08b"), "0" * 23)
        return _assemble(sign, "0" * 8, sub_rounded)

    exponent_bits = format(biased, "08b")
    steps.append({
        "title": "Assemble result",
        "detail": f"Sign={sign}, biased exponent={biased} ({exponent_bits}), mantissa={rounded}.",
    })
    return _assemble(sign, exponent_bits, rounded)


def _decode_significand(op):
    """Returns (exponent, significand_bits) where significand_bits is 24
    bits: the implicit leading bit (1 for normal, 0 for subnormal) plus the
    23 stored mantissa bits."""
    biased = int(op["exponent_bits"], 2)
    if biased == 0:
        return -126, "0" + op["mantissa_bits"]
    return biased - 127, "1" + op["mantissa_bits"]


def _describe(op, label):
    exponent, sig = _decode_significand(op)
    return {
        "title": f"Convert operand {label} to single-precision format",
        "detail": (
            f"{label} = {op['decimal']} -> sign={op['sign']}, "
            f"significand=1.{sig[1:]} x 2^{exponent}" if sig[0] == "1"
            else f"{label} = {op['decimal']} -> sign={op['sign']}, "
                 f"significand=0.{sig[1:]} x 2^{exponent} (subnormal)"
        ),
    }


# ---------------------------------------------------------------------------
# Addition
# ---------------------------------------------------------------------------

def add(a, b):
    steps = [_describe(a, "A"), _describe(b, "B")]

    special = _check_special_cases_add(a, b, steps)
    if special is not None:
        return steps, special

    exp_a, sig_a = _decode_significand(a)
    exp_b, sig_b = _decode_significand(b)

    if a["category"] == "zero":
        steps.append({"title": "Zero operand", "detail": "A is zero -> result equals B exactly, no rounding needed."})
        return steps, b
    if b["category"] == "zero":
        steps.append({"title": "Zero operand", "detail": "B is zero -> result equals A exactly, no rounding needed."})
        return steps, a

    min_exp = min(exp_a, exp_b)
    shift_a = exp_a - min_exp
    shift_b = exp_b - min_exp
    a_common = int(sig_a, 2) << shift_a
    b_common = int(sig_b, 2) << shift_b

    steps.append({
        "title": "Align exponents",
        "detail": (
            f"Common exponent reference: 2^{min_exp}. "
            f"A shifted left {shift_a} bit(s), B shifted left {shift_b} bit(s) "
            f"to express both significands at the same scale."
        ),
    })

    if a["sign"] == b["sign"]:
        result_int = a_common + b_common
        result_sign = a["sign"]
        steps.append({"title": "Perform addition", "detail": f"Same sign -> add magnitudes: {bin(a_common)[2:]} + {bin(b_common)[2:]}."})
    else:
        if a_common >= b_common:
            result_int = a_common - b_common
            result_sign = a["sign"]
        else:
            result_int = b_common - a_common
            result_sign = b["sign"]
        steps.append({"title": "Subtract significands", "detail": "Opposite signs -> subtract the smaller magnitude from the larger."})

    if result_int == 0:
        steps.append({"title": "Exact cancellation", "detail": "Operands cancel exactly -> result is +0."})
        return steps, _zero_result(0)

    bit_length = result_int.bit_length()
    exponent = min_exp + bit_length - 24
    bits = format(result_int, "b")
    mantissa_unrounded = bits[1:]

    steps.append({
        "title": "Normalize",
        "detail": f"Raw result 1{mantissa_unrounded} -> leading 1 at 2^{exponent}.",
    })

    result = _pack_result(result_sign, exponent, mantissa_unrounded, steps)
    return steps, result


def _check_special_cases_add(a, b, steps):
    if a["category"] == "nan" or b["category"] == "nan":
        steps.append({"title": "Special case: NaN", "detail": "An operand is NaN -> result is NaN (invalid operation propagates)."})
        return _nan_result()

    if a["category"] == "infinity" and b["category"] == "infinity":
        if a["sign"] != b["sign"]:
            steps.append({"title": "Special case: Infinity - Infinity", "detail": "Opposite-signed infinities -> result is NaN (indeterminate)."})
            return _nan_result()
        steps.append({"title": "Special case: Infinity + Infinity", "detail": "Same-signed infinities -> result is Infinity."})
        return _infinity_result(a["sign"])

    if a["category"] == "infinity":
        steps.append({"title": "Special case: Infinity operand", "detail": "A is Infinity -> result is Infinity (Infinity absorbs any finite value)."})
        return _infinity_result(a["sign"])

    if b["category"] == "infinity":
        steps.append({"title": "Special case: Infinity operand", "detail": "B is Infinity -> result is Infinity (Infinity absorbs any finite value)."})
        return _infinity_result(b["sign"])

    if a["category"] == "zero" and b["category"] == "zero":
        if a["sign"] == b["sign"]:
            steps.append({"title": "Special case: Zero + Zero", "detail": "Both operands are zero with the same sign -> result keeps that sign."})
            return _zero_result(a["sign"])
        steps.append({"title": "Special case: Zero + Zero", "detail": "Zero plus negative zero -> result is +0."})
        return _zero_result(0)

    return None


# ---------------------------------------------------------------------------
# Multiplication
# ---------------------------------------------------------------------------

def multiply(a, b):
    steps = [_describe(a, "A"), _describe(b, "B")]
    result_sign = a["sign"] ^ b["sign"]

    special = _check_special_cases_mul(a, b, result_sign, steps)
    if special is not None:
        return steps, special

    exp_a, sig_a = _decode_significand(a)
    exp_b, sig_b = _decode_significand(b)

    a_int = int(sig_a, 2)
    b_int = int(sig_b, 2)
    product_int = a_int * b_int

    steps.append({
        "title": "Multiply significands, add exponents",
        "detail": (
            f"Significands: {sig_a} x {sig_b}. "
            f"Exponents: {exp_a} + {exp_b} = {exp_a + exp_b}. "
            f"Result sign = {a['sign']} XOR {b['sign']} = {result_sign}."
        ),
    })

    if product_int == 0:
        steps.append({"title": "Exact zero", "detail": "One operand is exactly zero magnitude -> result is zero."})
        return steps, _zero_result(result_sign)

    bit_length = product_int.bit_length()
    exponent = exp_a + exp_b + bit_length - 47
    bits = format(product_int, "b")
    mantissa_unrounded = bits[1:]

    steps.append({
        "title": "Normalize",
        "detail": f"Raw product 1{mantissa_unrounded} -> leading 1 at 2^{exponent}.",
    })

    result = _pack_result(result_sign, exponent, mantissa_unrounded, steps)
    return steps, result


def _check_special_cases_mul(a, b, result_sign, steps):
    if a["category"] == "nan" or b["category"] == "nan":
        steps.append({"title": "Special case: NaN", "detail": "An operand is NaN -> result is NaN (invalid operation propagates)."})
        return _nan_result()

    a_zero = a["category"] == "zero"
    b_zero = b["category"] == "zero"
    a_inf = a["category"] == "infinity"
    b_inf = b["category"] == "infinity"

    if (a_zero and b_inf) or (b_zero and a_inf):
        steps.append({"title": "Special case: 0 x Infinity", "detail": "Zero times Infinity is an invalid operation -> result is NaN."})
        return _nan_result()

    if a_inf or b_inf:
        steps.append({"title": "Special case: Infinity operand", "detail": f"An operand is Infinity -> result is Infinity with sign {result_sign}."})
        return _infinity_result(result_sign)

    if a_zero or b_zero:
        steps.append({"title": "Special case: Zero operand", "detail": f"An operand is zero -> result is zero with sign {result_sign}."})
        return _zero_result(result_sign)

    return None


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def compute(value_a, format_a, value_b, format_b, operation):
    """
    value_a, value_b: operands as typed by the user
    format_a, format_b: "decimal" or "hex", independently per operand
    operation: "addition" or "multiplication"

    Returns {"operand_a", "operand_b", "operation", "steps", "result"}.
    """
    if operation not in ("addition", "multiplication"):
        raise ValueError('operation must be "addition" or "multiplication".')

    operand_a = parse_operand(value_a, format_a)
    operand_b = parse_operand(value_b, format_b)

    if operation == "addition":
        steps, result = add(operand_a, operand_b)
    else:
        steps, result = multiply(operand_a, operand_b)

    return {
        "operand_a": operand_a,
        "operand_b": operand_b,
        "operation": operation,
        "steps": steps,
        "result": result,
    }
