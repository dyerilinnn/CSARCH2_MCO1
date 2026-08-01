import math

# Input: A Decimal Number
# Output: The IEEE 754 single-precision representation (including special
#         cases like NaN, Infinity, etc.) in:
#   i.)  Binary with proper spacing
#   ii.) Hexadecimal


def get_sign_bit(number):
    # math.copysign handles -0.0 correctly (plain `number < 0` does not,
    # since -0.0 < 0 evaluates to False)
    return 1 if math.copysign(1.0, number) < 0 else 0


def integer_to_binary(integer):
    integer = int(integer)
    if integer == 0:
        return "0"

    stack = []
    while integer > 0:
        stack.append(integer % 2)
        integer //= 2

    result = ""
    while stack:
        result += str(stack.pop())

    return result


def fraction_to_binary(fraction, max_bits=250):
    # max_bits is generous (250) so that very small subnormal numbers still
    # get enough precision to normalize and round correctly.
    if fraction == 0:
        return ""

    result = ""
    count = 0
    while fraction != 0 and count < max_bits:
        fraction *= 2
        bit = int(fraction)
        result += str(bit)
        fraction -= bit
        count += 1

    return result


def normalize(binary_integer, binary_fraction):
    """
    Normalizes the binary representation into the form 1.mantissa x 2^exponent.
    Returns (exponent, mantissa_bits) or None if the value is zero.
    mantissa_bits is padded to at least 24 bits (extra bit for rounding).
    """
    if binary_integer in ("0", ""):
        # Value is < 1, so the leading 1 is somewhere in the fraction bits.
        idx = binary_fraction.find("1")
        if idx == -1:
            return None  # the number is zero
        exponent = -(idx + 1)
        mantissa_bits = binary_fraction[idx + 1:]
    else:
        # Leading 1 is the first bit of the integer part.
        exponent = len(binary_integer) - 1
        mantissa_bits = binary_integer[1:] + binary_fraction

    mantissa_bits = mantissa_bits.ljust(24, "0")
    return exponent, mantissa_bits


def round_mantissa(mantissa_bits, bits=23):
    """
    Rounds mantissa_bits (string of '0'/'1') to `bits` bits using
    round-half-to-even. Returns (rounded_bits, carry) where carry=1 means
    the rounding overflowed into the next power of two (all bits became 0
    and the exponent must be incremented).
    """
    if len(mantissa_bits) <= bits:
        return mantissa_bits.ljust(bits, "0"), 0

    keep = mantissa_bits[:bits]
    rest = mantissa_bits[bits:]

    round_up = False
    if rest[0] == "1":
        if "1" in rest[1:]:
            round_up = True          # more than halfway
        elif keep[-1] == "1":
            round_up = True          # exactly halfway -> round to even

    if round_up:
        as_int = int(keep, 2) + 1
        if as_int == (1 << bits):
            return "0" * bits, 1      # overflow, e.g. 1.111...1 -> 10.000...0
        return format(as_int, f"0{bits}b"), 0

    return keep, 0


def calculate_exponent(exponent, bias=127):
    """Returns the biased exponent as an integer (not yet converted to bits)."""
    return exponent + bias


def calculate_mantissa(mantissa_bits):
    """Rounds the mantissa bit string down to the 23 stored bits."""
    return round_mantissa(mantissa_bits, 23)


def _assemble(sign, exponent_bits, mantissa_bits):
    full_binary = str(sign) + exponent_bits + mantissa_bits
    spaced_binary = f"{sign} {exponent_bits} {mantissa_bits}"
    hex_value = "0x" + format(int(full_binary, 2), "08X")
    return {"binary": spaced_binary, "hex": hex_value}


def decimal_to_ieee754(number):
    number = float(number)
    sign = get_sign_bit(number)

    # --- Special case: NaN ---
    if math.isnan(number):
        exponent_bits = "1" * 8
        mantissa_bits = "1" + "0" * 22  # canonical quiet NaN
        return _assemble(0, exponent_bits, mantissa_bits)

    # --- Special case: Infinity ---
    if math.isinf(number):
        exponent_bits = "1" * 8
        mantissa_bits = "0" * 23
        return _assemble(sign, exponent_bits, mantissa_bits)

    # --- Special case: Zero (+0 or -0) ---
    if number == 0:
        exponent_bits = "0" * 8
        mantissa_bits = "0" * 23
        return _assemble(sign, exponent_bits, mantissa_bits)

    magnitude = abs(number)
    integer_part = int(magnitude)
    fraction_part = magnitude - integer_part

    binary_integer = integer_to_binary(integer_part)
    binary_fraction = fraction_to_binary(fraction_part)

    exponent, mantissa_bits_full = normalize(binary_integer, binary_fraction)
    biased_exponent = calculate_exponent(exponent)

    # --- Overflow -> Infinity ---
    if biased_exponent >= 255:
        exponent_bits = "1" * 8
        mantissa_bits = "0" * 23
        return _assemble(sign, exponent_bits, mantissa_bits)

    # --- Subnormal / underflow ---
    if biased_exponent <= 0:
        shift = -biased_exponent  # how far to shift right for exponent -126
        full_bits = "1" + mantissa_bits_full
        shifted = "0" * shift + full_bits

        if shift > len(shifted):
            # Shifted completely past all precision -> underflows to zero
            exponent_bits = "0" * 8
            mantissa_bits = "0" * 23
            return _assemble(sign, exponent_bits, mantissa_bits)

        mantissa_bits, carry = calculate_mantissa(shifted)
        if carry:
            # Rounded up into the smallest normal number
            exponent_bits = format(1, "08b")
            mantissa_bits = "0" * 23
        else:
            exponent_bits = "0" * 8
        return _assemble(sign, exponent_bits, mantissa_bits)

    # --- Normal case ---
    mantissa_bits, carry = calculate_mantissa(mantissa_bits_full)
    if carry:
        biased_exponent += 1
        if biased_exponent >= 255:
            exponent_bits = "1" * 8
            mantissa_bits = "0" * 23
            return _assemble(sign, exponent_bits, mantissa_bits)

    exponent_bits = format(biased_exponent, "08b")
    return _assemble(sign, exponent_bits, mantissa_bits)