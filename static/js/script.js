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
})();
