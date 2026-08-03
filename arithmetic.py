import struct
from converter import decimal_to_ieee754

# Input: Operands in either decimal or IEEE hexadecimal format and type of operation
# Output: The step-by-step solution and final results (including special cases) in:
#       i) Binary with proper spacing.
#       ii) Hexadecimal.
#       iii) Decimal.

BIAS = 127
GRS_BITS = 3
TOP_BIT_POSITION = 23 + GRS_BITS


def bits_to_float(sign_bit, exponent_bits, mantissa_bits):
    full = f"{sign_bit}{exponent_bits}{mantissa_bits}"
    as_int = int(full, 2)
    return struct.unpack(">f", struct.pack(">I", as_int))[0]


def decode_fields(sign_bit, exponent_bits, mantissa_bits):
    exponent_int = int(exponent_bits, 2)

    if exponent_int == 255:
        kind = "nan" if "1" in mantissa_bits else "inf"
        return {"sign": sign_bit, "kind": kind, "exponent": None, "significand": None}

    if exponent_int == 0:
        if "1" not in mantissa_bits:
            return {"sign": sign_bit, "kind": "zero", "exponent": -126, "significand": 0}
        return {
            "sign": sign_bit,
            "kind": "subnormal",
            "exponent": -126,
            "significand": int("0" + mantissa_bits, 2),
        }

    return {
        "sign": sign_bit,
        "kind": "normal",
        "exponent": exponent_int - BIAS,
        "significand": int("1" + mantissa_bits, 2),
    }


def assemble(sign, exponent_bits, mantissa_bits):
    full_binary = f"{sign}{exponent_bits}{mantissa_bits}"
    spaced_binary = f"{sign} {exponent_bits} {mantissa_bits}"
    hex_value = "0x" + format(int(full_binary, 2), "08X")
    return {
        "sign": sign,
        "exponent_bits": exponent_bits,
        "mantissa_bits": mantissa_bits,
        "binary": spaced_binary,
        "hex": hex_value,
        "decimal_value": bits_to_float(sign, exponent_bits, mantissa_bits),
    }


def pack_nan():
    return assemble(0, "1" * 8, "1" + "0" * 22)


def pack_inf(sign):
    return assemble(sign, "1" * 8, "0" * 23)


def pack_zero(sign):
    return assemble(sign, "0" * 8, "0" * 23)


def parse_operand(raw_value, number_format):
    raw_value = str(raw_value).strip()

    if number_format == "hex":
        text = raw_value[2:] if raw_value.lower().startswith("0x") else raw_value
        text = text.strip()
        if len(text) != 8 or any(c not in "0123456789abcdefABCDEF" for c in text):
            raise ValueError(f'"{raw_value}" is not a valid 8-digit IEEE 754 hex value.')
        bits_int = int(text, 16)
        sign_bit = (bits_int >> 31) & 1
        exponent_bits = format((bits_int >> 23) & 0xFF, "08b")
        mantissa_bits = format(bits_int & 0x7FFFFF, "023b")
    elif number_format == "decimal":
        try:
            number = float(raw_value)
        except (TypeError, ValueError):
            raise ValueError(f'"{raw_value}" is not a valid decimal number.')
        result = decimal_to_ieee754(number)
        sign_str, exponent_bits, mantissa_bits = result["binary"].split(" ")
        sign_bit = int(sign_str)
    else:
        raise ValueError('number_format must be "decimal" or "hex".')

    packed = assemble(sign_bit, exponent_bits, mantissa_bits)
    decoded = decode_fields(sign_bit, exponent_bits, mantissa_bits)

    return {
        "raw": raw_value,
        "format": number_format,
        "sign": sign_bit,
        "exponent_bits": exponent_bits,
        "mantissa_bits": mantissa_bits,
        "binary": packed["binary"],
        "hex": packed["hex"],
        "decimal_value": packed["decimal_value"],
        "decoded": decoded,
    }


def _shift_right_sticky(value, shift):
    if shift <= 0:
        return value
    if shift >= value.bit_length():
        return 1 if value != 0 else 0
    lost = value & ((1 << shift) - 1)
    shifted = value >> shift
    if lost:
        shifted |= 1
    return shifted


def _round_and_pack(sign, magnitude, exponent):
    if magnitude == 0:
        return pack_zero(sign)

    if exponent + BIAS <= 0:
        extra_shift = 1 - (exponent + BIAS)
        magnitude = _shift_right_sticky(magnitude, extra_shift)
        exponent = -126

    tail = magnitude & ((1 << GRS_BITS) - 1)
    kept = magnitude >> GRS_BITS

    guard = (tail >> 2) & 1
    round_bit = (tail >> 1) & 1
    sticky = tail & 1

    round_up = bool(guard) and (bool(round_bit) or bool(sticky) or (kept & 1) == 1)
    if round_up:
        kept += 1

    if kept.bit_length() > 24:
        kept >>= 1
        exponent += 1

    if exponent + BIAS >= 255:
        return pack_inf(sign)

    is_subnormal = exponent == -126 and kept < (1 << 23)
    biased_exponent = 0 if is_subnormal else exponent + BIAS

    exponent_bits = format(biased_exponent, "08b")
    mantissa_bits = format(kept & ((1 << 23) - 1), "023b")
    return assemble(sign, exponent_bits, mantissa_bits)


def _add_magnitudes(sign_a, exponent_a, significand_a, sign_b, exponent_b, significand_b):
    reference_exponent = max(exponent_a, exponent_b)

    extended_a = _shift_right_sticky(significand_a << GRS_BITS, reference_exponent - exponent_a)
    extended_b = _shift_right_sticky(significand_b << GRS_BITS, reference_exponent - exponent_b)

    signed_a = extended_a if sign_a == 0 else -extended_a
    signed_b = extended_b if sign_b == 0 else -extended_b
    total = signed_a + signed_b

    if total == 0:
        result_sign = 1 if (sign_a == 1 and sign_b == 1) else 0
        return result_sign, None, 0, True

    result_sign = 0 if total > 0 else 1
    magnitude = abs(total)

    top_bit = magnitude.bit_length() - 1
    shift = TOP_BIT_POSITION - top_bit
    if shift > 0:
        magnitude <<= shift
        reference_exponent -= shift
    elif shift < 0:
        magnitude = _shift_right_sticky(magnitude, -shift)
        reference_exponent += -shift

    return result_sign, reference_exponent, magnitude, False


def add(decoded_a, decoded_b):
    if decoded_a["kind"] == "nan" or decoded_b["kind"] == "nan":
        return pack_nan()

    if decoded_a["kind"] == "inf" or decoded_b["kind"] == "inf":
        if decoded_a["kind"] == "inf" and decoded_b["kind"] == "inf":
            if decoded_a["sign"] != decoded_b["sign"]:
                return pack_nan()
            return pack_inf(decoded_a["sign"])
        return pack_inf(decoded_a["sign"] if decoded_a["kind"] == "inf" else decoded_b["sign"])

    sign, exponent, magnitude, is_zero = _add_magnitudes(
        decoded_a["sign"], decoded_a["exponent"], decoded_a["significand"],
        decoded_b["sign"], decoded_b["exponent"], decoded_b["significand"],
    )
    if is_zero:
        return pack_zero(sign)
    return _round_and_pack(sign, magnitude, exponent)


def multiply(decoded_a, decoded_b):
    if decoded_a["kind"] == "nan" or decoded_b["kind"] == "nan":
        return pack_nan()

    a_is_zero = decoded_a["kind"] == "zero"
    b_is_zero = decoded_b["kind"] == "zero"
    result_sign = decoded_a["sign"] ^ decoded_b["sign"]

    if decoded_a["kind"] == "inf" or decoded_b["kind"] == "inf":
        if a_is_zero or b_is_zero:
            return pack_nan()
        return pack_inf(result_sign)

    if a_is_zero or b_is_zero:
        return pack_zero(result_sign)

    product = decoded_a["significand"] * decoded_b["significand"]
    raw_exponent = decoded_a["exponent"] + decoded_b["exponent"] - 46

    top_bit = product.bit_length() - 1
    shift = top_bit - TOP_BIT_POSITION
    if shift > 0:
        magnitude = _shift_right_sticky(product, shift)
    else:
        magnitude = product << (-shift)
    exponent = raw_exponent + shift + TOP_BIT_POSITION

    return _round_and_pack(result_sign, magnitude, exponent)


def compute(op1_raw, op1_format, op2_raw, op2_format, operation):
    if operation not in ("add", "multiply"):
        raise ValueError('Operation must be "add" or "multiply".')

    operand_a = parse_operand(op1_raw, op1_format)
    operand_b = parse_operand(op2_raw, op2_format)

    if operation == "add":
        result = add(operand_a["decoded"], operand_b["decoded"])
        symbol = "+"
    else:
        result = multiply(operand_a["decoded"], operand_b["decoded"])
        symbol = "\u00d7"

    steps = [
        f"A = {operand_a['decimal_value']!r} \u2192 sign {operand_a['sign']}, "
        f"exponent {operand_a['exponent_bits']}, mantissa {operand_a['mantissa_bits']}",
        f"B = {operand_b['decimal_value']!r} \u2192 sign {operand_b['sign']}, "
        f"exponent {operand_b['exponent_bits']}, mantissa {operand_b['mantissa_bits']}",
        f"A {symbol} B computed on the aligned/multiplied significands, "
        f"then normalized and rounded to nearest, ties-to-even.",
        f"Result = {result['decimal_value']!r}",
    ]

    return {
        "operand_a": operand_a,
        "operand_b": operand_b,
        "operation": operation,
        "result": result,
        "steps": steps,
    }

