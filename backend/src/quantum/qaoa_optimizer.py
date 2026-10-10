"""
Q-Care Quantum Optimizer V3

Experimental QAOA optimizer for evidence selection.

The quantum objective is NOT medical diagnosis.

This module supports QAOA circuits with configurable depth:

    p = 1
    p = 2
    p = 3

The underlying optimization problem is:

    C(x) = -sum(s_i * x_i)
           + lambda * (sum(x_i) - K)^2

where:

    x_i ∈ {0, 1}
    s_i = evidence score
    K   = maximum number of selected evidence items
"""

import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector


# =========================================================
# Classical QUBO
# =========================================================

def calculate_cost(
    selection,
    scores,
    maximum_selected=2,
    penalty=10.0,
):
    """Calculate the original QUBO cost."""

    reward = sum(
        score * bit
        for score, bit in zip(scores, selection)
    )

    selected_count = sum(selection)

    constraint_penalty = penalty * (
        selected_count - maximum_selected
    ) ** 2

    return -reward + constraint_penalty


# =========================================================
# QUBO → Hamiltonian
# =========================================================

def _cost_hamiltonian_coefficients(
    scores,
    maximum_selected=2,
    penalty=10.0,
):
    """
    Convert the binary QUBO into Z and ZZ coefficients.

    The resulting Hamiltonian is equivalent to the QUBO
    up to a constant global energy shift.
    """

    number_of_qubits = len(scores)

    linear_coefficients = [
        -score
        + penalty * (1 - 2 * maximum_selected)
        for score in scores
    ]

    pair_coefficient = 2 * penalty

    z_coefficients = []

    for i in range(number_of_qubits):

        pair_contribution = (
            (number_of_qubits - 1)
            * pair_coefficient
            / 4
        )

        z_value = (
            -linear_coefficients[i] / 2
            - pair_contribution
        )

        z_coefficients.append(z_value)

    zz_coefficient = pair_coefficient / 4

    return z_coefficients, zz_coefficient


# =========================================================
# QAOA Circuit
# =========================================================

def build_qaoa_circuit(
    scores,
    penalty=10.0,
    p=1,
):
    """
    Build a parameterized QAOA circuit.

    Supported depths:

        p = 1
        p = 2
        p = 3

    Each layer contains:

        cost separator
        mixer

    Parameters are named:

        gamma_1, beta_1
        gamma_2, beta_2
        ...
    """

    if not isinstance(p, int) or p < 1:
        raise ValueError(
            "Q-Care QAOA depth p must be a positive integer."
        )

    number_of_qubits = len(scores)

    circuit = QuantumCircuit(
        number_of_qubits
    )

    # -----------------------------------------------------
    # Initial uniform superposition
    # -----------------------------------------------------

    for qubit in range(number_of_qubits):
        circuit.h(qubit)

    z_coefficients, zz_coefficient = (
        _cost_hamiltonian_coefficients(
            scores,
            maximum_selected=2,
            penalty=penalty,
        )
    )

    # -----------------------------------------------------
    # QAOA layers
    # -----------------------------------------------------

    for layer in range(1, p + 1):

        gamma = Parameter(
            f"gamma_{layer}"
        )

        beta = Parameter(
            f"beta_{layer}"
        )

        # -------------------------------------------------
        # Cost separator
        # -------------------------------------------------

        for qubit, coefficient in enumerate(
            z_coefficients
        ):
            circuit.rz(
                2 * gamma * coefficient,
                qubit,
            )

        # -------------------------------------------------
        # Pairwise ZZ terms
        # -------------------------------------------------

        for i in range(number_of_qubits):

            for j in range(
                i + 1,
                number_of_qubits,
            ):

                circuit.rzz(
                    2 * gamma * zz_coefficient,
                    i,
                    j,
                )

        # -------------------------------------------------
        # Mixer
        # -------------------------------------------------

        for qubit in range(number_of_qubits):

            circuit.rx(
                2 * beta,
                qubit,
            )

    return circuit


# =========================================================
# Statevector Evaluation
# =========================================================

def evaluate_statevector(
    circuit,
    gamma,
    beta,
):
    """
    Evaluate a QAOA circuit.

    This function preserves compatibility with the
    original p=1 optimizer.

    For p=1:
        gamma = scalar
        beta  = scalar

    For p>1:
        use evaluate_statevector_layers().
    """

    parameters = {
        parameter.name: parameter
        for parameter in circuit.parameters
    }

    if "gamma_1" in parameters:

        bound = circuit.assign_parameters(
            {
                parameters["gamma_1"]: gamma,
                parameters["beta_1"]: beta,
            }
        )

    else:

        # Compatibility with an older p=1 circuit.
        bound = circuit.assign_parameters(
            {
                parameters["gamma"]: gamma,
                parameters["beta"]: beta,
            }
        )

    return Statevector.from_instruction(
        bound
    )


def evaluate_statevector_layers(
    circuit,
    gammas,
    betas,
):
    """
    Bind multiple QAOA layers.

    gammas = [gamma_1, gamma_2, ...]
    betas  = [beta_1, beta_2, ...]
    """

    if len(gammas) != len(betas):
        raise ValueError(
            "QAOA gamma and beta layer counts must match."
        )

    parameter_map = {
        parameter.name: parameter
        for parameter in circuit.parameters
    }

    bindings = {}

    for index, (
        gamma_value,
        beta_value,
    ) in enumerate(
        zip(gammas, betas),
        start=1,
    ):

        gamma_name = f"gamma_{index}"
        beta_name = f"beta_{index}"

        if gamma_name not in parameter_map:
            raise ValueError(
                f"Missing parameter {gamma_name}."
            )

        if beta_name not in parameter_map:
            raise ValueError(
                f"Missing parameter {beta_name}."
            )

        bindings[
            parameter_map[gamma_name]
        ] = gamma_value

        bindings[
            parameter_map[beta_name]
        ] = beta_value

    bound = circuit.assign_parameters(
        bindings
    )

    return Statevector.from_instruction(
        bound
    )


# =========================================================
# Expectation Value
# =========================================================

def calculate_expectation(
    statevector,
    scores,
    penalty=10.0,
):
    """
    Calculate the expected value of the original QUBO.
    """

    probabilities = (
        statevector.probabilities()
    )

    number_of_qubits = len(scores)

    expectation = 0.0

    for integer_state, probability in enumerate(
        probabilities
    ):

        bits = tuple(
            (integer_state >> qubit) & 1
            for qubit in range(
                number_of_qubits
            )
        )

        cost = calculate_cost(
            bits,
            scores,
            maximum_selected=2,
            penalty=penalty,
        )

        expectation += (
            probability * cost
        )

    return float(
        np.real(expectation)
    )


# =========================================================
# p=1 Parameter Search
# =========================================================

def search_qaoa_parameters(
    scores,
    penalty=10.0,
    gamma_values=None,
    beta_values=None,
):
    """
    Search QAOA parameters for p=1.

    This preserves the original V2 API.
    """

    if gamma_values is None:
        gamma_values = np.linspace(
            0,
            2 * np.pi,
            21,
        )

    if beta_values is None:
        beta_values = np.linspace(
            0,
            np.pi,
            21,
        )

    circuit = build_qaoa_circuit(
        scores,
        penalty=penalty,
        p=1,
    )

    best = None

    for gamma in gamma_values:

        for beta in beta_values:

            statevector = (
                evaluate_statevector_layers(
                    circuit,
                    [gamma],
                    [beta],
                )
            )

            expectation = (
                calculate_expectation(
                    statevector,
                    scores,
                    penalty,
                )
            )

            if (
                best is None
                or expectation
                < best["expectation"]
            ):

                best = {
                    "gamma": float(gamma),
                    "beta": float(beta),
                    "expectation": float(
                        expectation
                    ),
                }

    return best


# =========================================================
# Multi-layer Parameter Search
# =========================================================

def search_qaoa_parameters_layers(
    scores,
    penalty=10.0,
    p=2,
    gamma_values=None,
    beta_values=None,
):
    """
    Layer-wise QAOA parameter optimization.

    Instead of performing an exponential grid over all
    2p parameters, optimize one layer at a time.

    This is an experimental optimization strategy.

    Returns:

        gammas
        betas
        expectation
    """

    if p < 1:
        raise ValueError(
            "QAOA depth must be at least 1."
        )

    if gamma_values is None:
        gamma_values = np.linspace(
            0,
            2 * np.pi,
            11,
        )

    if beta_values is None:
        beta_values = np.linspace(
            0,
            np.pi,
            11,
        )

    # Start with neutral parameter values.
    gammas = [0.0] * p
    betas = [0.0] * p

    circuit = build_qaoa_circuit(
        scores,
        penalty=penalty,
        p=p,
    )

    best_expectation = None

    # -----------------------------------------------------
    # Optimize each layer sequentially
    # -----------------------------------------------------

    for layer in range(p):

        layer_best = None

        for gamma in gamma_values:

            for beta in beta_values:

                test_gammas = list(
                    gammas
                )

                test_betas = list(
                    betas
                )

                test_gammas[layer] = (
                    float(gamma)
                )

                test_betas[layer] = (
                    float(beta)
                )

                statevector = (
                    evaluate_statevector_layers(
                        circuit,
                        test_gammas,
                        test_betas,
                    )
                )

                expectation = (
                    calculate_expectation(
                        statevector,
                        scores,
                        penalty,
                    )
                )

                if (
                    layer_best is None
                    or expectation
                    < layer_best["expectation"]
                ):

                    layer_best = {
                        "gamma": float(
                            gamma
                        ),
                        "beta": float(
                            beta
                        ),
                        "expectation": float(
                            expectation
                        ),
                    }

        gammas[layer] = (
            layer_best["gamma"]
        )

        betas[layer] = (
            layer_best["beta"]
        )

        best_expectation = (
            layer_best["expectation"]
        )

    # -----------------------------------------------------
    # Final evaluation
    # -----------------------------------------------------

    final_statevector = (
        evaluate_statevector_layers(
            circuit,
            gammas,
            betas,
        )
    )

    final_expectation = (
        calculate_expectation(
            final_statevector,
            scores,
            penalty,
        )
    )

    return {
        "gammas": gammas,
        "betas": betas,
        "expectation": float(
            final_expectation
        ),
    }


# =========================================================
# Solution Extraction
# =========================================================

def extract_best_solution(
    statevector,
    scores,
    penalty=10.0,
):
    """
    Extract the most probable computational basis state.

    This gives the candidate QAOA solution.

    It does NOT represent a medical diagnosis.
    """

    probabilities = (
        statevector.probabilities()
    )

    best_state = int(
        np.argmax(probabilities)
    )

    number_of_qubits = len(scores)

    selection = tuple(
        (best_state >> qubit) & 1
        for qubit in range(
            number_of_qubits
        )
    )

    return {
        "selection": selection,
        "probability": float(
            probabilities[best_state]
        ),
        "cost": calculate_cost(
            selection,
            scores,
            maximum_selected=2,
            penalty=penalty,
        ),
    }