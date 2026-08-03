from flask import Flask, render_template, request, jsonify

from converter import decimal_to_ieee754
from rounding import round_decimal, round_binary
from arithmetic import compute

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
    """Add/multiply two IEEE 754 single-precision operands, step by step."""
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
    payload = request.get_json(silent=True) or {}
    operation = payload.get("operation", "add")
    op1_value = payload.get("op1_value", "")
    op1_format = payload.get("op1_format", "decimal")
    op2_value = payload.get("op2_value", "")
    op2_format = payload.get("op2_format", "decimal")

    if not str(op1_value).strip() or not str(op2_value).strip():
        return jsonify({"error": "Enter both operands first."}), 400

    try:
        outcome = compute(op1_value, op1_format, op2_value, op2_format, operation)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    result = outcome["result"]
    sign_bit, exponent_bits, mantissa_bits = result["binary"].split(" ")

    return jsonify(
        {
            "operation": operation,
            "operand_a": {
                "input": outcome["operand_a"]["raw"],
                "binary": outcome["operand_a"]["binary"],
                "hex": outcome["operand_a"]["hex"],
                "decimal": outcome["operand_a"]["decimal_value"],
            },
            "operand_b": {
                "input": outcome["operand_b"]["raw"],
                "binary": outcome["operand_b"]["binary"],
                "hex": outcome["operand_b"]["hex"],
                "decimal": outcome["operand_b"]["decimal_value"],
            },
            "result": {
                "binary": result["binary"],
                "hex": result["hex"],
                "sign": sign_bit,
                "exponent": exponent_bits,
                "mantissa": mantissa_bits,
                "decimal": result["decimal_value"],
            },
            "steps": outcome["steps"],
        }
    )


if __name__ == "__main__":
    app.run(debug=True)