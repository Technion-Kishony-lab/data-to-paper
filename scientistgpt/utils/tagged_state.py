from dataclasses import dataclass, field


@dataclass
class TaggedState:
    """
    A general dataclass that can store and restore its state by a tag
    """

    store_state_by_tag: list = field(default_factory=list)

    def restore_state(self, tag):
        """
        Rewind the state of the object to the state immediately after tagging by tag
        """
        while self.store_state_by_tag:
            if self.store_state_by_tag[-1][0] == tag:
                self.__dict__.update(self.store_state_by_tag[-1][1])
                return
            else:
                self.store_state_by_tag.pop()
        raise ValueError(f'no state stored by tag {tag}')

    def store_state(self, tag):
        """
        Store the state of the object by the tag
        """
        state = self.__dict__.copy()
        state.pop('store_state_by_tag')
        self.store_state_by_tag.append((tag, state))

    def is_tag(self, tag) -> bool:
        """
        Check if the tag exists
        """
        return any([tag == t for t, _ in self.store_state_by_tag])

    def create_or_reset_to_tag(self, tag):
        """
        Create a tag if it does not exist, or reset the object state to the state immediately after tagging.
        """
        if self.is_tag(tag):
            self.restore_state(tag)
        else:
            self.store_state(tag)
