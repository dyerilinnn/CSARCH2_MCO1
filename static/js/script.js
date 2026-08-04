/**
 * script.js — IEEE 754 Machine controller
 *
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
        valuePlaceholder: "e.g. 3.14159, -2.5, 10.1234",
        targetLabel: "Significant digits",
        targetHint: "Counted from the first nonzero digit — e.g. 10.1234 to 3 significant digits is 10.1.",
        targetUnit: "significant digit(s)",
      },
      binary: {
        valueLabel: "Binary number",
        valuePlaceholder: "e.g. 1.1011, -0.101, 1010",
        targetLabel: "Significant bits",
        targetHint: "Counted from the leading 1 — e.g. 1.1011 to 3 significant bits is 1.10.",
        targetUnit: "significant bit(s)",
      },
    };

    const targetHint = document.getElementById("target-hint");

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
      if (targetHint) targetHint.textContent = copy.targetHint;
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
      if (target === "" || Number(target) < 1 || !Number.isInteger(Number(target))) {
        showError("Target significant digits/bits must be a whole number of 1 or more.");
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

    const valueAInput = document.getElementById("value-a-input");
    const valueBInput = document.getElementById("value-b-input");

    const errorBox = document.getElementById("error-message");
    const resultPanel = document.getElementById("result-panel");
    const outEcho = document.getElementById("out-echo");
    const outSign = document.getElementById("out-sign");
    const outExponent = document.getElementById("out-exponent");
    const outMantissa = document.getElementById("out-mantissa");
    const outBinary = document.getElementById("out-binary");
    const outHex = document.getElementById("out-hex");
    const outDecimal = document.getElementById("out-decimal");
    const stepsList = document.getElementById("steps-list");

    const PLACEHOLDERS = {
      decimal: "e.g. 3.14159",
      hex: "e.g. 0x40490FDB",
    };

    form.querySelectorAll('input[name="format_a"]').forEach(function (radio) {
      radio.addEventListener("change", function () {
        valueAInput.placeholder = PLACEHOLDERS[getSelectedValue(form, "format_a")];
      });
    });
    form.querySelectorAll('input[name="format_b"]').forEach(function (radio) {
      radio.addEventListener("change", function () {
        valueBInput.placeholder = PLACEHOLDERS[getSelectedValue(form, "format_b")];
      });
    });

    function getSelectedValue(scope, name) {
      const checked = scope.querySelector(`input[name="${name}"]:checked`);
      return checked ? checked.value : "";
    }

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      hideError();

      const value_a = valueAInput.value.trim();
      const value_b = valueBInput.value.trim();
      const format_a = getSelectedValue(form, "format_a");
      const format_b = getSelectedValue(form, "format_b");
      const operation = getSelectedValue(form, "operation");

      if (!value_a || !value_b) {
        showError("Enter both operands first.");
        return;
      }

      setLoading(true);

      try {
        const response = await fetch("/api/arithmetic", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ value_a, format_a, value_b, format_b, operation }),
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
      const symbol = data.operation === "addition" ? "+" : "\u00d7";
      outEcho.textContent = `${data.operand_a.decimal} ${symbol} ${data.operand_b.decimal} = ${data.result.decimal}`;

      outSign.textContent = data.result.sign;
      outExponent.textContent = data.result.exponent_bits;
      outMantissa.textContent = data.result.mantissa_bits;
      outBinary.textContent = data.result.binary;
      outHex.textContent = data.result.hex;
      outDecimal.textContent = data.result.decimal;

      stepsList.innerHTML = "";
      data.steps.forEach(function (step) {
        const li = document.createElement("li");
        li.className = "step-item";

        const body = document.createElement("div");

        const title = document.createElement("p");
        title.className = "step-title";
        title.textContent = step.title;

        const detail = document.createElement("p");
        detail.className = "step-detail";
        detail.textContent = step.detail;

        body.appendChild(title);
        body.appendChild(detail);
        li.appendChild(body);
        stepsList.appendChild(li);
      });

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
      button.textContent = isLoading ? "Computing…" : "Compute";
    }
  }
})();
