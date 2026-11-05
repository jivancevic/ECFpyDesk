import pytest

from models.config import ConfigurationManager

ROWS = [f"{i}\t-0\t{i * 0.0436444}" for i in range(100)]


@pytest.fixture
def files(tmp_path):
    source = tmp_path / "input.txt"
    source.write_text("\n".join(ROWS) + "\n")
    return source, tmp_path / "train.txt", tmp_path / "test.txt"


def split(files, ratio, choice="random", **kwargs):
    source, train, test = files
    ConfigurationManager().split_train_test(str(source), str(train), str(test), ratio, choice, **kwargs)
    return train.read_text().splitlines(), test.read_text().splitlines() if test.exists() else None


@pytest.mark.parametrize("choice", ["random", "sequential"])
@pytest.mark.parametrize("ratio,train_rows", [(0.5, 50), (0.6, 60), (0.7, 70), (0.75, 75), (0.8, 80)])
def test_every_row_ends_up_in_exactly_one_set(files, ratio, train_rows, choice):
    train, test = split(files, ratio, choice)

    assert len(train) == train_rows
    assert sorted(train + test) == sorted(ROWS)


def test_no_header_is_added_and_no_row_is_taken_for_one(files):
    train, test = split(files, 0.8, "sequential")

    assert train[0] == ROWS[0]
    assert test[0] == ROWS[80]


def test_values_stay_exactly_as_they_were_written(files):
    train, test = split(files, 0.5)

    assert all(row.split("\t")[1] == "-0" for row in train + test)


def test_sequential_keeps_the_order(files):
    train, test = split(files, 0.7, "sequential")

    assert train == ROWS[:70]
    assert test == ROWS[70:]


def test_random_shuffles(files):
    train, _ = split(files, 0.7, "random")

    assert train != ROWS[:70]


def test_without_a_split_the_train_set_is_the_whole_input(files):
    train, test = split(files, 1)

    assert train == ROWS
    assert test is None


def test_a_previous_test_set_does_not_survive(files):
    split(files, 0.5)
    _, test = split(files, 1)

    assert test is None


def test_empty_lines_do_not_reach_srm(files):
    source, train, test = files
    source.write_text("1\t2\n\n3\t4\r\n\n")

    assert split(files, 1)[0] == ["1\t2", "3\t4"]


def test_a_row_stays_with_its_error_weight(files, tmp_path):
    weights = tmp_path / "weights.txt"
    weights.write_text("\n".join(str(i) for i in range(100)) + "\n")
    train_weights = tmp_path / "train_weights.txt"
    test_weights = tmp_path / "test_weights.txt"

    train, test = split(files, 0.7, "random", error_weights_path=str(weights), train_weights_path=str(train_weights), test_weights_path=str(test_weights))

    assert [row.split("\t")[0] for row in train] == train_weights.read_text().splitlines()
    assert [row.split("\t")[0] for row in test] == test_weights.read_text().splitlines()


def test_too_few_error_weights_is_an_error(files, tmp_path):
    weights = tmp_path / "weights.txt"
    weights.write_text("1\n2\n")

    with pytest.raises(ValueError):
        split(files, 0.7, error_weights_path=str(weights), train_weights_path=str(tmp_path / "a"), test_weights_path=str(tmp_path / "b"))


def test_a_single_row_cannot_be_split(files):
    source, _, _ = files
    source.write_text("1\t2\n")

    with pytest.raises(ValueError):
        split(files, 0.5)
