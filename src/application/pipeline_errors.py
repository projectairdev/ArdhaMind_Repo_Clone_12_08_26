class PipelineBlockedError(RuntimeError):
    """A critical validated dependency is unavailable or blocked."""


class PipelineInputError(ValueError):
    """A runtime value failed contract validation."""
