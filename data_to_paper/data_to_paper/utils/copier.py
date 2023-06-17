from dataclasses import dataclass


@dataclass
class Copier:
    """
    Base class for dataclass classes that have specific attributes that should be copied from other instances of the
    same-class, sub-classes or super-classes.
    """
    COPY_ATTRIBUTES = ()

    @classmethod
    def from_(cls, other, **kwargs):
        # copy the COPY_ATTRIBUTES attributes from other to self, if they exist in other and self
        k = {**{attr: kwargs.pop(attr, getattr(other, attr)) for attr in cls.COPY_ATTRIBUTES
                if hasattr(other, attr) and hasattr(cls, attr)}, **kwargs}
        return cls(**k)
