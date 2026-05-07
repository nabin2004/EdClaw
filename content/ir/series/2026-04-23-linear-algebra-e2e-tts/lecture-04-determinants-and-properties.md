---
difficulty: 3
id: determinants-and-properties.4
modality:
- text
- quiz
objective: Calculate the determinant of square matrices; Understand the geometric
  interpretation of the determinant
prerequisites: []
tags:
- generated
- autolecture
title: Determinants and Properties
---

# Lecture 4: Determinants and Properties

## 🚀 Why Determinants Matter: The Geometric View

Welcome back. In our previous lectures, we focused on the algebraic structure of vectors and matrices. Today, we introduce a concept that bridges algebra and geometry: the **determinant**.

Why should we care about a single number derived from a matrix? The determinant is not just an abstract calculation; it represents a fundamental geometric property of the linear transformation represented by the matrix.

**The core idea is this:** If a matrix transforms space, the determinant tells us how that transformation scales the volume (or area in 2D) of that space. A determinant of zero tells us that the transformation collapses the space into a lower dimension (e.g., a 3D object collapses into a plane or a line).

## 📐 Core Concept 1: Defining the Determinant

The **determinant** is a scalar value that is uniquely associated with every square matrix. For an $n \times n$ matrix $A$, we denote it as $\det(A)$ or $|A|$.

### Calculating the Determinant (Cofactor Expansion)

We calculate the determinant using a recursive process based on **cofactor expansion**. This method breaks down the calculation of an $n \times n$ determinant into a series of $(n-1) \times (n-1)$ determinants.

For a $2 \times 2$ matrix:
$$A = \begin{pmatrix} a & b \\ c & d \end{pmatrix} \implies \det(A) = ad - bc$$

For a $3 \times 3$ matrix, we expand along a row or column. Let's expand along the first row:
$$\det(A) = a \cdot C_{11} + b \cdot C_{12} + c \cdot C_{13}$$
where $C_{ij}$ are the **cofactors**.

The **minor** $M_{ij}$ is the determinant of the submatrix formed by removing the $i$-th row and $j$-th column. The **cofactor** $C_{ij}$ is:
$$C_{ij} = (-1)^{i+j} M_{ij}$$

### Geometric Interpretation

The absolute value of the determinant, $|\det(A)|$, represents the **scaling factor** of the volume under the linear transformation defined by the matrix $A$.

*   **If $|\det(A)| > 1$**: The transformation stretches the volume.
*   **If $|\det(A)| < 1$**: The transformation shrinks the volume.
*   **If $\det(A) = 0$**: The transformation collapses the volume to zero (the space is flattened).

## 🌟 Core Concept 2: Properties of Determinants

Understanding the properties allows us to calculate determinants efficiently and understand matrix relationships without full expansion every time.

1.  **Determinant of a Transpose:** The determinant of a matrix is equal to the determinant of its transpose:
    $$\det(A) = \det(A^T)$$

2.  **Row/Column Swapping:** If you swap any two rows or two columns of a matrix, the determinant of the new matrix is the negative of the original determinant.
    $$\text{If } B \text{ is obtained from } A \text{ by swapping two rows, then } \det(B) = -\det(A)$$

3.  **Scalar Multiplication:** If you multiply a single row (or column) of a matrix by a scalar $k$, the determinant is multiplied by that same scalar $k$.
    $$\det(kA) = k^n \det(A)$$
    (Where $n$ is the dimension of the matrix.)

4.  **Determinant of a Product:** The determinant of a product of matrices is the product of their determinants:
    $$\det(AB) = \det(A) \cdot \det(B)$$

5.  **Determinant of the Inverse:** A crucial property for invertibility (covered next):
    $$\det(A^{-1}) = \frac{1}{\det(A)}$$

## 🔑 Core Concept 3: Matrix Invertibility

The determinant provides the definitive test for whether a matrix has an inverse.

**Theorem:** A square matrix $A$ is **invertible** (or non-singular) if and only if its determinant is non-zero.
$$\text{Matrix } A \text{ is invertible } \iff \det(A) \neq 0$$

If $\det(A) = 0$, the matrix is **singular** and has no inverse. Geometrically, this confirms our earlier intuition: if the determinant is zero, the transformation collapses the space, meaning information is lost, and there is no unique way to reverse the transformation.

---

## 📝 Worked Example: Calculating a $3 \times 3$ Determinant

Let's calculate the determinant of the following matrix $A$:
$$A = \begin{pmatrix} 1 & 2 & 3 \\ 0 & 1 & 4 \\ 2 & 0 & 1 \end{pmatrix}$$

We will use cofactor expansion along the first row:
$$\det(A) = 1 \cdot \det \begin{pmatrix} 1 & 4 \\ 0 & 1 \end{pmatrix} - 2 \cdot \det \begin{pmatrix} 0 & 4 \\ 2 & 1 \end{pmatrix} + 3 \cdot \det \begin{pmatrix} 0 & 1 \\ 2 & 0 \end{pmatrix}$$

**Step 1: Calculate the $2 \times 2$ determinants (the minors):**

1.  First term: $1 \cdot \det \begin{pmatrix} 1 & 4 \\ 0 & 1 \end{pmatrix} = 1 \cdot ((1)(1) - (4)(0)) = 1(1 - 0) = 1$
2.  Second term: $-2 \cdot \det \begin{pmatrix} 0 & 4 \\ 2 & 1 \end{pmatrix} = -2 \cdot ((0)(1) - (4)(2)) = -2(0 - 8) = -2(-8) = 16$
3.  Third term: $3 \cdot \det \begin{pmatrix} 0 & 1 \\ 2 & 0 \end{pmatrix} = 3 \cdot ((0)(0) - (1)(2)) = 3(0 - 2) = 3(-2) = -6$

**Step 2: Sum the results:**
$$\det(A) = 1 + 16 + (-6)$$
$$\det(A) = 11$$

Since $\det(A) = 11$, which is **not zero**, the matrix $A$ is **invertible**.

---

## 📚 Recap

*   The **determinant** ($\det(A)$) is a scalar value that measures the scaling factor of the volume under the linear transformation defined by matrix $A$.
*   It is calculated using **cofactor expansion**, which recursively breaks the problem down into $2 \times 2$ determinants.
*   **Properties** allow us to manipulate determinants efficiently (e.g., $\det(AB) = \det(A)\det(B)$).
*   The most critical application: A matrix $A$ is **invertible** if and only if $\det(A) \neq 0$.

---

## ✅ Check Your Understanding

1.  If a $3 \times 3$ matrix has a determinant of 0, what does this imply about the geometric transformation it represents?
2.  Explain the relationship between the determinant and matrix invertibility.
3.  If matrix $B$ is obtained from matrix $A$ by swapping two rows, how does $\det(B)$ relate to $\det(A)$?