---
difficulty: 3
id: vectors-and-vector-spaces.1
modality:
- text
- quiz
objective: Understand the concept of vectors and vector spaces; Learn how to perform
  basic vector operations
prerequisites: []
tags:
- generated
- autolecture
title: Vectors and Vector Spaces
---

# Lecture 1: Vectors and Vector Spaces

## Why Study Vectors? (The Hook)

Welcome to Linear Algebra! In this course, we will move beyond simple arithmetic and explore the mathematics of change, direction, and space. Why? Because almost every field of science—physics, computer graphics, machine learning, and engineering—deals with data that exists in multi-dimensional spaces. **Vectors** are the fundamental language we use to describe these spaces. They allow us to represent physical quantities, directions, and transformations in a precise, algebraic way. Understanding vectors is the first step toward mastering the tools needed to analyze complex systems.

---

## 1. Vectors in $\mathbb{R}^n$

### Definition of a Vector

A **vector** is essentially an object that has both **magnitude** (size) and **direction**. Geometrically, we can visualize a vector as an arrow starting from the origin $(0, 0, \dots, 0)$ and ending at a specific point $(x_1, x_2, \dots, x_n)$ in $n$-dimensional space.

In the context of this course, we focus on vectors in $\mathbb{R}^n$, the $n$-dimensional Euclidean space.

### Coordinate Representation

We represent an $n$-dimensional vector $\mathbf{v}$ as an ordered list of $n$ components, called its **coordinates**:
$$\mathbf{v} = \begin{pmatrix} v_1 \\ v_2 \\ \vdots \\ v_n \end{pmatrix} \quad \text{or} \quad \mathbf{v} = (v_1, v_2, \dots, v_n)$$

The vector $\mathbf{v}$ is often written in **column vector** form in linear algebra, which simplifies matrix operations later on.

---

## 2. Vector Operations

We can perform algebraic operations on vectors, which correspond to intuitive geometric actions.

### Vector Addition

Vector addition is performed component-wise. If we have two vectors $\mathbf{u} = (u_1, u_2, \dots, u_n)$ and $\mathbf{v} = (v_1, v_2, \dots, v_n)$, their sum is:
$$\mathbf{u} + \mathbf{v} = (u_1 + v_1, u_2 + v_2, \dots, u_n + v_n)$$
**Intuition:** Adding two vectors means placing them head-to-tail to find the resultant vector.

### Scalar Multiplication

A **scalar** is a single real number (e.g., $c \in \mathbb{R}$). Scalar multiplication involves multiplying every component of the vector by that scalar:
$$c\mathbf{v} = (c v_1, c v_2, \dots, c v_n)$$
**Intuition:** Multiplying a vector by a scalar changes its length (magnitude). If $c > 1$, the vector gets longer; if $0 < c < 1$, it gets shorter; if $c < 0$, it points in the opposite direction.

### Linear Combinations

A **linear combination** is the most fundamental operation. It is the process of creating a new vector by taking a weighted sum of a set of existing vectors.
Given vectors $\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k$ and scalars $c_1, c_2, \dots, c_k$, the linear combination is:
$$c_1\mathbf{v}_1 + c_2\mathbf{v}_2 + \dots + c_k\mathbf{v}_k$$

---

## 3. Span, Basis, and Linear Independence

These concepts describe the structure formed by a set of vectors.

### Span

The **span** of a set of vectors $\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\}$, denoted $\text{Span}\{\mathbf{v}_1, \dots, \mathbf{v}_k\}$, is the set of *all possible linear combinations* of those vectors.
**Intuition:** The span is the entire space (line, plane, or higher-dimensional volume) that can be reached by moving from the origin using the vectors as directions.

### Basis

A **basis** for a vector space (or a subspace) is a set of vectors that satisfies two crucial conditions:
1. **Span the space:** The vectors must be able to generate every vector in that space.
2. **Linear Independence:** No vector in the set can be written as a linear combination of the others.

The **dimension** of a vector space is the number of vectors in any basis for that space.

---

## Worked Example: Span and Basis in $\mathbb{R}^3$

Let's examine the following set of vectors in $\mathbb{R}^3$:
$$\mathbf{v}_1 = \begin{pmatrix} 1 \\ 0 \\ 1 \end{pmatrix}, \quad \mathbf{v}_2 = \begin{pmatrix} 0 \\ 1 \\ 1 \end{pmatrix}, \quad \mathbf{v}_3 = \begin{pmatrix} 2 \\ 1 \\ 0 \end{pmatrix}$$

**Goal:** Determine the span and check if the set forms a basis for $\mathbb{R}^3$.

### Step 1: Check for Linear Independence

We check if the vectors are linearly independent by seeing if the only solution to $c_1\mathbf{v}_1 + c_2\mathbf{v}_2 + c_3\mathbf{v}_3 = \mathbf{0}$ is $c_1=c_2=c_3=0$. This leads to the system of equations:
$$c_1\begin{pmatrix} 1 \\ 0 \\ 1 \end{pmatrix} + c_2\begin{pmatrix} 0 \\ 1 \\ 1 \end{pmatrix} + c_3\begin{pmatrix} 2 \\ 1 \\ 0 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \\ 0 \end{pmatrix}$$

This gives the system:
1. $c_1 + 2c_3 = 0$
2. $c_2 + c_3 = 0$
3. $c_1 + c_2 = 0$

Solving this system (e.g., by substitution or row reduction) reveals that the only solution is $c_1=0, c_2=0, c_3=0$.
**Conclusion:** Since the only solution is the trivial one, the vectors $\{\mathbf{v}_1, \mathbf{v}_2, \mathbf{v}_3\}$ are **linearly independent**.

### Step 2: Determine the Span

Since we have three linearly independent vectors in $\mathbb{R}^3$ (a 3-dimensional space), they must span the entire space.
$$\text{Span}\{\mathbf{v}_1, \mathbf{v}_2, \mathbf{v}_3\} = \mathbb{R}^3$$

### Step 3: Identify the Basis

Since the set $\{\mathbf{v}_1, \mathbf{v}_2, \mathbf{v}_3\}$ is linearly independent and spans $\mathbb{R}^3$, it forms a **basis** for $\mathbb{R}^3$.
The **dimension** of this space is 3.

---

## Recap

*   **Vectors** are objects with magnitude and direction, represented by coordinates in $\mathbb{R}^n$.
*   **Vector Operations** involve component-wise addition and scalar multiplication.
*   **Linear Combinations** are weighted sums of vectors.
*   The **Span** is the set of all vectors that can be created by these combinations.
*   A **Basis** is a set of linearly independent vectors that span the entire space.

---

## Check Your Understanding

1.  If $\mathbf{u} = (1, 2)$ and $\mathbf{v} = (-1, 3)$, calculate the vector $\mathbf{w} = 3\mathbf{u} - 2\mathbf{v}$.
2.  Explain the geometric difference between the span of a single vector in $\mathbb{R}^2$ and the span of two linearly independent vectors in $\mathbb{R}^2$.
3.  What is the primary difference between a **spanning set** and a **basis**?