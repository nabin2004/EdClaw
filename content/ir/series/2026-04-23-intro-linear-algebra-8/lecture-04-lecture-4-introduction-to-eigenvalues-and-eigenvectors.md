---
id: lecture-4-introduction-to-eigenvalues-and-eigenv.4
title: 'Lecture 4: Introduction to Eigenvalues and Eigenvectors'
objective: Define the concept of eigenvalues and eigenvectors; Calculate the eigenvalues
  and eigenvectors of a given matrix
prerequisites: []
difficulty: 3
modality:
- text
- quiz
tags:
- generated
- autolecture
---

# Lecture 4: Introduction to Eigenvalues and Eigenvectors

## 🚀 Why Study Eigenvalues and Eigenvectors? (The Hook)

In the previous lectures, we studied how matrices transform vectors—they rotate, stretch, and shear them. But what if we found a special set of vectors that are *not* rotated by the transformation, only scaled?

**Eigenvalues and eigenvectors** reveal the intrinsic, fundamental behavior of a linear transformation represented by a matrix. They describe the directions that remain unchanged when a transformation is applied. This concept is not just theoretical; it is the mathematical backbone for understanding phenomena in physics (like quantum mechanics), engineering (like vibration analysis), data science (like Principal Component Analysis), and computer graphics. Understanding these concepts allows us to simplify complex systems by finding the directions where the transformation acts purely as a scaling operation.

## 🧠 Core Concepts: Defining Eigen-Structures

### 1. The Definition

For a square matrix $\mathbf{A}$, a non-zero vector $\mathbf{v}$, and a scalar $\lambda$, the relationship that defines an **eigenvector** and its corresponding **eigenvalue** is:

$$\mathbf{A}\mathbf{v} = \lambda\mathbf{v}$$

*   **Eigenvector ($\mathbf{v}$):** This is a special, non-zero vector that, when multiplied by the matrix $\mathbf{A}$, results in a vector that points in the *exact same direction* as the original vector $\mathbf{v}$. It only gets scaled, not rotated.
*   **Eigenvalue ($\lambda$):** This is the scalar factor by which the eigenvector $\mathbf{v}$ is scaled during the transformation. It quantifies *how much* the eigenvector is stretched or compressed.

### 2. Intuition: What does this mean?

Imagine a transformation (matrix $\mathbf{A}$) acting on the entire 2D plane. Most vectors will be spun around. However, if you pick a vector lying along a special direction (the eigenvector), applying the transformation only stretches or shrinks that vector along its own line. The eigenvalue tells you the factor of that stretch/shrink.

### 3. Calculating Eigenvalues and Eigenvectors

To find the eigenvalues ($\lambda$) and eigenvectors ($\mathbf{v}$) for a matrix $\mathbf{A}$, we must rearrange the defining equation:

$$\mathbf{A}\mathbf{v} = \lambda\mathbf{v}$$

We can rewrite $\lambda\mathbf{v}$ as $\lambda\mathbf{I}\mathbf{v}$, where $\mathbf{I}$ is the identity matrix of the same dimension as $\mathbf{A}$:

$$\mathbf{A}\mathbf{v} = \lambda\mathbf{I}\mathbf{v}$$
$$\mathbf{A}\mathbf{v} - \lambda\mathbf{I}\mathbf{v} = \mathbf{0}$$
$$(\mathbf{A} - \lambda\mathbf{I})\mathbf{v} = \mathbf{0}$$

For this system to have a non-trivial solution (i.e., $\mathbf{v} \neq \mathbf{0}$), the matrix $(\mathbf{A} - \lambda\mathbf{I})$ must be singular, meaning its determinant must be zero. This leads us to the **Characteristic Equation**:

$$\det(\mathbf{A} - \lambda\mathbf{I}) = 0$$

**Step-by-Step Process:**

1.  **Calculate the Characteristic Equation:** Find the determinant of $(\mathbf{A} - \lambda\mathbf{I})$ and set it equal to zero. Solve this resulting polynomial equation for $\lambda$. These solutions are the **eigenvalues**.
2.  **Determine Eigenvectors:** For each eigenvalue $\lambda_i$ found, substitute it back into the equation $(\mathbf{A} - \lambda_i\mathbf{I})\mathbf{v} = \mathbf{0}$ and solve the resulting system of linear equations for the components of the eigenvector $\mathbf{v}$.

---

## 🛠️ Worked Example: Finding Eigenvalues and Eigenvectors

Let's find the eigenvalues and eigenvectors for the following $2 \times 2$ matrix:
$$\mathbf{A} = \begin{pmatrix} 4 & 1 \\ 2 & 3 \end{pmatrix}$$

### Step 1: Calculate the Eigenvalues ($\lambda$)

We start by finding the characteristic equation: $\det(\mathbf{A} - \lambda\mathbf{I}) = 0$.

$$\mathbf{A} - \lambda\mathbf{I} = \begin{pmatrix} 4 & 1 \\ 2 & 3 \end{pmatrix} - \lambda \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} = \begin{pmatrix} 4-\lambda & 1 \\ 2 & 3-\lambda \end{pmatrix}$$

Now, calculate the determinant:
$$\det(\mathbf{A} - \lambda\mathbf{I}) = (4-\lambda)(3-\lambda) - (1)(2)$$
$$= (12 - 4\lambda - 3\lambda + \lambda^2) - 2$$
$$= \lambda^2 - 7\lambda + 10$$

Set the determinant to zero to find the characteristic equation:
$$\lambda^2 - 7\lambda + 10 = 0$$

Factor the quadratic equation:
$$(\lambda - 5)(\lambda - 2) = 0$$

The **eigenvalues** are:
$$\lambda_1 = 5 \quad \text{and} \quad \lambda_2 = 2$$

### Step 2: Determine the Eigenvectors ($\mathbf{v}$)

**Case 1: For $\lambda_1 = 5$**

We solve the system $(\mathbf{A} - 5\mathbf{I})\mathbf{v} = \mathbf{0}$:
$$\begin{pmatrix} 4-5 & 1 \\ 2 & 3-5 \end{pmatrix} \begin{pmatrix} v_1 \\ v_2 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix}$$
$$\begin{pmatrix} -1 & 1 \\ 2 & -2 \end{pmatrix} \begin{pmatrix} v_1 \\ v_2 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix}$$

This gives us the equations:
1) $-v_1 + v_2 = 0 \implies v_1 = v_2$
2) $2v_1 - 2v_2 = 0 \implies v_1 = v_2$

We can choose any non-zero value for $v_1$. Let $v_1 = 1$. Then $v_2 = 1$.
The **eigenvector** corresponding to $\lambda_1 = 5$ is $\mathbf{v}_1 = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$.

**Case 2: For $\lambda_2 = 2$**

We solve the system $(\mathbf{A} - 2\mathbf{I})\mathbf{v} = \mathbf{0}$:
$$\begin{pmatrix} 4-2 & 1 \\ 2 & 3-2 \end{pmatrix} \begin{pmatrix} v_1 \\ v_2 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix}$$
$$\begin{pmatrix} 2 & 1 \\ 2 & 1 \end{pmatrix} \begin{pmatrix} v_1 \\ v_2 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \end{pmatrix}$$

This gives us the equations:
1) $2v_1 + v_2 = 0 \implies v_2 = -2v_1$
2) $2v_1 + v_2 = 0$

Let $v_1 = 1$. Then $v_2 = -2$.
The **eigenvector** corresponding to $\lambda_2 = 2$ is $\mathbf{v}_2 = \begin{pmatrix} 1 \\ -2 \end{pmatrix}$.

**Summary of Results:**
*   **Eigenvalue $\lambda_1 = 5$** corresponds to **Eigenvector $\mathbf{v}_1 = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$**.
*   **Eigenvalue $\lambda_2 = 2$** corresponds to **Eigenvector $\mathbf{v}_2 = \begin{pmatrix} 1 \\ -2 \end{pmatrix}$**.

---

## 📝 Recap

*   **Definition:** Eigenvectors ($\mathbf{v}$) are special vectors that only scale when a matrix ($\mathbf{A}$) acts upon them, and the scaling factor is the eigenvalue ($\lambda$).
*   **The Core Equation:** $\mathbf{A}\mathbf{v} = \lambda\mathbf{v}$.
*   **Finding Eigenvalues:** Solve the **Characteristic Equation**: $\det(\mathbf{A} - \lambda\mathbf{I}) = 0$.
*   **Finding Eigenvectors:** Substitute each eigenvalue back into $(\mathbf{A} - \lambda\mathbf{I})\mathbf{v} = \mathbf{0}$ and solve the resulting system of equations.

## ✅ Check Your Understanding

1.  If a matrix transformation results in an eigenvalue of $\lambda = 1$, what does this imply about the eigenvector $\mathbf{v}$?
2.  What is the primary mathematical tool used to find the eigenvalues of a matrix?
3.  If you find an eigenvector $\mathbf{v}$ for an eigenvalue $\lambda$, what is the result of the matrix multiplication $\mathbf{A}\mathbf{v}$?
