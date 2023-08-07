import logging

from pylint.lint import Run
from pylint.lint.pylinter import LinterStats

LINT_PATH = "."
THRESHOLD = 8
PYLINT_ARGS = [
    "-d=W0511",  # disable TODOs
    "--recursive=y",
    LINT_PATH,
]

MAX_WARNINGS = 30

SHOULD_CHECK_WARNINGS_AND_SCORE = False

logging.getLogger().setLevel(logging.INFO)


def _display_stats(stats: LinterStats):
    print()
    logging.info(" Score: %f", stats.global_note)
    logging.info(" FATAL: %d", stats.fatal)
    logging.info(" ERROR: %d", stats.error)
    logging.info(" WARNING: %d", stats.warning)
    logging.info(" REFACTOR: %d", stats.refactor)
    logging.info(" CONVENTION: %d", stats.convention)
    print()


def _exit_with_error(message: str):
    logging.error(message)
    raise Exception(message)


def _check_errors() -> LinterStats:
    logging.info(" Start checking errors only")
    stats = Run(["-E"] + PYLINT_ARGS, exit=False).linter.stats
    logging.info(" Finish checking errors only")
    print()
    return stats


def _exit():
    logging.info(" SUCCESSFULLY FINISHED")

    exit(0)


def main():
    error_stats = _check_errors()

    if error_stats.fatal > 0 or error_stats.error > 0:
        return _exit_with_error(" Code contains errors")

    if not SHOULD_CHECK_WARNINGS_AND_SCORE:
        _exit()

    results = Run(PYLINT_ARGS, exit=False)
    stats = results.linter.stats
    _display_stats(stats)

    if stats.warning > MAX_WARNINGS:
        return _exit_with_error(f"Too many WARNINGs ({stats.warning}/{MAX_WARNINGS})")

    final_score = round(stats.global_note, 3)
    if final_score < THRESHOLD:
        return _exit_with_error(
            f"Score threshold is not passed ({final_score}/{THRESHOLD})"
        )


if __name__ == "__main__":
    main()
