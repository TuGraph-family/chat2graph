class GraphDb:
    """Graph store implementation."""

    def __init__(self, config):
        """Initialize graph store with configuration."""
        self.config = config
        self._driver = None

    @property
    def conn(self):
        """Get the database connection."""
        raise NotImplementedError("Subclasses should implement this method.")
