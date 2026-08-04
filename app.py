from flask import Flask, render_template, request, jsonify

from converter import decimal_to_ieee754
from rounding import round_decimal, round_binary
from arithmetic import compute as compute_arithmetic

app = Flask(__name__)


@app.route("/")
def index():
    """Main menu."""
    return render_template("index.html")


@app.route("/convert")
def convert_page():
    """Decimal -> IEEE 754 single-precision conversion page."""
    return render_template("convert.html")


@app.route("/rounding")
def rounding_page():
    """Rounding methods demonstration page."""
    return render_template("rounding.html")


@app.route("/arithmetic")
def arithmetic_page():
    """Arithmetic (addition / multiplication) demonstration page."""
    return render_template("arithmetic.html")


@app.route("/api/convert", methods=["POST"])
def api_convert():
    """
    JSON API used by script.js on convert.html.

    Expects: {"value": "<decimal number as typed by the user>"}
    Returns: {
        "input": "...",
        "binary": "s eeeeeeee mmmmmmmmmmmmmmmmmmmmmmm",
        "hex": "0xXXXXXXXX",
        "sign": "s",
        "exponent": "eeeeeeee",
        "mantissa": "mmmmmmmmmmmmmmmmmmmmmmm"
    }
    """
    payload = request.get_json(silent=True) or {}
    raw_value = payload.get("value", "")

    try:
        number = float(raw_value)
    except (TypeError, ValueError):
        return jsonify({"error": f'"{raw_value}" is not a valid decimal number.'}), 400

    result = decimal_to_ieee754(number)
    binary = result["binary"]
    hex_value = result["hex"]
    sign_bit, exponent_bits, mantissa_bits = binary.split(" ")

    return jsonify(
        {
            "input": raw_value,
            "binary": binary,
            "hex": hex_value,
            "sign": sign_bit,
            "exponent": exponent_bits,
            "mantissa": mantissa_bits,
        }
    )


@app.route("/api/round", methods=["POST"])
def api_round():
    """
    JSON API used by script.js on rounding.html.

    Expects: {
        "base": "decimal" | "binary",
        "value": "<number as typed by the user>",
        "target": "<target digits/bits, as a string or number>"
    }
    Returns: {
        "base": "decimal" | "binary",
        "input": "...",
        "target": 2,
        "truncated": "...",
        "rounded_up": "...",
        "rounded_down": "...",
        "ties_to_even": "..."
    }
    """
    payload = request.get_json(silent=True) or {}
    base = payload.get("base", "decimal")
    raw_value = payload.get("value", "")
    raw_target = payload.get("target", "")

    if base not in ("decimal", "binary"):
        return jsonify({"error": 'base must be "decimal" or "binary".'}), 400

    try:
        target = int(raw_target)
    except (TypeError, ValueError):
        return jsonify({"error": "Target digits/bits must be a whole number."}), 400

    try:
        if base == "binary":
            results = round_binary(raw_value, target)
        else:
            results = round_decimal(raw_value, target)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "base": base,
            "input": raw_value,
            "target": target,
            **results,
        }
    )


@app.route("/api/arithmetic", methods=["POST"])
def api_arithmetic():
    """
    JSON API used by script.js on arithmetic.html.

    Expects: {
        "value_a": "...", "format_a": "decimal" | "hex",
        "value_b": "...", "format_b": "decimal" | "hex",
        "operation": "addition" | "multiplication"
    }
    Returns: {
        "operation": "...",
        "operand_a": {sign, exponent_bits, mantissa_bits, binary, hex, decimal, category},
        "operand_b": {...same shape...},
        "steps": [{"title": "...", "detail": "..."}, ...],
        "result": {...same shape as operand_a/b...}
    }
    """
    payload = request.get_json(silent=True) or {}
    value_a = payload.get("value_a", "")
    format_a = payload.get("format_a", "decimal")
    value_b = payload.get("value_b", "")
    format_b = payload.get("format_b", "decimal")
    operation = payload.get("operation", "addition")

    try:
        result = compute_arithmetic(value_a, format_a, value_b, format_b, operation)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)


if __name__ == "__main__":
    app.run()
