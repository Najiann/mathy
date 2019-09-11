from typing import Any, List, Optional, Type

from tf_agents.trajectories import time_step

from ..core.expressions import MathExpression
from ..game_modes import MODE_SIMPLIFY_POLYNOMIAL
from ..mathy_env import MathyEnv, MathyEnvProblem
from ..mathy_env_state import MathyEnvState
from ..problems import commute_haystack
from ..rules import AssociativeSwapRule, BaseRule, CommutativeSwapRule
from ..rules.helpers import TermEx, get_term_ex, get_terms
from ..types import MathyEnvDifficulty, MathyEnvProblemArgs


class MathyPolynomialGroupingEnv(MathyEnv):
    """A Mathy environment for grouping polynomial terms that are like.

    The goal is to commute all the like terms so they become siblings as quickly as
    possible.
    """

    def get_rewarding_actions(self, state: MathyEnvState) -> List[Type[BaseRule]]:
        return [CommutativeSwapRule, AssociativeSwapRule]

    def max_moves_fn(
        self, problem: MathyEnvProblem, config: MathyEnvProblemArgs
    ) -> int:
        return problem.complexity

    def transition_fn(
        self, env_state: MathyEnvState, expression: MathExpression, features: Any
    ) -> Optional[time_step.TimeStep]:
        """If all like terms are siblings."""
        term_nodes = get_terms(expression)
        already_seen: set = set()
        current_term = ""
        # Iterate over each term in order and build a unique key to identify its
        # term likeness. For this we drop the coefficient from the term and use
        # only its variable/exponent to build keys.
        for term in term_nodes:
            ex: Optional[TermEx] = get_term_ex(term)
            if ex is None:
                raise ValueError("should this happen?")
            key = f"{ex.variable}{ex.exponent}"
            # If the key is in the "already seen and moved on" list then we've failed
            # to meet the completion criteria. e.g. the final x in "4x + 2y + x"
            if key in already_seen:
                return None
            if key != current_term:
                already_seen.add(current_term)
                current_term = key

        return time_step.termination(features, self.get_win_signal(env_state))

    def problem_fn(self, params: MathyEnvProblemArgs) -> MathyEnvProblem:
        complexity = 2
        if params.difficulty == MathyEnvDifficulty.easy:
            text, _ = commute_haystack(
                min_terms=4, max_terms=12, easy=True, powers=True
            )
        elif params.difficulty == MathyEnvDifficulty.normal:
            text, _ = commute_haystack(
                min_terms=8, max_terms=16, easy=False, powers=True
            )
        elif params.difficulty == MathyEnvDifficulty.hard:
            text, _ = commute_haystack(
                min_terms=12, max_terms=24, easy=False, powers=True
            )
        else:
            raise ValueError(f"Unknown difficulty: {params.difficulty}")
        return MathyEnvProblem(text, complexity, MODE_SIMPLIFY_POLYNOMIAL)
