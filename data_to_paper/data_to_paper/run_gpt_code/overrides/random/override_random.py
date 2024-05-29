from dataclasses import dataclass
from typing import Optional, Any

from data_to_paper.run_gpt_code.base_run_contexts import RegisteredRunContext


@dataclass
class SetRandomSeeds(RegisteredRunContext):
    """
    Set the global seed of:
    - numpy (np.random.seed)
    - random (random.seed)
    """
    random_seed: Optional[int] = 0  # None to disable
    _np_seed: Optional[Any] = None
    _random_seed: Optional[Any] = None

    def __enter__(self):
        if self.random_seed is not None:
            import numpy as np
            import random
            self._np_seed = np.random.get_state()
            self._random_seed = random.getstate()
            np.random.seed(self.random_seed)
            random.seed(self.random_seed)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.random_seed is not None:
            import numpy as np
            import random
            np.random.set_state(self._np_seed)
            random.setstate(self._random_seed)
            self._np_seed = None
            self._random_seed = None
        return super().__exit__(exc_type, exc_val, exc_tb)
