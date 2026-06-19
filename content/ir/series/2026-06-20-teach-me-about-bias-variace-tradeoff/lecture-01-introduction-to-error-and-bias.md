---
difficulty: 3
id: introduction-to-error-and-bias.1
modality:
- text
- quiz
objective: Define bias and variance in the context of model error; Understand the
  relationship between training error, bias, and variance
prerequisites: []
tags:
- generated
- autolecture
title: Introduction to Error and Bias
---

# Lecture 1: Introduction to Error and Bias

## 🚀 Why Does This Matter? The Goal of Machine Learning

Welcome to the world of machine learning! Our goal is not just to build a model that looks good on our training data, but to build a model that accurately predicts outcomes on **new, unseen data**.

The central challenge in machine learning is understanding *why* a model makes errors. A model might have low error on the data it was trained on, but if it performs poorly on real-world data, it is useless. This lecture introduces the fundamental concepts—**Bias** and **Variance**—that explain this difference between fitting the training data and generalizing to the real world. Understanding this trade-off is the key to building robust and reliable predictive systems.

## 📐 Measuring Error: Mean Squared Error (MSE)

Before we dive into bias and variance, we need a way to quantify how wrong our model is. We use an error metric to measure the discrepancy between our predicted values and the actual observed values.

### Mean Squared Error (MSE)

The most common way to measure this error is using the **Mean Squared Error (MSE)**.

$$\text{MSE} = \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2$$

Where:
*   $y_i$ is the actual observed value.
*   $\hat{y}_i$ is the value predicted by our model.
*   $n$ is the total number of data points.

**Intuition:** MSE calculates the average squared difference between the true values and the predicted values. Squaring the errors penalizes large errors much more heavily than small errors, which encourages our model to avoid large mistakes.

## 🧠 Decomposing Error: Bias and Variance

The total error of a model can be decomposed into three main components: **Bias**, **Variance**, and **Irreducible Error**.

### 1. Bias

**Definition:** **Bias** refers to the error introduced by approximating a real-world problem (which may be complex) with a simplified model. It measures how much the model systematically misses the true relationship.

*   **High Bias:** Indicates **underfitting**. The model is too simple and cannot capture the underlying patterns in the data, leading to consistently large errors on both training and test sets.
*   **Intuition:** A high-bias model makes strong, simplifying assumptions about the data. It is *too rigid*.

### 2. Variance

**Definition:** **Variance** refers to the amount that the model's predictions change when trained on different subsets of the training data. It measures how sensitive the model is to the specific training set it sees.

*   **High Variance:** Indicates **overfitting**. The model has learned the noise and random fluctuations in the training data too well, causing it to perform excellently on the training set but poorly on unseen test data.
*   **Intuition:** A high-variance model is extremely sensitive to the specific examples it was trained on. It is *too flexible*.

### The Bias-Variance Tradeoff

The goal of machine learning is to find a balance:

$$\text{Total Error} \approx \text{Bias}^2 + \text{Variance} + \text{Irreducible Error}$$

We aim to minimize both bias and variance simultaneously. Reducing one often increases the other. We want a model that is complex enough to capture the signal (low bias) but not so complex that it memorizes the noise (low variance).

## 📝 Worked Example: Visualizing Bias vs. Variance

Imagine we are trying to fit a line to a set of data points.

**Scenario Setup:**
We train two models on our training data ($D_{\text{train}}$) and test them on unseen data ($D_{\text{test}}$).

1.  **Model A (High Bias / Underfitting):** We use a very simple straight line ($y = mx + b$) to fit the data.
    *   **Result:** The line misses most of the data points, both in training and testing.
    *   **Interpretation:** This model has **High Bias**. It is too simple to capture the true relationship.

2.  **Model B (High Variance / Overfitting):** We use a very complex, wiggly curve (a high-degree polynomial) to fit the data perfectly on $D_{\text{train}}$.
    *   **Result:** The line passes exactly through every training point but wildly misses the true trend in $D_{\text{test}}$.
    *   **Interpretation:** This model has **High Variance**. It has memorized the noise of the training set and fails to generalize.

3.  **Model C (Optimal Balance):** We use a moderately complex line that captures the general trend without fitting every single data point perfectly.
    *   **Result:** The line fits the overall pattern well on $D_{\text{train}}$ and generalizes effectively to $D_{\text{test}}$.
    *   **Interpretation:** This model achieves a good balance, minimizing both bias and variance.

## 📚 Recap

*   **MSE** is our primary tool for quantifying prediction error: $\text{MSE} = \frac{1}{n} \sum (y_i - \hat{y}_i)^2$.
*   **Bias** measures the systematic error from simplifying assumptions; high bias leads to **underfitting**.
*   **Variance** measures the sensitivity of the model to the training data; high variance leads to **overfitting**.
*   The goal is to find the sweet spot where both bias and variance are minimized—the **Bias-Variance Tradeoff**.

***

## ✅ Check Your Understanding

1. If a machine learning model has very low training error but very high test error, which problem (High Bias or High Variance) is it most likely suffering from?
2. Explain in your own words the difference between underfitting and overfitting using the concepts of bias and variance.
3. How does minimizing the Mean Squared Error help us in understanding the overall performance of a model?