---
id: lecture-1-foundations-of-vector-spaces.1
title: 'Lecture 1: Foundations of Vector Spaces'
objective: Understand the concept of vectors and vector spaces; Differentiate between
  vector and scalar quantities
prerequisites: []
difficulty: 3
modality:
- text
- quiz
tags:
- generated
- autolecture
---

# Lecture 1: Foundations of Vector Spaces

## Why This Matters: The Language of Change and Space

Welcome to Linear Algebra! This course is not just about crunching numbers; it is about learning the fundamental language used to describe change, motion, and structure in almost every field of science and engineering—from physics and computer graphics to machine learning and economics.

The core idea we explore today is how we can represent complex information using simple, organized mathematical objects. We will learn how to move, combine, and analyze these representations, giving us the tools to solve problems that involve multiple interacting variables.

## 1. Vectors and Scalars: The Fundamental Distinction

Before diving into vector spaces, we must establish the difference between the two fundamental types of quantities we will be working with: **scalars** and **vectors**.

### Scalars
A **scalar** is a single numerical value that represents a magnitude or amount.
*   **Intuition:** Scalars describe "how much."
*   **Examples:** Temperature ($25^\circ\text{C}$), time (5 seconds), mass (10 kg), or a single number (3.14).
*   **Mathematical Representation:** Scalars are real numbers ($\mathbb{R}$).

### Vectors
A **vector** is an object that has both **magnitude** (size) and **direction**.
*   **Intuition:** Vectors describe "how much" *and* "in what direction."
*   **Examples:** Displacement (5 meters East), velocity (60 mph North), or a force applied to an object.
*   **Mathematical Representation:** Vectors are ordered lists of numbers, often represented as columns or rows. In $\mathbb{R}^2$ or $\mathbb{R}^3$, a vector is an ordered pair or triple, respectively.

## 2. Vectors in $\mathbb{R}^n$

We typically work with vectors in **Euclidean space**, denoted as $\mathbb{R}^n$.

### Definition of a Vector in $\mathbb{R}^n$
A vector in $\mathbb{R}^n$ is an ordered list of $n$ real numbers, often written as a column matrix:
$$\mathbf{v} = \begin{pmatrix} v_1 \\ v_2 \\ \vdots \\ v_n \end{pmatrix}$$
The number $n$ is the **dimension** of the space. For example, vectors in $\mathbb{R}^2$ are points $(x, y)$, and vectors in $\mathbb{R}^3$ are points $(x, y, z)$.

### Vector Operations

We define how we combine and scale these vectors.

#### A. Vector Addition
Vector addition is performed component-wise. If we have two vectors $\mathbf{u} = \begin{pmatrix} u_1 \\ u_2 \end{pmatrix}$ and $\mathbf{v} = \begin{pmatrix} v_1 \\ v_2 \end{pmatrix}$ in $\mathbb{R}^2$, their sum is:
$$\mathbf{u} + \mathbf{v} = \begin{pmatrix} u_1 + v_1 \\ u_2 + v_2 \end{pmatrix}$$
**Intuition:** Geometrically, vector addition corresponds to placing the vectors head-to-tail. This is often visualized using the **parallelogram rule**.

#### B. Scalar Multiplication
Scalar multiplication involves multiplying every component of the vector by a single scalar $c$. If $\mathbf{v} = \begin{pmatrix} v_1 \\ v_2 \end{pmatrix}$ and $c$ is a scalar:
$$c\mathbf{v} = c \begin{pmatrix} v_1 \\ v_2 \end{pmatrix} = \begin{pmatrix} c v_1 \\ c v_2 \end{pmatrix}$$
**Intuition:** Scalar multiplication changes the **magnitude** of the vector. If $c > 1$, the vector is stretched; if $0 < c < 1$, it is shrunk; if $c < 0$, the direction is reversed.

### Linear Combinations
A **linear combination** is the most powerful concept introduced in this section. It describes how one vector can be constructed by scaling and adding other vectors.

Given a set of vectors $\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\}$ and scalars $\{c_1, c_2, \dots, c_k\}$, a linear combination of these vectors is:
$$\mathbf{w} = c_1\mathbf{v}_1 + c_2\mathbf{v}_2 + \dots + c_k\mathbf{v}_k$$
**Intuition:** This operation shows that any vector lying within the span of a set of vectors can be expressed as a combination of those vectors.

---

## Worked Example: Vector Operations in $\mathbb{R}^3$

Let's work with vectors in three-dimensional space ($\mathbb{R}^3$).

Consider the following vectors:
$$\mathbf{a} = \begin{pmatrix} 1 \\ 2 \\ -1 \end{pmatrix} \quad \text{and} \quad \mathbf{b} = \begin{pmatrix} 3 \\ -1 \\ 4 \end{pmatrix}$$
And let the scalar be $c = 2$.

### Step 1: Vector Addition
Calculate the sum $\mathbf{a} + \mathbf{b}$:
$$\mathbf{a} + \mathbf{b} = \begin{pmatrix} 1 \\ 2 \\ -1 \end{pmatrix} + \begin{pmatrix} 3 \\ -1 \\ 4 \end{pmatrix} = \begin{pmatrix} 1+3 \\ 2+(-1) \\ -1+4 \end{pmatrix} = \begin{pmatrix} 4 \\ 1 \\ 3 \end{pmatrix}$$

### Step 2: Scalar Multiplication
Calculate the scalar multiple $2\mathbf{a}$:
$$2\mathbf{a} = 2 \begin{pmatrix} 1 \\ 2 \\ -1 \end{pmatrix} = \begin{pmatrix} 2 \times 1 \\ 2 \times 2 \\ 2 \times (-1) \end{pmatrix} = \begin{pmatrix} 2 \\ 4 \\ -2 \end{pmatrix}$$

### Step 3: Linear Combination
Find a vector $\mathbf{w}$ that is a linear combination of $\mathbf{a}$ and $\mathbf{b}$ using scalars $c_1 = 1$ and $c_2 = 3$:
$$\mathbf{w} = 1\mathbf{a} + 3\mathbf{b}$$
$$\mathbf{w} = 1 \begin{pmatrix} 1 \\ 2 \\ -1 \end{pmatrix} + 3 \begin{pmatrix} 3 \\ -1 \\ 4 \end{pmatrix}$$
$$\mathbf{w} = \begin{pmatrix} 1 \\ 2 \\ -1 \end{pmatrix} + \begin{pmatrix} 9 \\ -3 \\ 12 \end{pmatrix} = \begin{pmatrix} 10 \\ -1 \\ 11 \end{pmatrix}$$
Thus, $\mathbf{w} = \begin{pmatrix} 10 \\ -1 \\ 11 \end{pmatrix}$.

---

## Recap

*   **Scalars** are single numbers representing magnitude (e.g., mass, time).
*   **Vectors** are ordered lists of numbers representing magnitude and direction (e.g., position, velocity).
*   **Vector Addition** is component-wise addition, geometrically representing the combination of directions.
*   **Scalar Multiplication** scales the vector, changing its length.
*   **Linear Combination** is the process of building a new vector by scaling and adding a set of existing vectors.

## Check Your Understanding

1.  If you are describing the force exerted on an object, is that quantity a scalar or a vector? Explain your reasoning.
2.  If $\mathbf{v} = \begin{pmatrix} 4 \\ -2 \end{pmatrix}$, what is the result of multiplying $\mathbf{v}$ by the scalar $c = -3$?
3.  What does the term "span" mean in the context of linear combinations?
