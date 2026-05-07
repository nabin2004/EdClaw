---
difficulty: 3
id: foundations-of-calculus.1
modality:
- text
- quiz
objective: Understand the basic concepts of change and motion; Introduce the concept
  of limits
prerequisites: []
tags:
- generated
- autolecture
title: Foundations of Calculus
---

# Foundations of Calculus

## Why Calculus Matters: Understanding Change

Have you ever wondered how fast a car is going at the exact moment you pass a specific mile marker? Or how quickly the temperature of a room is changing as you walk into it? These questions deal with **change** and **motion**.

Calculus is the mathematical tool designed to precisely measure and analyze these kinds of continuous changes. It allows us to move beyond calculating simple averages and determine the exact rate of change at any single point in time. Without calculus, we can describe motion generally, but we cannot calculate the instantaneous speed or acceleration.

This lecture introduces the two foundational pillars of calculus: **rates of change** and the concept of **limits**.

## Part 1: Introduction to Rates of Change

A **rate of change** measures how one quantity changes in relation to another. The most common example is **speed** (distance over time).

### Average Rate of Change

When we look at motion over an interval, we can easily calculate the **average rate of change**.

Let $x$ represent time ($t$) and $y$ represent distance ($d$). The average rate of change between two points $(x_1, y_1)$ and $(x_2, y_2)$ is the slope of the line connecting those two points, often called the **average rate of change**:

$$\text{Average Rate of Change} = \frac{\text{Change in } y}{\text{Change in } x} = \frac{y_2 - y_1}{x_2 - x_1}$$

In the context of motion, this is the **average velocity**:
$$\text{Average Velocity} = \frac{\text{Change in Position}}{\text{Change in Time}}$$

This tells us the overall speed maintained over the entire trip.

### The Need for Instantaneous Change

The average rate of change is useful, but it doesn't tell us what was happening at a single instant. If you drive 100 miles in 2 hours, your average speed was 50 mph. But were you traveling at exactly 50 mph the entire time? Perhaps you sped up and slowed down.

We need a way to find the rate of change at a **single, specific point**—the **instantaneous rate of change**. This is the speed you are traveling at the exact moment you look at your speedometer.

## Part 2: Intuitive Understanding of Limits

To move from the **average rate of change** to the **instantaneous rate of change**, we use the concept of a **limit**.

### What is a Limit?

A **limit** describes the value that a function or sequence *approaches* as the input or index approaches some value. It is a way of describing the behavior of a function near a certain point, even if the function is undefined *at* that point.

We write the concept as:
$$\lim_{x \to a} f(x) = L$$
This is read as: "The limit of $f(x)$ as $x$ approaches $a$ is $L$."

**Intuitive Explanation:**
Imagine you are walking along a path defined by a function $f(x)$. If you want to know the height of the path exactly at $x=5$, you can't just plug $x=5$ into the equation if the equation is undefined there.

Instead, you can look at the points immediately to the left of 5 (e.g., 4.9, 4.99, 4.999) and the points immediately to the right of 5 (e.g., 5.1, 5.01, 5.001). As you get closer and closer to $x=5$ from both sides, the corresponding $y$-values get closer and closer to a single, specific value. The limit is that specific value the function is "trying" to reach.

### Connecting Limits to Rates of Change

The instantaneous rate of change (the slope of the tangent line at a point) is defined as the limit of the average rate of change as the interval shrinks to zero.

If we take two points, $x$ and $x+h$, the average rate of change (the slope of the secant line) is:
$$\text{Average Rate} = \frac{f(x+h) - f(x)}{(x+h) - x} = \frac{f(x+h) - f(x)}{h}$$

To find the **instantaneous rate of change** at $x$, we let the distance $h$ approach zero. This process defines the limit:

$$\text{Instantaneous Rate of Change} = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$$

This resulting expression is the formal definition of the **derivative**, which is the core concept of differential calculus.

## Worked Example: Finding the Instantaneous Rate of Change

Let's use a simple function to see how the limit concept works. Suppose the position of an object is given by the function:
$$s(t) = t^2$$
We want to find the **instantaneous velocity** (rate of change) at $t=3$ seconds.

**Step 1: Find the Average Rate of Change over an interval.**
Let's calculate the average velocity between $t=3$ and $t=3.1$.
$$s(3) = 3^2 = 9$$
$$s(3.1) = (3.1)^2 = 9.61$$
$$\text{Average Velocity} = \frac{s(3.1) - s(3)}{3.1 - 3} = \frac{9.61 - 9}{0.1} = \frac{0.61}{0.1} = 6.1 \text{ units/second}$$

**Step 2: Apply the Limit to find the Instantaneous Rate of Change.**
To find the exact velocity at $t=3$, we use the limit definition, letting the time interval $h$ approach zero:
$$\text{Instantaneous Velocity} = \lim_{h \to 0} \frac{s(3+h) - s(3)}{h}$$

Substitute the function $s(t) = t^2$:
$$\text{Instantaneous Velocity} = \lim_{h \to 0} \frac{(3+h)^2 - 3^2}{h}$$

Expand the numerator:
$$\text{Instantaneous Velocity} = \lim_{h \to 0} \frac{(9 + 6h + h^2) - 9}{h}$$

Simplify:
$$\text{Instantaneous Velocity} = \lim_{h \to 0} \frac{6h + h^2}{h}$$

Factor out $h$ from the numerator and cancel:
$$\text{Instantaneous Velocity} = \lim_{h \to 0} \frac{h(6 + h)}{h} = \lim_{h \to 0} (6 + h)$$

Now, apply the limit by substituting $h=0$:
$$\text{Instantaneous Velocity} = 6 + 0 = 6$$

**Conclusion:** The instantaneous velocity of the object at $t=3$ seconds is **6 units/second**.

## Recap

*   **Rates of Change:** Measure how one quantity changes relative to another (e.g., speed, slope).
*   **Average Rate of Change:** Calculated over an interval: $\frac{f(b) - f(a)}{b - a}$.
*   **Limits:** Describe the value a function approaches as its input approaches a certain value.
*   **Instantaneous Rate of Change:** Found by taking the limit of the average rate of change as the interval shrinks to zero. This process forms the basis of the **derivative**.

***

## Check Your Understanding

1.  Explain in your own words the difference between the **average rate of change** and the **instantaneous rate of change**.
2.  If a function is defined by $f(x) = x^2$, what does the expression $\lim_{h \to 0} \frac{(x+h)^2 - x^2}{h}$ represent geometrically?
3.  Why is the concept of a **limit** necessary to define the instantaneous rate of change?