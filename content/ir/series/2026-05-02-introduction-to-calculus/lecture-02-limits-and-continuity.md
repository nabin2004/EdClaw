---
difficulty: 3
id: limits-and-continuity.2
modality:
- text
- quiz
objective: Master the formal definition of a limit; Analyze the concept of continuity
prerequisites: []
tags:
- generated
- autolecture
title: Limits and Continuity
---

# Lecture 2: Limits and Continuity

## 🚀 Why Limits Matter: Bridging the Gap to Calculus

Welcome to the world of Calculus! In our previous lectures, we focused on the foundations of functions and algebraic manipulation. Today, we introduce the single most important concept that allows us to study **motion, change, and accumulation**: **Limits**.

Why do we need limits? In algebra, we can easily plug in a value and find the output of a function. But what happens when we ask: "What value is the function *approaching* as the input gets infinitely close to a certain point, even if the function is undefined *at* that exact point?"

Limits allow us to analyze the **behavior** of a function near a point, giving us the mathematical tools to define the instantaneous rate of change (the derivative) and the area under a curve (the integral). Limits are the bedrock upon which all of calculus is built.

---

## 1. The Concept of a Limit

The concept of a limit describes the value that a function approaches as the input approaches a specific value. It is about the *trend* of the function, not necessarily the actual value *at* that point.

### 1.1 Intuitive Understanding

We write the limit as:
$$\lim_{x \to a} f(x) = L$$
This reads: "The limit of $f(x)$ as $x$ approaches $a$ is $L$."

*   **$x \to a$**: We are interested in what happens to the function $f(x)$ as $x$ gets arbitrarily close to the number $a$ (from both sides).
*   **$L$**: This is the specific output value that $f(x)$ gets closer and closer to.

### 1.2 One-Sided Limits

For a limit to exist at a point $a$, the function must approach the same value from both the left side and the right side. We define these separately:

1.  **The Left-Hand Limit:**
    $$\lim_{x \to a^-} f(x)$$
    This describes the value $f(x)$ approaches as $x$ approaches $a$ from values *less than* $a$ (the left side).

2.  **The Right-Hand Limit:**
    $$\lim_{x \to a^+} f(x)$$
    This describes the value $f(x)$ approaches as $x$ approaches $a$ from values *greater than* $a$ (the right side).

**The Formal Definition of a Two-Sided Limit:**
The two-sided limit $\lim_{x \to a} f(x)$ exists if and only if the left-hand limit equals the right-hand limit:
$$\lim_{x \to a} f(x) = L \quad \text{if and only if} \quad \lim_{x \to a^-} f(x) = \lim_{x \to a^+} f(x) = L$$

---

## 2. Continuity

While a limit describes the behavior *near* a point, **continuity** describes the behavior *at* that point. A function is continuous if there are no sudden jumps, holes, or breaks.

### 2.1 Definition of Continuity

A function $f(x)$ is **continuous** at a point $x=a$ if and only if three conditions are met:

1.  **The function must be defined at $a$:** $f(a)$ must exist (i.e., $a$ must be in the domain of $f$).
2.  **The limit must exist at $a$:** $\lim_{x \to a} f(x)$ must exist.
3.  **The limit must equal the function value:** The limit must equal the actual function value.
    $$\lim_{x \to a} f(x) = f(a)$$

If any one of these conditions fails, the function is **discontinuous** at $x=a$.

### 2.2 Types of Discontinuities

Discontinuities occur when the function fails the continuity test. We generally categorize them as:

*   **Removable Discontinuity:** The limit exists, but either $f(a)$ is undefined, or $f(a)$ exists but does not equal the limit. (This is a "hole" in the graph that can be fixed by redefining the function value.)
*   **Jump Discontinuity:** The left-hand limit and the right-hand limit both exist, but they are not equal. (The graph jumps from one value to another.)
*   **Infinite Discontinuity:** The function approaches $\infty$ or $-\infty$ at the point. (This corresponds to a vertical asymptote.)

---

## 3. Worked Example: Analyzing a Function

Let's analyze the function $f(x)$ at $x=2$.

$$f(x) = \begin{cases} x + 1 & \text{if } x < 2 \\ 5 & \text{if } x = 2 \\ x^2 - 1 & \text{if } x > 2 \end{cases}$$

We will check if $f(x)$ is continuous at $a=2$.

**Step 1: Check Condition 1 ($f(2)$ exists)**
$$f(2) = 5$$
(Condition 1 is met.)

**Step 2: Check Condition 2 (The limit exists)**
We must find the left-hand and right-hand limits.

*   **Left-Hand Limit ($x \to 2^-$):** We use the top rule ($x+1$).
    $$\lim_{x \to 2^-} f(x) = \lim_{x \to 2^-} (x + 1) = 2 + 1 = 3$$

*   **Right-Hand Limit ($x \to 2^+$):** We use the bottom rule ($x^2 - 1$).
    $$\lim_{x \to 2^+} f(x) = \lim_{x \to 2^+} (x^2 - 1) = 2^2 - 1 = 4 - 1 = 3$$

Since the left-hand limit equals the right-hand limit, the two-sided limit exists:
$$\lim_{x \to 2} f(x) = 3$$
(Condition 2 is met.)

**Step 3: Check Condition 3 (Limit equals function value)**
We compare the limit found in Step 2 with the actual function value from Step 1.
$$\lim_{x \to 2} f(x) = 3$$
$$f(2) = 5$$

Since $3 \neq 5$, the third condition fails.

**Conclusion:** The function $f(x)$ is **discontinuous** at $x=2$. Specifically, it has a **removable discontinuity** because the limit exists, but the function value is defined elsewhere.

---

## 📝 Recap

*   **Limit ($\lim_{x \to a} f(x)$):** Describes the value a function *approaches* as $x$ gets close to $a$.
*   **One-Sided Limits:** $\lim_{x \to a^-}$ (from the left) and $\lim_{x \to a^+}$ (from the right). A two-sided limit only exists if both one-sided limits are equal.
*   **Continuity:** A function is continuous at $x=a$ if $\lim_{x \to a} f(x) = f(a)$. It means the function has no breaks, jumps, or holes at that point.

---

## ✅ Check Your Understanding

1.  If $\lim_{x \to 5^-} f(x) = 10$ and $\lim_{x \to 5^+} f(x) = 10$, what can you conclude about $\lim_{x \to 5} f(x)$?
2.  What is the necessary condition for a function $f(x)$ to be continuous at a point $x=a$?
3.  In the context of the worked example, why was the function discontinuous at $x=2$?