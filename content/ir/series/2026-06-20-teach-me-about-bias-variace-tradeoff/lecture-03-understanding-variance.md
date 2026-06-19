---
difficulty: 3
id: understanding-variance.3
modality:
- text
- quiz
objective: Explain what high variance means for a model; Identify sources of high
  variance (overfitting)
prerequisites: []
tags:
- generated
- autolecture
title: Understanding Variance
---

# Lecture 3: Understanding Variance

## Hook: Why Does Model Performance Matter More Than Just Accuracy?

In our previous lectures, we established that the total error of a machine learning model can be decomposed into **Bias**, **Variance**, and **Irreducible Error**. We learned how **Bias** relates to underfitting (the model is too simple) and how it relates to systematic errors. Today, we tackle the second major component: **Variance**. Understanding variance is critical because it tells us *how sensitive* our model is to the specific training data we provide. A high-variance model might look perfect on the data it was trained on, but it will fail spectacularly when faced with new, unseen data.

## 1. Defining Variance in Machine Learning

**Variance** measures how much the predictions of a model vary when trained on different datasets drawn from the same underlying distribution. In simpler terms, variance quantifies the **sensitivity** of the model to the specific training examples it sees.

*   **Low Variance:** A model with low variance is stable. If we train it on slightly different subsets of the training data, the resulting predictions will be very similar. The model has learned the general patterns effectively.
*   **High Variance:** A model with high variance is unstable. Small changes in the training data lead to large changes in the model's predictions. This indicates that the model has essentially **memorized the noise and specific details** of the training set rather than learning the underlying, generalizable relationship.

## 2. Overfitting vs. Underfitting: The Context

Variance is intrinsically linked to the concepts of **overfitting** and **underfitting**.

### Underfitting (High Bias)
When a model has high bias, it is too simple to capture the complexity of the true relationship in the data. It performs poorly on both the training data and test data because it misses the fundamental patterns.

### Overfitting (High Variance)
When a model has high variance, it is too complex and flexible. It fits the training data *too* closely, including the random noise and idiosyncrasies specific to that dataset. While the performance on the **training set** will be extremely low (very low error), its performance on **unseen test data** will be significantly worse because it failed to generalize the true underlying concept.

**The Tradeoff:** We aim for a model that balances these two forces:
*   **High Bias + Low Variance:** Underfitting (Too simple, consistently wrong).
*   **Low Bias + High Variance:** Overfitting (Too complex, memorized noise).
*   **Low Bias + Low Variance:** The Ideal State (Good generalization).

## 3. Sources of High Variance: Model Complexity

The primary driver for high variance is **model complexity**. Models that are overly flexible can easily adapt to the training data, leading to high variance.

### Complex Models as Variance Magnifiers
Consider complex models like **Deep Decision Trees** or very deep Neural Networks. These models have many parameters (weights and nodes) that they can adjust based on the input data.

1.  **Flexibility:** A highly flexible model has enough parameters to perfectly map every single training point, including the random measurement errors (noise) present in that specific sample.
2.  **Memorization:** By assigning specific weights or splits to capture these noise points, the model becomes extremely sensitive to those exact points. If you slightly change the input data, the decision boundary can shift dramatically.

In essence, complex models have the *capacity* to fit the training data perfectly, and if they do so, they often **overfit** by latching onto the noise rather than the signal.

## 4. Worked Example: The Simple Decision Boundary

Imagine we are trying to classify points on a 2D plane using a simple decision boundary (a line).

**Scenario:** We have a set of training points that form a somewhat scattered, non-linear pattern.

1.  **Simple Model (Low Complexity):** If we use a simple straight line (low variance), the line must pass through the general center of the data. It will make some errors on individual points, but its overall prediction is stable across similar datasets.
2.  **Complex Model (High Complexity):** If we use a highly complex decision tree with many splits (high variance), the algorithm can create an extremely jagged, convoluted boundary that perfectly separates *every single training point*.
    *   **Training Performance:** The error on the training set is near zero.
    *   **Generalization Failure:** However, this jagged line is defined entirely by the specific locations of those training points. If we introduce a new data point slightly outside the original cluster, the complex boundary might flip wildly to accommodate that single outlier, leading to poor generalization. This instability is **high variance**.

## Recap

*   **Variance** measures how much a model's predictions change based on the specific training data it sees.
*   **High Variance** implies the model is overly sensitive and has **overfit** the training set by memorizing noise.
*   **Model Complexity** (e.g., deep trees) increases the potential for high variance because they have more parameters to fit the training data exactly.
*   The goal of tuning models is to find a sweet spot where bias and variance are balanced, leading to the best **generalization** capability.

***

## Check Your Understanding

1.  If a model has very low bias but very high variance, what is the most likely problem with that model when applied to new data?
2.  How does increasing the complexity of a machine learning model generally affect its variance?
3.  Explain in your own words the difference between **overfitting** and **underfitting** in terms of bias and variance.