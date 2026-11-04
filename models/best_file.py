"""Reading what SRM writes: the best file of a Process and the result of an evaluation run."""
import math
import re

# One block of a best file. SRM appends blocks while the app reads, so a read can end in the
# middle of one: anything that does not match yet stays for the next read.
BLOCK_PATTERN = re.compile(
    r'^(?P<generation>\d+)\r?\n'
    r'(?P<function>.+?)\r?\n'
    r'<Individual[^>\r\n]*>\r?\n'
    r'\s*<FitnessMin value="(?P<error>[^"]*)"/>\r?\n'
    r'\s*<Tree size="(?P<size>\d+)">(?P<prefix_function>[^<]*)</Tree>\r?\n'
    r'</Individual>\r?\n',
    re.MULTILINE,
)
FITNESS_PATTERN = re.compile(r'<FitnessMin value="([^"]*)"')


def parse_float(text):
    try:
        return float(text)
    except ValueError:
        # MSVC prints NaN as -nan(ind)
        return float("nan")


def parse_best_text(text):
    """Returns the individuals in text and the unfinished rest of it."""
    individuals = []
    end = 0
    for match in BLOCK_PATTERN.finditer(text):
        end = match.end()
        error = parse_float(match["error"])
        if not math.isfinite(error):
            continue
        individuals.append({
            "generation": int(match["generation"]),
            "function": match["function"].strip(),
            "error": error,
            "size": int(match["size"]),
            "prefix_function": match["prefix_function"].strip(),
        })
    return individuals, text[end:]


def parse_evaluation(best_text, srm_output):
    """Returns the error and the value at each sample from an evaluation run.

    The error comes from SRM's output. The Individual in the best file carries the fitness it
    was given as input, which is the error on the train set, whatever data was evaluated.
    """
    fitness_values = FITNESS_PATTERN.findall(srm_output)
    _, closing_tag, values = best_text.partition("</Individual>")
    if not fitness_values or not closing_tag:
        raise ValueError("SRM wrote no evaluation result")
    return parse_float(fitness_values[-1]), [parse_float(line) for line in values.split()]
