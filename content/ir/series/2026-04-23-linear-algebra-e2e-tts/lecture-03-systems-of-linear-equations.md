---
difficulty: 3
id: systems-of-linear-equations.3
modality:
- text
- quiz
objective: Solve systems of linear equations using various methods; Understand the
  concept of matrix representation of systems
prerequisites: []
tags:
- generated
- autolecture
title: Systems of Linear Equations
---

# Lecture 3: Systems of Linear Equations

## Why Systems of Equations Matter (The Hook)

Why are we spending time studying systems of linear equations? In the real world—whether you are optimizing a business, designing an electrical circuit, or analyzing population growth—problems are rarely isolated. They are usually interconnected. Systems of linear equations provide the mathematical framework to model these interconnected relationships. Understanding how to solve these systems is not just an academic exercise; it is a fundamental skill for data science, engineering, economics, and virtually every quantitative field. We will learn how to translate complex word problems into solvable algebraic structures using the powerful tools of linear algebra.

## 1. Representing Systems as $Ax=b$

A system of linear equations is a set of equations where the variables are the unknowns we are trying to find. Linear algebra allows us to represent these systems compactly using matrices.

### The Matrix Formulation

Consider a general system of $m$ linear equations with $n$ variables:
$$
\begin{align*} a_{11}x_1 + a_{12}x_2 + \dots + a_{1n}x_n &= b_1 \\ a_{21}x_1 + a_{22}x_2 + \dots + a_{2n}x_n &= b_2 \\ &\vdots \\ a_{m1}x_1 + a_{m2}x_2 + \dots + a_{mn}x_n &= b_m \end{align*}
$$

We can represent this system in the compact matrix form:
$$\mathbf{Ax} = \mathbf{b}$$

Where:
*   **A** is the **coefficient matrix** ($m \times n$), containing the coefficients of the variables.
*   **x** is the **variable vector** ($n \times 1$), containing the unknowns ($x_1, x_2, \dots, x_n$).
*   **b** is the **constant vector** ($m \times 1$), containing the constants on the right-hand side of the equations.

**Intuition:** The matrix $\mathbf{A}$ captures the *relationships* (the coefficients), and the vectors $\mathbf{x}$ and $\mathbf{b}$ represent the *unknowns* and the *results*, respectively. Solving the system means finding the specific vector $\mathbf{x}$ that satisfies the relationship defined by $\mathbf{A}$ and $\mathbf{b}$.

## 2. Solving Systems using Gaussian Elimination

Since solving systems by substitution or elimination can become cumbersome for large systems, we use **Gaussian Elimination** to transform the system into an equivalent, much simpler form.

### The Augmented Matrix

To perform row operations efficiently, we combine the coefficient matrix $\mathbf{A}$ and the constant vector $\mathbf{b}$ into a single **augmented matrix**:
$$
\begin{bmatrix} a_{11} & a_{12} & \dots & a_{1n} & | & b_1 \\ a_{21} & a_{22} & \dots & a_{2n} & | & b_2 \\ \vdots & \vdots & \ddots & \vdots & | & \vdots \\ a_{m1} & a_{m2} & \dots & a_{mn} & | & b_m \end{bmatrix}
$$

### Gaussian Elimination and Row Echelon Form (REF)

Gaussian elimination is the process of using elementary row operations to transform the augmented matrix into **Row Echelon Form (REF)**. The allowed elementary row operations are:
1.  **Swapping** two rows.
2.  **Multiplying** a row by a non-zero scalar.
3.  **Adding** a multiple of one row to another row.

**Row Echelon Form (REF):** A matrix is in REF if:
1.  All non-zero rows are above any rows of all zeros.
2.  The leading non-zero entry (the **pivot**) in each row is strictly to the right of the pivot in the row above it.

By performing these operations, we systematically create zeros below the main diagonal, which reveals the structure of the solution.

### Back-Substitution

Once the augmented matrix is in REF, we can easily find the solution by using **back-substitution**. The system is now in a triangular form, making it straightforward to solve for the variables starting from the last equation and working backward.

## 3. Matrix Inverse and Solving Systems

If the coefficient matrix $\mathbf{A}$ is a **square matrix** ($n \times n$) and is **invertible** (meaning its determinant is non-zero), we can use the concept of the inverse matrix, $\mathbf{A}^{-1}$, to solve $\mathbf{Ax} = \mathbf{b}$.

### The Inverse Method

If $\mathbf{A}^{-1}$ exists, we can multiply both sides of the equation $\mathbf{Ax} = \mathbf{b}$ by $\mathbf{A}^{-1}$ from the left:
$$\mathbf{A}^{-1}(\mathbf{Ax}) = \mathbf{A}^{-1}\mathbf{b}$$
$$\mathbf{Ix} = \mathbf{A}^{-1}\mathbf{b}$$
$$\mathbf{x} = \mathbf{A}^{-1}\mathbf{b}$$

This method is powerful because it allows us to find the solution $\mathbf{x}$ directly by calculating the inverse of $\mathbf{A}$ and multiplying it by $\mathbf{b}$.

**Note on Practicality:** While mathematically elegant, for very large systems, Gaussian elimination (or related methods like LU decomposition) is often computationally more efficient than explicitly calculating the inverse $\mathbf{A}^{-1}$.

---

## Worked Example: Solving a System using Gaussian Elimination

Let's solve the following system of equations using Gaussian elimination.

**System:**
$$
\begin{align*} 2x + y - z &= 8 \\ -3x - y + 2z &= -11 \\ -2x + y + 2z &= -3 \end{align*}
$$

**Step 1: Form the Augmented Matrix**
$$
\begin{bmatrix} 2 & 1 & -1 & | & 8 \\ -3 & -1 & 2 & | & -11 \\ -2 & 1 & 2 & | & -3 \end{bmatrix}
$$

**Step 2: Achieve Row Echelon Form (REF)**

*Goal: Get a leading 1 in the first row.* (Swap $R_1$ and $R_3$ to get a smaller starting number.)
$$
\begin{bmatrix} -2 & 1 & 2 & | & -3 \\ -3 & -1 & 2 & | & -11 \\ 2 & 1 & -1 & | & 8 \end{bmatrix}
$$
*Operation: $R_1 \leftrightarrow R_3$*
$$
\begin{bmatrix} 2 & 1 & -1 & | & 8 \\ -3 & -1 & 2 & | & -11 \\ -2 & 1 & 2 & | & -3 \end{bmatrix}
$$

*Goal: Make the leading entry in $R_1$ equal to 1.* (Divide $R_1$ by 2.)
*Operation: $R_1 \leftarrow \frac{1}{2}R_1$*
$$
\begin{bmatrix} 1 & 1/2 & -1/2 & | & 4 \\ -3 & -1 & 2 & | & -11 \\ -2 & 1 & 2 & | & -3 \end{bmatrix}
$$

*Goal: Eliminate entries below the first pivot.*
*Operation: $R_2 \leftarrow R_2 + 3R_1$*
*Operation: $R_3 \leftarrow R_3 + 2R_1$*
$$
\begin{bmatrix} 1 & 1/2 & -1/2 & | & 4 \\ 0 & 1/2 & 1/2 & | & 1 \\ 0 & 2 & 1 & | & 5 \end{bmatrix}
$$

*Goal: Eliminate the entry below the second pivot.* (Multiply $R_2$ by 2 to clear the fraction, then use it to clear $R_3$.)
*Operation: $R_2 \leftarrow 2R_2$*
$$
\begin{bmatrix} 1 & 1/2 & -1/2 & | & 4 \\ 0 & 1 & 1 & | & 2 \\ 0 & 2 & 1 & | & 5 \end{bmatrix}
$$
*Operation: $R_3 \leftarrow R_3 - 2R_2$*
$$
\begin{bmatrix} 1 & 1/2 & -1/2 & | & 4 \\ 0 & 1 & 1 & | & 2 \\ 0 & 0 & -1 & | & 1 \end{bmatrix}
$$

**Step 3: Back-Substitution**

The matrix is now in Row Echelon Form. We convert it back to equations:
1. $x + \frac{1}{2}y - \frac{1}{2}z = 4$
2. $y + z = 2$
3. $-z = 1$

From Equation (3):
$$z = -1$$

Substitute $z=-1$ into Equation (2):
$$y + (-1) = 2 \implies y = 3$$

Substitute $y=3$ and $z=-1$ into Equation (1):
$$x + \frac{1}{2}(3) - \frac{1}{2}(-1) = 4$$
$$x + 1.5 + 0.5 = 4$$
$$x + 2 = 4 \implies x = 2$$

**Solution:** The system has a unique solution: $(x, y, z) = (2, 3, -1)$.

---

## Recap

*   **Matrix Representation:** A system of equations is represented as $\mathbf{Ax} = \mathbf{b}$, where $\mathbf{A}$ is the coefficient matrix, $\mathbf{x}$ is the variable vector, and $\mathbf{b}$ is the constant vector.
*   **Gaussian Elimination:** This is the systematic process of using elementary row operations on the **augmented matrix** to transform it into **Row Echelon Form (REF)**.
*   **Solving:** REF allows us to use **back-substitution** to find the unique solution for the variables.
*   **Inverse Method:** For square, invertible matrices, the solution can also be found via $\mathbf{x} = \mathbf{A}^{-1}\mathbf{b}$.

---

## Check Your Understanding

1.  What is the primary goal of performing Gaussian elimination on an augmented matrix?
2.  If a system of equations results in a row of zeros in the coefficient part of the augmented matrix (e.g., $[0 \ 0 \ 0 | c]$ where $c \neq 0$), what does this imply about the system's solutions?
3.  In the context of $\mathbf{Ax} = \mathbf{b}$, what condition must the matrix $\mathbf{A}$ satisfy for the inverse $\mathbf{A}^{-1}$ to exist?