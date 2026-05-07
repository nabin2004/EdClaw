---
id: lecture-3-linear-transformations-and-basis-vecto.3
title: 'Lecture 3: Linear Transformations and Basis Vectors'
objective: Understand the concept of a linear transformation; Identify and work with
  basis vectors
prerequisites: []
difficulty: 3
modality:
- text
- quiz
tags:
- generated
- autolecture
---

# Lecture 3: Linear Transformations and Basis Vectors

## 🚀 Hook: Why Study Transformations?

Imagine you are navigating a map. A **linear transformation** is the mathematical rule that dictates how every point on the map moves when you apply a specific operation (like stretching, rotating, or shearing). In linear algebra, we use these transformations to study the fundamental ways that vectors and spaces can be mapped onto themselves. Understanding transformations allows us to model complex physical systems, computer graphics, and data analysis.

Today, we will define what a linear transformation is, understand the building blocks of vector spaces (span and independence), and see how we can change our perspective on these transformations using **basis vectors**.

---

## 1. The Concept of a Linear Transformation

A **linear transformation** is a function between vector spaces that preserves the structure of vector addition and scalar multiplication. Intuitively, a linear transformation describes a geometric operation that involves only scaling, rotation, and shearing—no shifting or adding an offset.

### Definition of a Linear Transformation

A transformation $T$ from vector space $V$ to vector space $W$ is **linear** if, for any vectors $\mathbf{u}$ and $\mathbf{v}$ in $V$ and any scalars $c$:

1.  **Additivity:** $T(\mathbf{u} + \mathbf{v}) = T(\mathbf{u}) + T(\mathbf{v})$
2.  **Homogeneity (Scalar Multiplication):** $T(c\mathbf{u}) = cT(\mathbf{u})$

These two properties ensure that the transformation respects the underlying structure of the vector space.

### The Role of Matrices

Every linear transformation can be represented by a **matrix**. If $T: \mathbb{R}^n \to \mathbb{R}^m$ is a linear transformation, and we choose a standard basis for the domain and codomain, the transformation is represented by an $m \times n$ matrix $A$ such that:
$$T(\mathbf{x}) = A\mathbf{x}$$

---

## 2. Span, Linear Independence, and Basis

To understand what a transformation *does*, we must first understand the structure of the space we are working in. This involves understanding the concepts of **span** and **linear independence**.

### Span

The **span** of a set of vectors $\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\}$ is the set of all possible linear combinations of those vectors. It represents the entire space covered by those vectors.

$$\text{Span}\{\mathbf{v}_1, \dots, \mathbf{v}_k\} = \{c_1\mathbf{v}_1 + c_2\mathbf{v}_2 + \dots + c_k\mathbf{v}_k \mid c_i \in \mathbb{R}\}$$

### Linear Independence

A set of vectors $\{\mathbf{v}_1, \mathbf{v}_2, \dots, \mathbf{v}_k\}$ is **linearly independent** if the only way to write the zero vector as a linear combination of these vectors is by setting all the scalars to zero:
$$c_1\mathbf{v}_1 + c_2\mathbf{v}_2 + \dots + c_k\mathbf{v}_k = \mathbf{0} \implies c_1 = c_2 = \dots = c_k = 0$$

If there exists a non-trivial solution (where at least one $c_i$ is non-zero), the vectors are **linearly dependent**.

### Basis

A **basis** for a vector space $V$ is a set of vectors that satisfies two conditions:
1.  The set **spans** $V$ (every vector in $V$ can be written as a linear combination of the set).
2.  The set is **linearly independent** (no vector in the set is redundant).

The **dimension** of a vector space is the number of vectors in any basis for that space.

---

## 3. Linear Transformations and Basis Vectors

The concept of a basis is crucial because it allows us to simplify the description of a transformation.

### Action on Basis Vectors

If $\{\mathbf{b}_1, \mathbf{b}_2, \dots, \mathbf{b}_n\}$ is a basis for $\mathbb{R}^n$, any vector $\mathbf{x}$ in $\mathbb{R}^n$ can be written as a linear combination of the basis vectors:
$$\mathbf{x} = c_1\mathbf{b}_1 + c_2\mathbf{b}_2 + \dots + c_n\mathbf{b}_n$$

Because the transformation $T$ is linear, we can find the entire transformation by simply knowing where it maps the basis vectors:
$$T(\mathbf{x}) = T(c_1\mathbf{b}_1 + \dots + c_n\mathbf{b}_n) = c_1T(\mathbf{b}_1) + c_2T(\mathbf{b}_2) + \dots + c_nT(\mathbf{b}_n)$$

The images of the basis vectors, $\{T(\mathbf{b}_1), T(\mathbf{b}_2), \dots, T(\mathbf{b}_n)\}$, form the **image** of the transformation.

### Change of Basis

The **change of basis** allows us to switch from one coordinate system (one basis) to another. If we have a transformation $T$ represented by matrix $A$ with respect to basis $B$, and we want to find its representation $A'$ with respect to a new basis $B'$, we use the **change-of-basis matrix**.

If $P$ is the change-of-basis matrix from $B$ to $B'$, then the new representation $A'$ is found by:
$$A' = P^{-1} A P$$

This operation essentially transforms the matrix $A$ into the coordinates of the transformation relative to the new basis $B'$.

---

## 💡 Worked Example: Transformation in $\mathbb{R}^2$

Let $T$ be a linear transformation defined by the matrix $A = \begin{pmatrix} 2 & 1 \\ 1 & 3 \end{pmatrix}$. We will use the standard basis $B = \{\mathbf{e}_1, \mathbf{e}_2\}$ where $\mathbf{e}_1 = \begin{pmatrix} 1 \\ 0 \end{pmatrix}$ and $\mathbf{e}_2 = \begin{pmatrix} 0 \\ 1 \end{pmatrix}$.

**Step 1: Find the images of the basis vectors.**
We calculate $T(\mathbf{e}_1)$ and $T(\mathbf{e}_2)$ by multiplying $A$ by the basis vectors:
$$T(\mathbf{e}_1) = A\mathbf{e}_1 = \begin{pmatrix} 2 & 1 \\ 1 & 3 \end{pmatrix} \begin{pmatrix} 1 \\ 0 \end{pmatrix} = \begin{pmatrix} 2 \\ 1 \end{pmatrix}$$
$$T(\mathbf{e}_2) = A\mathbf{e}_2 = \begin{pmatrix} 2 & 1 \\ 1 & 3 \end{pmatrix} \begin{pmatrix} 0 \\ 1 \end{pmatrix} = \begin{pmatrix} 1 \\ 3 \end{pmatrix}$$

**Step 2: Determine the transformation.**
Since $T$ is linear, we can find $T(\mathbf{x})$ for any vector $\mathbf{x} = \begin{pmatrix} x_1 \\ x_2 \end{pmatrix}$ by using the linear combination property:
$$T(\mathbf{x}) = x_1 T(\mathbf{e}_1) + x_2 T(\mathbf{e}_2) = x_1 \begin{pmatrix} 2 \\ 1 \end{pmatrix} + x_2 \begin{pmatrix} 1 \\ 3 \end{pmatrix} = \begin{pmatrix} 2x_1 + x_2 \\ x_1 + 3x_2 \end{pmatrix}$$
Notice that this result is exactly $A\mathbf{x}$, confirming that the matrix $A$ represents the transformation $T$.

**Step 3: Conceptualizing Change of Basis.**
Suppose we change our basis $B$ to a new basis $B' = \{\mathbf{b}_1, \mathbf{b}_2\}$ where $\mathbf{b}_1 = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$ and $\mathbf{b}_2 = \begin{pmatrix} 0 \\ 1 \end{pmatrix}$. The change-of-basis matrix $P$ (from $B$ to $B'$) is formed by the new basis vectors: $P = \begin{pmatrix} 1 & 0 \\ 1 & 1 \end{pmatrix}$.

To find the transformation $T$ in the new basis $B'$, we use the formula: $A' = P^{-1} A P$.
First, find $P^{-1}$: $P^{-1} = \begin{pmatrix} 1 & 0 \\ -1 & 1 \end{pmatrix}$.
Then calculate $A' = \begin{pmatrix} 1 & 0 \\ -1 & 1 \end{pmatrix} \begin{pmatrix} 2 & 1 \\ 1 & 3 \end{pmatrix} \begin{pmatrix} 1 & 0 \\ 1 & 1 \end{pmatrix}$.
(Performing the multiplication yields $A' = \begin{pmatrix} 3 & 4 \\ 1 & 2 \end{pmatrix}$). This new matrix $A'$ represents the exact same geometric transformation $T$, but viewed through the lens of the new basis $B'$.

---

## 📚 Recap

*   **Linear Transformation:** A function that preserves vector addition and scalar multiplication, often represented by a matrix $A$ such that $T(\mathbf{x}) = A\mathbf{x}$.
*   **Basis:** A set of linearly independent vectors that span the entire space. The number of vectors in a basis is the **dimension** of the space.
*   **Span and Independence:** These concepts define the fundamental structure of the vector space.
*   **Change of Basis:** The process of finding the representation of a transformation matrix $A$ relative to a different basis $P$, using the formula $A' = P^{-1} A P$.

---

## ✅ Check Your Understanding

1.  Explain in your own words why the property of **linear independence** is essential when defining a **basis** for a vector space.
2.  If a transformation $T$ is linear, how can we determine the action of $T$ on *any* vector $\mathbf{x}$ if we only know the images of the basis vectors?
3.  Describe the conceptual purpose of the **change of basis** formula ($A' = P^{-1} A P$).
