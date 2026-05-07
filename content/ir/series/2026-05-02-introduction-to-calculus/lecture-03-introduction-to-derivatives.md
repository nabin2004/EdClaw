---
difficulty: 3
id: introduction-to-derivatives.3
modality:
- text
- quiz
objective: Understand the geometric and physical meaning of the derivative; Learn
  the rules for differentiating basic functions
prerequisites: []
tags:
- generated
- autolecture
title: Introduction to Derivatives
---

# Introduction to Derivatives

## 🚀 Why Derivatives Matter: Measuring Change

Have you ever needed to know the exact speed of a car at a precise moment, or the exact rate at which a chemical reaction is changing? In the real world, we don't usually measure things at a single instant; we measure things over an interval.

The **derivative** is the mathematical tool that allows us to move beyond measuring *average* change to measuring **instantaneous change**. It is the foundation for understanding motion, optimization, rates of change, and the behavior of all dynamic systems in science and engineering.

**In this lecture, we will learn:**
1. The geometric and physical meaning of the derivative (slope and rate of change).
2. How to calculate the derivative using fundamental rules.

---

## 1. The Concept of the Derivative: Slope and Instantaneous Rate of Change

### The Slope Analogy

We already know how to find the slope of a straight line: $\text{slope} = \frac{\text{rise}}{\text{run}}$. The derivative extends this idea to curves.

*   **Average Rate of Change:** If we have two points, $(x_1, y_1)$ and $(x_2, y_2)$, the average rate of change between them is the slope of the line connecting them:
    $$\text{Average Rate of Change} = \frac{y_2 - y_1}{x_2 - x_1}$$
*   **Instantaneous Rate of Change:** The derivative answers the question: *What is the rate of change at a single, specific point?* Geometrically, this is the slope of the **tangent line** to the curve at that point.

### The Derivative as the Slope of the Tangent Line

The derivative of a function $f(x)$ at a point $x=a$, denoted as $f'(a)$, is the **slope of the tangent line** to the graph of $f(x)$ at the point $(a, f(a))$.

$$\text{Derivative} = f'(x) = \text{Slope of the Tangent Line at } x$$

### Physical Interpretation: Instantaneous Rate of Change

If $f(t)$ represents the position of an object at time $t$:
*   The **average rate of change** is the **average velocity** over an interval.
*   The **instantaneous rate of change** (the derivative) is the **instantaneous velocity**—the exact speed the object is traveling at that precise moment.

---

## 2. Differentiation Rules

Calculating the slope of a tangent line requires a formal process (using limits, which we will cover later). Fortunately, we have powerful shortcuts called **differentiation rules** that allow us to find these slopes quickly.

### A. The Power Rule

The Power Rule is the most fundamental rule for differentiating functions that are raised to a power.

**Rule:** If $f(x) = x^n$, then the derivative is:
$$f'(x) = n \cdot x^{n-1}$$

**Intuition:** You bring the exponent down as a multiplier, and then you subtract 1 from the original exponent.

### B. The Product Rule

When dealing with functions that are multiplied together, we need the Product Rule.

**Rule:** If $h(x) = f(x) \cdot g(x)$, then the derivative is:
$$h'(x) = f'(x)g(x) + f(x)g'(x)$$

**Mnemonic:** "First derivative of the first times the second, plus the first times the derivative of the second."

---

## 3. Worked Example: Applying the Rules

Let's find the derivative of the function $f(x) = 4x^3 - 5x + 2$.

**Goal:** Find $f'(x)$.

**Step 1: Apply the Sum/Difference Rule and the Power Rule to each term.**
The derivative of a sum is the sum of the derivatives:
$$f'(x) = \frac{d}{dx}(4x^3) - \frac{d}{dx}(5x) + \frac{d}{dx}(2)$$

**Term 1: $\frac{d}{dx}(4x^3)$**
Using the Power Rule ($n=3$):
$$4 \cdot (3x^{3-1}) = 12x^2$$

**Term 2: $\frac{d}{dx}(5x)$**
Remember that $x = x^1$. Using the Power Rule ($n=1$):
$$5 \cdot (1x^{1-1}) = 5x^0 = 5 \cdot 1 = 5$$

**Term 3: $\frac{d}{dx}(2)$**
The derivative of any constant is zero:
$$\frac{d}{dx}(2) = 0$$

**Step 2: Combine the results.**
$$f'(x) = 12x^2 - 5 + 0$$
$$f'(x) = 12x^2 - 5$$

**Conclusion:** The derivative of $f(x) = 4x^3 - 5x + 2$ is $f'(x) = 12x^2 - 5$. This new function, $f'(x)$, tells us the slope of the original function $f(x)$ at any point $x$.

---

## 📝 Recap

*   **The Derivative ($f'(x)$):** Represents the **instantaneous rate of change** of a function, which is geometrically the **slope of the tangent line** at that point.
*   **Power Rule:** For $f(x) = x^n$, the derivative is $f'(x) = n x^{n-1}$.
*   **Product Rule:** For $h(x) = f(x)g(x)$, the derivative is $h'(x) = f'(x)g(x) + f(x)g'(x)$.

---

## ✅ Check Your Understanding

1. If a function $f(x)$ is increasing at a certain point, what must be true about its derivative, $f'(x)$, at that point?
2. If you are calculating the rate of change of $y = x^5$ at $x=2$, what is the value of the derivative $f'(2)$?
3. Which rule would you use to find the derivative of $g(x) = (x^2)(x+1)$?