import pytest

from models.best_file import parse_best_text, parse_evaluation
from models.main import Model

BLOCK = """{generation}
{function}
<Individual size="1">
\t<FitnessMin value="{error}"/>
\t<Tree size="{size}">{prefix} </Tree>
</Individual>

"""


def block(generation=10, function="-0.5 + 0.2 * (x1 + x2)", error="0.25", size=9, prefix="+ D_-0.5 * D_0.2 + x1 x2"):
    return BLOCK.format(generation=generation, function=function, error=error, size=size, prefix=prefix)


def test_reads_every_field():
    individuals, rest = parse_best_text(block())

    assert individuals == [{
        "generation": 10,
        "function": "-0.5 + 0.2 * (x1 + x2)",
        "error": 0.25,
        "size": 9,
        "prefix_function": "+ D_-0.5 * D_0.2 + x1 x2",
    }]
    assert rest.strip() == ""


def test_reads_all_blocks_in_order():
    individuals, _ = parse_best_text(block(generation=0) + block(generation=10) + block(generation=20))

    assert [individual["generation"] for individual in individuals] == [0, 10, 20]


@pytest.mark.parametrize("cut", range(1, len(block()) - 2))
def test_a_read_can_end_anywhere_in_a_block(cut):
    """SRM appends while the app reads, so the second read starts where the first one stopped."""
    text = block(generation=0) + block(generation=10)
    first_end = len(block()) + cut

    first, rest = parse_best_text(text[:first_end])
    second, rest = parse_best_text(rest + text[first_end:])

    assert [i["generation"] for i in first + second] == [0, 10]


def test_windows_line_ends():
    individuals, _ = parse_best_text(block().replace("\n", "\r\n"))

    assert individuals[0]["error"] == 0.25
    assert individuals[0]["function"] == "-0.5 + 0.2 * (x1 + x2)"


def test_a_function_that_looks_like_a_generation_number():
    individuals, _ = parse_best_text(block(generation=30, function="2", size=1, prefix="2"))

    assert individuals[0]["generation"] == 30
    assert individuals[0]["function"] == "2"


@pytest.mark.parametrize("error", ["nan", "-nan", "inf", "-nan(ind)"])
def test_an_individual_without_a_finite_error_is_skipped(error):
    individuals, rest = parse_best_text(block(error=error) + block(generation=20))

    assert [individual["generation"] for individual in individuals] == [20]
    assert rest.strip() == ""


def test_evaluation_takes_the_error_from_srm_output_not_from_the_best_file():
    """The best file only repeats the fitness of the Individual it was given."""
    best_text = block(generation=0, error="0.25") + "1\n0.801331\n-2e-05\n"
    output = 'Parsing configuration file\n<Individual size="1">\n\t<FitnessMin value="3.5"/>\n</Individual>\n'

    assert parse_evaluation(best_text, output) == (3.5, [1.0, 0.801331, -2e-05])


@pytest.mark.parametrize("best_text,output", [("", '<FitnessMin value="1"/>'), (block(), "Error: Initialization failed!")])
def test_evaluation_without_a_result_is_an_error(best_text, output):
    with pytest.raises(ValueError):
        parse_evaluation(best_text, output)


class ReadingFixture:
    def __init__(self, tmp_path):
        self.model = Model()
        self.path = tmp_path / "best.txt"
        self.model.config_manager.configurations[0] = type("Config", (), {"best_file_path": str(self.path)})
        self.model.register_process(0)

    def append(self, text):
        with open(self.path, "a", newline="") as file:
            file.write(text)


@pytest.fixture
def reading(tmp_path):
    return ReadingFixture(tmp_path)


def test_each_individual_is_returned_once(reading):
    reading.append(block(generation=0, function="a"))
    assert [i["function"] for i in reading.model.read_new_individuals(0)] == ["a"]

    reading.append(block(generation=10, function="a") + block(generation=20, function="b"))
    assert [i["function"] for i in reading.model.read_new_individuals(0)] == ["b"]

    assert reading.model.read_new_individuals(0) == []


def test_a_missing_best_file_is_no_error(reading):
    assert reading.model.read_new_individuals(0) == []


def test_a_block_split_between_reads(reading):
    text = block(function="a")
    reading.append(text[:30])
    assert reading.model.read_new_individuals(0) == []

    reading.append(text[30:])
    assert [i["function"] for i in reading.model.read_new_individuals(0)] == ["a"]


def test_a_restarted_process_starts_reading_from_the_top(reading):
    reading.append(block(function="a") * 3)
    reading.model.read_new_individuals(0)

    reading.model.reset_file_reading(0)
    assert not reading.path.exists()

    reading.append(block(function="b"))
    assert [i["function"] for i in reading.model.read_new_individuals(0)] == ["b"]


def test_what_a_process_wrote_last_survives_its_restart(reading):
    """SRM ends right after writing its best Individual, before the next read comes."""
    reading.append(block(function="a"))
    reading.model.read_new_individuals(0)
    reading.append(block(function="b"))

    reading.model.reset_file_reading(0)
    reading.append(block(function="c"))

    assert [i["function"] for i in reading.model.read_new_individuals(0)] == ["b", "c"]
    assert reading.model.read_new_individuals(0) == []


def test_a_shorter_file_does_not_lose_the_reading_position(reading):
    """If SRM truncates the file behind the app's back, reading must still find later blocks."""
    reading.append(block(function="a") * 3)
    reading.model.read_new_individuals(0)

    reading.path.write_text("")
    assert reading.model.read_new_individuals(0) == []

    reading.append(block(function="b"))
    assert [i["function"] for i in reading.model.read_new_individuals(0)] == ["b"]
