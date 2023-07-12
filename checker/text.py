"""Contains Text Checker class"""

from checker.basic import Checker
from typing import List, Tuple

from utils.basic import map_verdict


class TextChecker(Checker):
    """Provides evaluation for text tasks"""

    async def start(
        self, user_answers: List[str], correct_answers: List[str]
    ) -> Tuple[List[int], List[str]]:
        """Starts checker

        Args:
            user_answers (list[str]): user answers
            correct_answers (list[str]): correct answers

        Returns:
            tuple[list[int], list[str]]: (verdicts, logs)
        """

        user_answers_length = len(user_answers)
        verdicts: List[int] = []
        for i, correct_answer in enumerate(correct_answers):
            if i >= user_answers_length:
                verdict = "WA"
            else:
                verdict = (
                    "OK"
                    if self._compare_strings(correct_answer, user_answers[i])
                    else "WA"
                )
            verdicts.append(map_verdict(verdict))

        return verdicts, []
