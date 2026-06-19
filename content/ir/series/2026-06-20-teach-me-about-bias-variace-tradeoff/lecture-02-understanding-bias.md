---
difficulty: 3
id: understanding-bias.2
modality:
- text
- quiz
objective: Explain what high bias means for a model; Identify sources of high bias
  (underfitting)
prerequisites: []
tags:
- generated
- autolecture
title: Understanding Bias
---

# Lecture 2: Understanding Bias

## Why Understanding Bias Matters

In machine learning, our goal is to build a model that accurately reflects the true relationship between the input data and the target outcome. However, simply achieving low error isn't enough; we need to understand *why* the error occurs. This lecture introduces the concept of **Bias**, which is one of the two fundamental components (along with Variance) that determine how well a model generalizes to new, unseen data. Understanding bias allows us to diagnose whether our model is too simple or too complex for the task at hand.

## The Spectrum of Model Performance: Underfitting vs. Overfitting

To understand bias, we must first place it in context by comparing it to **Variance**. These two concepts define the fundamental trade-off we will explore later.

*   **Underfitting:** This occurs when a model is **too simple** and fails to capture the underlying patterns in the training data. A model that underfits has high error on *both* the training set and the test set because it hasn't learned enough from the data.
*   **Overfitting:** This occurs when a model is **too complex** and learns the noise and random fluctuations specific to the training data, performing exceptionally well on the training set but poorly on new, unseen data.

The relationship between these concepts is crucial:
*   **High Bias** $\rightarrow$ Underfitting (Model is too simple)
*   **High Variance** $\rightarrow$ Overfitting (Model is too complex/sensitive to training noise)

## Defining High Bias

**Bias** refers to the error introduced by approximating a real-world problem (which may be complex) with a simplified model. In essence, bias measures how much the model's predictions systematically miss the true values.

### Intuition: The Simplification Penalty

Imagine you are trying to draw a complex, winding coastline on a piece of paper using only straight lines. No matter how many straight lines you use, they will inevitably smooth out the curves and miss the fine details.

*   **High Bias:** A model with high bias makes strong, simplifying assumptions about the relationship between variables. It forces the data into a simple structure that ignores important, subtle relationships present in the true data.
*   **The Cost of Simplicity:** High bias means the model is **underfitting**. It has failed to capture the complexity of the data because its structure is too constrained.

### Simple Models and High Bias

Simple models, such as **Linear Regression**, are inherently prone to high bias when applied to complex, non-linear relationships.

*   **Linear Regression Example:** A linear model assumes a perfectly straight-line relationship ($y = mx + b$). If the true relationship between $X$ and $Y$ is highly curved (e.g., parabolic or exponential), forcing the data into a straight line introduces a systematic error—this systematic error is **high bias**. The model is biased toward the simplest possible fit, even if that fit is fundamentally inaccurate to the reality of the data.

## Worked Example: High Bias in Simple Regression

Consider a scenario where we are trying to predict house prices based on square footage ($X$). We know from domain knowledge that the relationship between size and price is highly non-linear (it curves sharply at certain thresholds).

**Scenario:** We train a **Simple Linear Regression Model** on this complex, curved data.

1.  **The True Relationship (Hypothetical):** The true relationship is $Y = 0.5X^2 + 100$ (a parabola).
2.  **The Model Applied:** We fit the simplest possible model: $\hat{Y} = mX + b$.
3.  **The Result:** Because the linear model cannot capture the curvature of the true relationship, it will consistently underestimate or overestimate prices across the entire range of square footage.
4.  **Diagnosis:** The resulting error (the difference between the predicted line and the actual curved data points) is systematic. This systematic deviation demonstrates **high bias**. The model is too constrained by its simple linear form to accurately represent the true, complex relationship.

To reduce this high bias, we would need to move away from the simple linear assumption and use a more flexible model (e.g., Polynomial Regression or a Neural Network) that has the capacity to bend and fit the curve of the data.

## Recap

*   **Bias** measures the error introduced by making strong, simplifying assumptions about the data.
*   **High Bias** means the model is **underfitting**; it is too simple to capture the true complexity of the underlying relationship.
*   Simple models (like basic Linear Regression) often suffer from high bias when applied to complex, non-linear datasets because they cannot bend to fit the true pattern.

***

## Check Your Understanding

1.  If a machine learning model performs very well on the training data but poorly on the test data, which component—Bias or Variance—is most likely the primary issue?
2.  Explain in your own words why a model with high bias is considered underfitting.
3.  How might increasing the complexity of a model (e.g., moving from Linear Regression to a Decision Tree) help reduce high bias?