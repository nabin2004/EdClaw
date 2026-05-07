---
id: lecture-2-introduction-to-matrices-and-systems-o.2
title: 'Lecture 2: Introduction to Matrices and Systems of Equations'
objective: Define matrices and understand their structure; Solve systems of linear
  equations using matrix methods
prerequisites: []
difficulty: 3
modality:
- text
- quiz
tags:
- generated
- autolecture
---

# Lecture 2: Introduction to Matrices and Systems of Equations

## 🚀 Why Matrices Matter: From Vectors to Computation

Welcome back! In our first lecture, we established the foundation of **vectors**—ordered lists of numbers that represent directions and magnitudes in space. Today, we transition from the abstract world of vectors to a powerful computational tool: **matrices**.

Why should we care about matrices? In science, engineering, computer graphics, and data analysis, we rarely deal with single vectors; we deal with *systems* of related vectors. Matrices provide the organized, compact language we use to represent these systems. They allow us to encode complex relationships and perform massive calculations efficiently. Think of matrices as the ultimate organizational tool for handling large sets of data and solving complex problems.

## 1. Defining Matrices and Their Structure

### What is a Matrix?

A **matrix** is a rectangular array of numbers, symbols, or expressions arranged in rows and columns.

*   **Structure:** A matrix is defined by its **dimensions**, or its size, which is given by the number of rows ($m$) and the number of columns ($n$).
*   **Notation:** We denote a matrix $A$ using capital letters. The element in the $i$-th row and $j$-th column is denoted by $a_{ij}$.

$$A = \begin{pmatrix} a_{11} & a_{12} & \cdots & a_{1n} \\ a_{21} & a_{22} & \cdots & a_{2n} \\ \vdots & \vdots & \ddots & \vdots \\ a_{m1} & a_{m2} & \cdots & a_{mn} \end{pmatrix}$$

*   **Order:** The matrix $A$ has **$m$ rows** and **$n$ columns**. We call this the dimension of the matrix, $m \times n$.

### Matrix Operations

We perform operations on matrices to manipulate the data they represent.

#### A. Matrix Addition and Subtraction
Matrices must have the **exact same dimensions** to be added or subtracted. The operation is performed element-wise.

If $A$ and $B$ are matrices of the same size ($m \times n$), then their sum $C = A + B$ is:
$$C_{ij} = a_{ij} + b_{ij}$$

#### B. Scalar Multiplication
Multiplying a matrix by a single number (a scalar, $c$) means multiplying every element in the matrix by that scalar.
If $A$ is an $m \times n$ matrix and $c$ is a scalar:
$$cA = c \cdot \begin{pmatrix} a_{11} & a_{12} \\ a_{21} & a_{22} \end{pmatrix} = \begin{pmatrix} c a_{11} & c a_{12} \\ c a_{21} & c a_{22} \end{pmatrix}$$

#### C. Matrix Multiplication
Matrix multiplication is the most complex operation. For two matrices $A$ (size $m \times p$) and $B$ (size $p \times n$) to be multiplied ($AB$), the number of **columns in $A$ must equal the number of rows in $B$** (the inner dimensions must match). The resulting matrix $C = AB$ will have the dimensions $m \times n$.

The element $c_{ij}$ is calculated by taking the dot product of the $i$-th row of $A$ and the $j$-th column of $B$.

## 2. Matrices as Representations of Linear Transformations

Matrices are not just arrays of numbers; they are the mechanism by which we represent **linear transformations**.

A linear transformation is a function that maps vectors from one space to another while preserving vector addition and scalar multiplication.

If we have a transformation $T$ that acts on a vector $\mathbf{x}$ to produce a vector $\mathbf{b}$ (i.e., $T(\mathbf{x}) = \mathbf{b}$), we can represent this transformation using a matrix $A$.

$$\mathbf{b} = T(\mathbf{x}) \quad \text{is represented by} \quad A\mathbf{x} = \mathbf{b}$$

In this equation:
*   $A$ is the **transformation matrix**.
*   $\mathbf{x}$ is the input vector.
*   $\mathbf{b}$ is the output vector.

Matrix multiplication ($A\mathbf{x}$) is the computational way of applying the transformation $A$ to the vector $\mathbf{x}$.

## 3. Solving Systems of Linear Equations

The practical application of matrices is solving systems of linear equations. A system of equations can be written in the compact matrix form:

$$\begin{align*} a_{11}x_1 + a_{12}x_2 + \cdots + a_{1n}x_n &= b_1 \\ a_{21}x_1 + a_{22}x_2 + \cdots + a_{2n}x_n &= b_2 \\ &\vdots \\ a_{m1}x_1 + a_{m2}x_2 + \cdots + a_{mn}x_n &= b_m \end{align*}$$

This system can be written in the matrix form:
$$\mathbf{A}\mathbf{x} = \mathbf{b}$$
where $\mathbf{A}$ is the coefficient matrix, $\mathbf{x}$ is the vector of unknowns, and $\mathbf{b}$ is the constant vector.

### Solving via Gaussian Elimination

To solve $\mathbf{A}\mathbf{x} = \mathbf{b}$, we use **Gaussian Elimination**, a systematic algorithm to transform the augmented matrix $[\mathbf{A} | \mathbf{b}]$ into an **Row Echelon Form (REF)**. This process uses elementary row operations to simplify the system until the solution becomes obvious.

**Elementary Row Operations:**
1.  **Row Swap:** Swapping the positions of two rows.
2.  **Row Scaling:** Multiplying a row by a non-zero scalar.
3.  **Row Addition:** Adding a multiple of one row to another row.

The goal of Gaussian Elimination is to create a staircase pattern (Row Echelon Form) where the leading non-zero entry (the **pivot**) in each row is 1, and all entries below the pivot are zero.

---

### Worked Example: Solving a System

Let's solve the following system of equations using Gaussian Elimination:
$$\begin{align*} 2x + y &= 8 \\ -3x + 4y &= 10 \end{align*}$$

**Step 1: Form the Augmented Matrix**
We write the coefficients and constants into an augmented matrix:
$$\begin{pmatrix} 2 & 1 & | & 8 \\ -3 & 4 & | & 10 \end{pmatrix}$$

**Step 2: Achieve Row Echelon Form**
Our goal is to get a zero below the first pivot (the 2 in the first row, first column). We use the operation $R_2 \rightarrow R_2 + \frac{3}{2}R_1$ to eliminate the $-3$.

$$R_2 \rightarrow R_2 + \frac{3}{2}R_1$$
$$\begin{pmatrix} 2 & 1 & | & 8 \\ -3 + \frac{3}{2}(2) & 4 + \frac{3}{2}(1) & | & 10 + \frac{3}{2}(8) \end{pmatrix}$$
$$\begin{pmatrix} 2 & 1 & | & 8 \\ 0 & 4.5 & | & 16 \end{pmatrix}$$

**Step 3: Back-Substitution**
The matrix is now in Row Echelon Form. We convert it back to equations:
$$\begin{align*} 2x + y &= 8 \quad \text{(Equation 1)} \\ 4.5y &= 16 \quad \text{(Equation 2)} \end{align*}$$

From Equation 2, solve for $y$:
$$y = \frac{16}{4.5} = \frac{32}{9}$$

Substitute $y$ back into Equation 1 to find $x$:
$$2x + \frac{32}{9} = 8$$
$$2x = 8 - \frac{32}{9} = \frac{72}{9} - \frac{32}{9} = \frac{40}{9}$$
$$x = \frac{40}{18} = \frac{20}{9}$$

The solution is $x = \frac{20}{9}$ and $y = \frac{32}{9}$.

## 📝 Recap

*   **Matrices** are rectangular arrays used to organize data and represent linear transformations.
*   Matrix operations include **addition, scalar multiplication, and matrix multiplication** (where inner dimensions must match).
*   A system of equations $\mathbf{A}\mathbf{x} = \mathbf{b}$ is the matrix representation of the system.
*   **Gaussian Elimination** is an algorithm that uses elementary row operations to transform the augmented matrix into **Row Echelon Form**, allowing us to easily solve for the variables through back-substitution.

---

## ✅ Check Your Understanding

1.  If matrix $A$ is $3 \times 2$ and matrix $B$ is $2 \times 3$, what is the dimension of the resulting matrix $AB$?
2.  What is the primary purpose of using Gaussian Elimination when solving a system of linear equations?
3.  Describe the difference between matrix addition and matrix multiplication in terms of the required dimensions.
