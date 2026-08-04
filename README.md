# IEEE 754 Computing Machine

A web-based IEEE 754 Single-Precision Floating-Point simulator developed using **Python**, **Flask**, **HTML**, **CSS**, and **JavaScript**. The application demonstrates the fundamentals of IEEE 754 representation, rounding methods, and floating-point arithmetic operations.

---

## Deployed Website

https://csarch-2-mco-1.vercel.app/

---

## Video Walkthrough

> https://youtu.be/BVwc3lOkpKU

---

## Features

### Decimal to IEEE 754 Single-Precision Conversion
- Converts decimal numbers to IEEE 754 single-precision (32-bit) format.
- Displays:
  - Sign bit
  - Exponent
  - Mantissa
  - Binary representation
  - Hexadecimal representation

### Rounding Methods
Supports rounding of both **decimal** and **binary** values using:
- Truncate (Round toward Zero)
- Round Up (Ceiling)
- Round Down (Floor)
- Round to Nearest, Ties to Even (IEEE 754 Default)

### IEEE 754 Arithmetic Operations
Performs single-precision floating-point:
- Addition
- Multiplication

Supports operands entered in:
- Decimal
- Hexadecimal

Displays:
- Binary representation
- Hexadecimal representation
- Decimal result
- Step-by-step explanation of the operation

---

# Program Structure

```text
IEEE754-Machine/
│
├── app.py                     # Flask application and routes
│
├── converter.py               # IEEE 754 conversion module
├── rounding.py                # Rounding algorithms
├── arithmetic.py              # Arithmetic operations
│
├── templates/
│   ├── index.html
│   ├── convert.html
│   ├── rounding.html
│   └── arithmetic.html
│
├── static/
│   ├── css/
│   │     └── style.css
│   └── js/
│         └── script.js
│
└── requirements.txt
```

---

# Technologies Used

- Python
- Flask
- HTML5
- CSS3
- JavaScript
- IEEE 754 Single-Precision Floating-Point Standard

---

# Installation

### 1. Clone the repository

```bash
git clone https://github.com/<username>/<repository>.git
cd <repository>
```

### 2. Install the required packages

```bash
pip install -r requirements.txt
```

Alternatively,

```bash
pip install flask
```

### 3. Run the application

```bash
python app.py
```

### 4. Open the application

Visit:

```
http://127.0.0.1:5000/
```

---

# Sample Test Cases

## Decimal to IEEE 754 Conversion

**Input**

```
13.25
```

**Expected Output**

- Binary: `0 10000010 10101000000000000000000`
- Hex: `0x41540000`

---

## Rounding

**Input**

```
Value: 3.14159
Significant Digits: 4
```

| Rounding Mode | Expected Result |
|---------------|-----------------|
| Truncate | 3.141 |
| Round Up | 3.142 |
| Round Down | 3.141 |
| Ties to Even | 3.142 |

---

## Arithmetic

### Addition

```
5.5 + 2.25
```

Expected Result

```
7.75
```

---

### Multiplication

```
1.0 × 2.0
```

Expected Result

```
2.0
```

---

# Authors

- De Gracia, Kaleela Ysabel
- Gerylyn Guiller

---

## License

This project was developed as a course requirement for **CSARCH2 – Computer Architecture**.
