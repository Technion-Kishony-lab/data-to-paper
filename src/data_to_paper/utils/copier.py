from dataclasses import dataclass


@dataclass
class Copier:
    """
    Base class for dataclass classes that have specific attributes that should be copied from other instances of the
    same-class, sub-classes or super-classes.
    """
    COPY_ATTRIBUTES = ()

    @classmethod
    def get_copy_attributes(cls):
        """
        Recursively gather COPY_ATTRIBUTES from the current class and its superclasses,
        but only from classes that are subclasses of Copier.
        """
        # Collect attributes from current class and all parent classes that are subclasses of Copier
        attrs = set()
        for base in cls.__mro__:
            if issubclass(base, Copier):
                attrs.update(getattr(base, 'COPY_ATTRIBUTES'))
        return attrs

    @classmethod
    def from_(cls, other, **kwargs):
        """
        Create a new instance of the class, copying attributes from another instance of the same class.
        """
        k = dict()
        for attr in cls.get_copy_attributes():
            if attr in kwargs:
                k[attr] = kwargs.pop(attr)
            elif hasattr(other, attr):
                k[attr] = getattr(other, attr)
        return cls(**k, **kwargs)
