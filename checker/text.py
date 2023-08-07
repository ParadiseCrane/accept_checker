"""Contains Text Checker class"""

from typing import List, Tuple

from checker.basic import Checker
from utils.basic import generate_tests_verdicts, group_values, map_verdict


class TextChecker(Checker):
    """Provides evaluation for text tasks"""

    def _test_group(
        self,
        user_answers: List[str],
        correct_answers: List[str],
    ) -> Tuple[bool, List[int]]:
        all_correct = True

        user_answers_length = len(user_answers)
        verdicts: List[int] = []
        for i, correct_answer in enumerate(correct_answers):
            if i < user_answers_length and self._compare_strings(
                correct_answer, user_answers[i]
            ):
                verdict = "OK"
            else:
                verdict = "WA"
                all_correct = False

            verdicts.append(map_verdict(verdict))

        return all_correct, verdicts

    async def start(
        self,
        user_answers: List[str],
        correct_answers: List[str],
        test_groups: List[int],
    ) -> Tuple[List[int], List[str]]:
        """Starts checker

        Args:
            user_answers (list[str]): user answers
            correct_answers (list[str]): correct answers
            test_groups (list[int]): index slices of test groups

        Returns:
            tuple[list[int], list[str]]: (verdicts, logs)
        """

        grouped_user_answers: List[List[str]] = group_values(user_answers, test_groups)
        grouped_correct_answers: List[List[str]] = group_values(
            correct_answers, test_groups
        )

        grouped_user_answers_len = len(grouped_user_answers)

        all_correct = True
        verdicts: List[int] = []
        for i, correct_answers_group in enumerate(grouped_correct_answers):
            if not all_correct:
                verdicts += generate_tests_verdicts("NT", len(correct_answers_group))
                continue

            if i >= grouped_user_answers_len:
                verdicts += generate_tests_verdicts("WA", len(correct_answers_group))
                continue

            all_correct, group_verdicts = self._test_group(
                grouped_user_answers[i], correct_answers_group
            )
            verdicts += group_verdicts

        return verdicts, []
