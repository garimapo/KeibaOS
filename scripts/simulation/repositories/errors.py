"""Repository boundary exceptions for the simulation subsystem."""


class SimulationRepositoryError(Exception):
    """Base class for expected repository failures."""


class RepositoryValidationError(SimulationRepositoryError):
    """A caller supplied an invalid value or the database contained invalid data."""


class RepositoryConflictError(SimulationRepositoryError):
    """An immutable publication already exists with different content."""


class RepositoryDataIntegrityError(SimulationRepositoryError):
    """A database constraint or stored-data invariant was violated."""
