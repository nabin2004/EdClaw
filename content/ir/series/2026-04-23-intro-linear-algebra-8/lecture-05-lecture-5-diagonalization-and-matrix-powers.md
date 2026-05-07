---
id: lecture-5-diagonalization-and-matrix-powers.5
title: 'Lecture 5: Diagonalization and Matrix Powers'
objective: Understand the process of diagonalizing a matrix; Use diagonalization to
  simplify matrix exponentiation
prerequisites: []
difficulty: 3
modality:
- text
- quiz
tags:
- generated
- autolecture
---

# Lecture 5: Diagonalization and Matrix Powers

## 🚀 Why Diagonalization Matters

Why spend time learning about **diagonalization**? In the previous lectures, we explored **eigenvalues** and **eigenvectors**, which revealed the fundamental, intrinsic behavior of a linear transformation represented by a matrix. Diagonalization is the process of exploiting this intrinsic structure.

Diagonalization allows us to simplify complex matrix operations—like calculating high powers or the matrix exponential—by transforming the matrix into a much simpler, diagonal form. It is the bridge that connects the abstract concepts of eigenvalues to concrete, powerful computational tools.

## 🧠 Core Concept 1: Diagonalization

**Diagonalization** is the process of finding an invertible matrix $P$ and a diagonal matrix $D$ such that a given square matrix $A$ can be written as:
$$A = PDP^{-1}$$

### Intuition: Change of Basis

Think of a matrix $A$ as a transformation that acts on vectors in the standard basis. If we change our coordinate system (the basis) to one where the transformation is simpler—specifically, one where the transformation only involves scaling along the new axes—the matrix representation becomes diagonal.

*   **$D$ (Diagonal Matrix):** Contains the **eigenvalues** of $A$ on its main diagonal. These eigenvalues represent the scaling factors along the new, specialized basis directions.
*   **$P$ (Change of Basis Matrix):** The columns of $P$ are the **eigenvectors** of $A$. $P$ transforms vectors from the specialized basis (the eigenvector basis) back to the standard basis.
*   **$P^{-1}$ (Inverse):** Transforms vectors from the standard basis to the eigenvector basis.

### The Process of Diagonalization

To diagonalize an $n \times n$ matrix $A$:

1.  **Find the Eigenvalues:** Calculate the eigenvalues ($\lambda_i$) of $A$. These will form the entries of the diagonal matrix $D$.
2.  **Find the Eigenvectors:** For each eigenvalue $\lambda_i$, find the corresponding linearly independent eigenvectors ($\mathbf{v}_i$).
3.  **Construct P and D:**
    *   The diagonal matrix $D$ is formed by placing the eigenvalues on the diagonal: $D = \begin{pmatrix} \lambda_1 & 0 & \dots \\ 0 & \lambda_2 & \dots \\ \vdots & \vdots & \ddots \end{pmatrix}$.
    *   The matrix $P$ is formed by using the corresponding eigenvectors as columns: $P = \begin{pmatrix} \mathbf{v}_1 & \mathbf{v}_2 & \dots \end{pmatrix}$.
4.  **Verify:** Ensure that $P$ is invertible (i.e., the eigenvectors form a basis for $\mathbb{R}^n$).

## 🔢 Core Concept 2: Simplifying Matrix Powers

Diagonalization dramatically simplifies calculating high powers of a matrix, $A^k$.

If $A = PDP^{-1}$, then calculating $A^k$ becomes much easier:
$$A^2 = (PDP^{-1})(PDP^{-1}) = PD(P^{-1}P)DP^{-1} = PDIDP^{-1} = PD^2P^{-1}$$
By induction, we find the general formula for powers:
$$\mathbf{A^k = PD^kP^{-1}}$$

Since $D$ is a diagonal matrix, calculating $D^k$ is trivial: you simply raise each diagonal entry to the power $k$:
$$D^k = \begin{pmatrix} \lambda_1^k & 0 & \dots \\ 0 & \lambda_2^k & \dots \\ \vdots & \vdots & \ddots \end{pmatrix}$$

This method avoids performing $k-1$ full matrix multiplications, which is computationally intensive and error-prone for large $k$.

## ⏱️ Core Concept 3: The Matrix Exponential

The **matrix exponential**, denoted $e^A$, is a function of a matrix defined by the power series:
$$e^A = \sum_{k=0}^{\infty} \frac{A^k}{k!} = I + A + \frac{A^2}{2!} + \frac{A^3}{3!} + \dots$$

Calculating this infinite sum directly is impractical. Diagonalization provides an elegant way to compute $e^A$.

If $A = PDP^{-1}$, then:
$$e^A = P e^D P^{-1}$$

Since $D$ is a diagonal matrix, $e^D$ is simply found by exponentiating each diagonal entry:
$$e^D = \begin{pmatrix} e^{\lambda_1} & 0 & \dots \\ 0 & e^{\lambda_2} & \dots \\ \vdots & \vdots & \ddots \end{pmatrix}$$

This transformation allows us to compute the matrix exponential by performing simple scalar exponentiation on the eigenvalues, which is vastly simpler than calculating the infinite series directly.

---

## 📝 Worked Example: Calculating $A^2$ using Diagonalization

Let's use a simple $2 \times 2$ matrix $A$ to demonstrate the power simplification.

$$A = \begin{pmatrix} 3 & 1 \\ 2 & 2 \end{pmatrix}$$

**Step 1: Find the Eigenvalues ($\lambda$)**
We solve the characteristic equation $\det(A - \lambda I) = 0$:
$$\det \begin{pmatrix} 3-\lambda & 1 \\ 2 & 2-\lambda \end{pmatrix} = (3-\lambda)(2-\lambda) - (1)(2) = 0$$
$$6 - 5\lambda + \lambda^2 - 2 = 0$$
$$\lambda^2 - 5\lambda + 4 = 0$$
$$(\lambda - 4)(\lambda - 1) = 0$$
The eigenvalues are $\lambda_1 = 4$ and $\lambda_2 = 1$.

**Step 2: Find the Eigenvectors ($\mathbf{v}$)**

*   **For $\lambda_1 = 4$:**
    $$(A - 4I)\mathbf{v}_1 = \begin{pmatrix} -1 & 1 \\ 2 & -2 \end{pmatrix} \begin{pmatrix} x \\ y \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix} \implies -x + y = 0.$$
    We choose $\mathbf{v}_1 = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$.

*   **For $\lambda_2 = 1$:**
    $$(A - 1I)\mathbf{v}_2 = \begin{pmatrix} 2 & 1 \\ 2 & 1 \end{pmatrix} \begin{pmatrix} x \\ y \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix} \implies 2x + y = 0.$$
    We choose $\mathbf{v}_2 = \begin{pmatrix} -1 \\ 2 \end{pmatrix}$.

**Step 3: Construct P and D**
$$D = \begin{pmatrix} 4 & 0 \\ 0 & 1 \end{pmatrix}, \quad P = \begin{pmatrix} 1 & -1 \\ 1 & 2 \end{pmatrix}$$

**Step 4: Find $P^{-1}$**
The inverse of $P$ is:
$$P^{-1} = \frac{1}{(1)(2) - (-1)(1)} \begin{pmatrix} 2 & 1 \\ -1 & 1 \end{pmatrix} = \frac{1}{3} \begin{pmatrix} 2 & 1 \\ -1 & 1 \end{pmatrix}$$

**Step 5: Calculate $A^2$ using Diagonalization**
We use the formula $A^2 = PD^2P^{-1}$. First, calculate $D^2$:
$$D^2 = \begin{pmatrix} 4^2 & 0 \\ 0 & 1^2 \end{pmatrix} = \begin{pmatrix} 16 & 0 \\ 0 & 1 \end{pmatrix}$$

Now, calculate $A^2$:
$$A^2 = \begin{pmatrix} 1 & -1 \\ 1 & 2 \end{pmatrix} \begin{pmatrix} 16 & 0 \\ 0 & 1 \end{pmatrix} \frac{1}{3} \begin{pmatrix} 2 & 1 \\ -1 & 1 \end{pmatrix}$$
$$A^2 = \frac{1}{3} \begin{pmatrix} 16 & -1 \\ 16 & 2 \end{pmatrix} \begin{pmatrix} 2 & 1 \\ -1 & 1 \end{pmatrix}$$
$$A^2 = \frac{1}{3} \begin{pmatrix} (32+1) & (16-1) \\ (32-2) & (16+2) \end{pmatrix} = \frac{1}{3} \begin{pmatrix} 33 & 15 \\ 30 & 18 \end{pmatrix} = \begin{pmatrix} 11 & 5 \\ 10 & 6 \end{pmatrix}$$

*(Self-Check: Direct calculation of $A^2$: $\begin{pmatrix} 3 & 1 \\ 2 & 2 \end{pmatrix} \begin{pmatrix} 3 & 1 \\ 2 & 2 \end{pmatrix} = \begin{pmatrix} 9+2 & 3+2 \\ 6+4 & 2+4 \end{pmatrix} = \begin{pmatrix} 11 & 5 \\ 10 & 6 \end{pmatrix}$. The result matches!)*

---

## 📚 Recap

*   **Diagonalization** is the process of finding $P$ and $D$ such that $A = PDP^{-1}$.
*   The matrix $D$ contains the **eigenvalues** of $A$ on the diagonal.
*   **Matrix Powers** are simplified by using the formula: $A^k = PD^kP^{-1}$, where $D^k$ is easy to compute.
*   The **Matrix Exponential** is simplified by using the formula: $e^A = P e^D P^{-1}$, where $e^D$ is computed by exponentiating the diagonal entries.

---

## ✅ Check Your Understanding

1.  If a matrix $A$ is diagonalizable, what must be true about the eigenvectors corresponding to the eigenvalues?
2.  Explain in simple terms why calculating $A^{100}$ using diagonalization is computationally superior to multiplying $A$ by itself 99 times.
3.  If $D$ is a diagonal matrix, how do you calculate the matrix $e^D$?
