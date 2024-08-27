from dataclasses import dataclass
from typing import Optional

from data_to_paper.run_gpt_code.base_run_contexts import RegisteredRunContext


@dataclass
class SetRandomSeeds(RegisteredRunContext):
    """
    Set the global seed of:
    - numpy (np.random.seed)
    - random (random.seed)
    """
    random_seed: Optional[int] = 0  # None to disable

    def _reversible_enter(self):
        if self.random_seed is not None:
            import numpy as np
            import random
            self._np_seed = np.random.get_state()
            self._random_seed = random.getstate()
            np.random.seed(self.random_seed)
            random.seed(self.random_seed)
        return super()._reversible_enter()

    def _reversible_exit(self):
        if self.random_seed is not None:
            import numpy as np
            import random
            np.random.set_state(self._np_seed)
            random.setstate(self._random_seed)
        return super()._reversible_exit()
