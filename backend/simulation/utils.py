"""Mathematical utilities for portfolio simulation."""

import numpy as np

def make_positive_definite(matrix: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """Make a matrix positive definite by adjusting eigenvalues.
    
    Args:
        matrix: Input correlation matrix
        epsilon: Minimum eigenvalue threshold
        
    Returns:
        Adjusted positive definite matrix
    """
    # Eigenvalue decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    
    # Adjust negative eigenvalues
    eigenvalues[eigenvalues < epsilon] = epsilon
    
    # Reconstruct matrix
    adjusted_matrix = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    
    # Normalize to correlation matrix (diagonal = 1)
    d = np.sqrt(np.diag(adjusted_matrix))
    adjusted_matrix = adjusted_matrix / np.outer(d, d)
    
    return adjusted_matrix
