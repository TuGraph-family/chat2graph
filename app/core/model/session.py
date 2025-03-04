from dataclasses import dataclass


@dataclass
class Session:
    """Session class"""
    id: str
    name: str
    created_at: str
    
