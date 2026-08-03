/**
 * script.js — IEEE 754 Machine controller
 *
 * Currently wires up the Convert page (#convert-form). Rounding and
 * Arithmetic pages will register their own handlers here once
 * rounding.html / arithmetic.html exist — follow the same pattern:
 * grab the form by id, prevent default, fetch its /api/... endpoint,
 * render results, handle errors.
 */

(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    initConvertForm();
    initRoundingForm();
    initArithmeticForm();
  }

  function initConvertForm() {
    const form = document.getElementById("convert-form");
    if (!form) return; // not on the convert page

    const input = document.getElementById("decimal-input");
    const errorBox = document.getElementById("error-message");
    const resultPanel = document.getElementById("result-panel");

    const outSign = document.getElementById("out-sign");
    const outExponent = document.getElementById("out-exponent");
    const outMantissa = document.getElementById("out-mantissa");
    const outBinary = document.getElementById("out-binary");
    const outHex = document.getElementById("out-hex");

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      hideError();

      const value = input.value.trim();
      if (!value) {
        showError("Enter a decimal number first.");
        return;
      }

      setLoading(true);

      try {
        const response = await fetch("/api/convert", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ value }),
        });

        const data = await response.json();

        if (!response.ok) {
          showError(data.error || "Something went wrong. Try a different value.");
          resultPanel.hidden = true;
          return;
        }

        renderResult(data);
      } catch (err) {
        showError("Could not reach the server. Check your connection and try again.");
        resultPanel.hidden = true;
      } finally {
        setLoading(false);
      }
    });

    function renderResult(data) {
      outSign.textContent = data.sign;
      outExponent.textContent = data.exponent;
      outMantissa.textContent = data.mantissa;
      outBinary.textContent = data.binary;
      outHex.textContent = data.hex;
      resultPanel.hidden = false;
    }

    function showError(message) {
      errorBox.textContent = message;
      errorBox.hidden = false;
    }

    function hideError() {
      errorBox.hidden = true;
      errorBox.textContent = "";
    }

    function setLoading(isLoading) {
      const button = form.querySelector('button[type="submit"]');
      if (!button) return;
      button.disabled = isLoading;
      button.textContent = isLoading ? "Converting…" : "Convert";
    }
  }

  function initRoundingForm() {
    const form = document.getElementById("rounding-form");
    if (!form) return; // not on the rounding page

    const valueInput = document.getElementById("round-value-input");
    const targetInput = document.getElementById("round-target-input");
    const valueLabel = document.getElementById("value-label");
    const targetLabel = document.getElementById("target-label");
    const baseRadios = form.querySelectorAll('input[name="base"]');

    const errorBox = document.getElementById("error-message");
    const resultPanel = document.getElementById("result-panel");
    const outEcho = document.getElementById("out-echo");
    const outTruncated = document.getElementById("out-truncated");
    const outRoundedUp = document.getElementById("out-rounded-up");
    const outRoundedDown = document.getElementById("out-rounded-down");
    const outTiesToEven = document.getElementById("out-ties-to-even");

    const COPY = {
      decimal: {
        valueLabel: "Decimal number",
        valuePlaceholder: "e.g. 3.14159, -2.5, 2.675",
        targetLabel: "Digits after the decimal point",
        targetUnit: "digit(s)",
      },
      binary: {
        valueLabel: "Binary number",
        valuePlaceholder: "e.g. 1.1011, -0.101, 1010",
        targetLabel: "Bits after the binary point",
        targetUnit: "bit(s)",
      },
    };

    baseRadios.forEach(function (radio) {
      radio.addEventListener("change", applyBaseCopy);
    });
    applyBaseCopy();

    function applyBaseCopy() {
      const base = getSelectedBase();
      const copy = COPY[base];
      valueLabel.textContent = copy.valueLabel;
      valueInput.placeholder = copy.valuePlaceholder;
      valueInput.inputMode = base === "binary" ? "numeric" : "decimal";
      targetLabel.textContent = copy.targetLabel;
    }

    function getSelectedBase() {
      const checked = form.querySelector('input[name="base"]:checked');
      return checked ? checked.value : "decimal";
    }

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      hideError();

      const base = getSelectedBase();
      const value = valueInput.value.trim();
      const target = targetInput.value.trim();

      if (!value) {
        showError("Enter a number first.");
        return;
      }
      if (target === "" || Number(target) < 0 || !Number.isInteger(Number(target))) {
        showError("Target digits/bits must be a whole number of 0 or more.");
        return;
      }

      setLoading(true);

      try {
        const response = await fetch("/api/round", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ base, value, target }),
        });

        const data = await response.json();

        if (!response.ok) {
          showError(data.error || "Something went wrong. Try a different value.");
          resultPanel.hidden = true;
          return;
        }

        renderResult(data);
      } catch (err) {
        showError("Could not reach the server. Check your connection and try again.");
        resultPanel.hidden = true;
      } finally {
        setLoading(false);
      }
    });

    function renderResult(data) {
      const unit = COPY[data.base].targetUnit;
      outEcho.textContent = `${data.input} rounded to ${data.target} ${unit}`;
      outTruncated.textContent = data.truncated;
      outRoundedUp.textContent = data.rounded_up;
      outRoundedDown.textContent = data.rounded_down;
      outTiesToEven.textContent = data.ties_to_even;
      resultPanel.hidden = false;
    }

    function showError(message) {
      errorBox.textContent = message;
      errorBox.hidden = false;
    }

    function hideError() {
      errorBox.hidden = true;
      errorBox.textContent = "";
    }

    function setLoading(isLoading) {
      const button = form.querySelector('button[type="submit"]');
      if (!button) return;
      button.disabled = isLoading;
      button.textContent = isLoading ? "Rounding…" : "Round";
    }
  }

  function initArithmeticForm() {
  const form = document.getElementById("arithmetic-form");
  if (!form) return; // not on the arithmetic page

  const op1Input = document.getElementById("op1-value-input");
  const op2Input = document.getElementById("op2-value-input");

  const errorBox = document.getElementById("error-message");
  const resultPanel = document.getElementById("result-panel");

  const outEcho = document.getElementById("out-echo");
  const outSign = document.getElementById("out-sign");
  const outExponent = document.getElementById("out-exponent");
  const outMantissa = document.getElementById("out-mantissa");
  const outBinary = document.getElementById("out-binary");
  const outHex = document.getElementById("out-hex");
  const outDecimal = document.getElementById("out-decimal");
  const outStepA = document.getElementById("out-step-a");
  const outStepB = document.getElementById("out-step-b");
  const outStepResult = document.getElementById("out-step-result");

  const FORMAT_PLACEHOLDER = {
    decimal: "e.g. 3.14159, -2.5",
    hex: "e.g. 40490FDB",
  };

  form.querySelectorAll('input[name="op1_format"]').forEach(function (radio) {
    radio.addEventListener("change", function () {
      op1Input.placeholder = FORMAT_PLACEHOLDER[getSelectedFormat("op1_format")];
      op1Input.inputMode = getSelectedFormat("op1_format") === "hex" ? "text" : "decimal";
    });
  });
  form.querySelectorAll('input[name="op2_format"]').forEach(function (radio) {
    radio.addEventListener("change", function () {
      op2Input.placeholder = FORMAT_PLACEHOLDER[getSelectedFormat("op2_format")];
      op2Input.inputMode = getSelectedFormat("op2_format") === "hex" ? "text" : "decimal";
    });
  });

  function getSelectedFormat(name) {
    const checked = form.querySelector(`input[name="${name}"]:checked`);
    return checked ? checked.value : "decimal";
  }

  function getSelectedOperation() {
    const checked = form.querySelector('input[name="operation"]:checked');
    return checked ? checked.value : "add";
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    hideError();

    const operation = getSelectedOperation();
    const op1Value = op1Input.value.trim();
    const op2Value = op2Input.value.trim();

    if (!op1Value || !op2Value) {
      showError("Enter both operands first.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/arithmetic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operation,
          op1_value: op1Value,
          op1_format: getSelectedFormat("op1_format"),
          op2_value: op2Value,
          op2_format: getSelectedFormat("op2_format"),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        showError(data.error || "Something went wrong. Try different operands.");
        resultPanel.hidden = true;
        return;
      }

      renderResult(data);
    } catch (err) {
      showError("Could not reach the server. Check your connection and try again.");
      resultPanel.hidden = true;
    } finally {
      setLoading(false);
    }
  });

  function renderResult(data) {
    const symbol = data.operation === "multiply" ? "\u00d7" : "+";
    outEcho.textContent = `${data.operand_a.input} ${symbol} ${data.operand_b.input} = ${data.result.decimal}`;
    outSign.textContent = data.result.sign;
    outExponent.textContent = data.result.exponent;
    outMantissa.textContent = data.result.mantissa;
    outBinary.textContent = data.result.binary;
    outHex.textContent = data.result.hex;
    outDecimal.textContent = data.result.decimal;
    outStepA.textContent = `${data.operand_a.input} \u2192 ${data.operand_a.binary} (${data.operand_a.hex})`;
    outStepB.textContent = `${data.operand_b.input} \u2192 ${data.operand_b.binary} (${data.operand_b.hex})`;
    outStepResult.textContent = `${data.result.binary} (${data.result.hex})`;
    resultPanel.hidden = false;
  }

  function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
  }

  function hideError() {
    errorBox.hidden = true;
    errorBox.textContent = "";
  }

  function setLoading(isLoading) {
    const button = form.querySelector('button[type="submit"]');
    if (!button) return;
    button.disabled = isLoading;
    button.textContent = isLoading ? "Computing\u2026" : "Compute";
  }
}

})();
