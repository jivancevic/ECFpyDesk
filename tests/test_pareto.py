from models.main import Model


def individual(size, error, **extra):
    return {"size": size, "error": error, "function": f"f{size}_{error}", **extra}


def pairs(functions, error_name="error"):
    return [(f["size"], f[error_name]) for f in functions]


def test_keeps_only_individuals_nothing_beats_on_both_size_and_error():
    data = [individual(5, 0.5), individual(3, 0.9), individual(7, 0.6), individual(9, 0.1), individual(3, 1.2)]

    assert pairs(Model().filter_best_functions(data)) == [(3, 0.9), (5, 0.5), (9, 0.1)]


def test_a_larger_individual_with_the_same_error_is_dropped():
    assert pairs(Model().filter_best_functions([individual(3, 0.5), individual(4, 0.5)])) == [(3, 0.5)]


def test_empty():
    assert Model().filter_best_functions([]) == []


def test_non_finite_errors_never_reach_the_front():
    data = [individual(1, float("nan")), individual(2, float("inf")), individual(3, 0.5)]

    assert pairs(Model().filter_best_functions(data)) == [(3, 0.5)]


def test_test_data_ranks_by_test_error():
    data = [individual(3, 0.9, test_error=0.2), individual(5, 0.1, test_error=0.7)]

    assert pairs(Model().filter_best_functions(data, "test"), "test_error") == [(3, 0.2)]


def test_the_front_spans_all_processes():
    model = Model()
    model.register_process(0)
    model.register_process(1)
    model.add_individuals(0, [individual(3, 0.9), individual(9, 0.5)])
    model.add_individuals(1, [individual(5, 0.3), individual(4, 1.0)])

    assert pairs(model.update_best_functions()) == [(3, 0.9), (5, 0.3)]


def test_individuals_of_a_later_batch_join_the_front_of_a_process():
    model = Model()
    model.register_process(0)
    model.add_individuals(0, [individual(9, 0.5)])
    model.add_individuals(0, [individual(3, 0.5), individual(5, 0.1)])

    assert pairs(model.update_best_functions()) == [(3, 0.5), (5, 0.1)]


def test_the_test_front_shows_test_errors_and_leaves_the_train_front_alone():
    model = Model()
    model.register_process(0)
    model.add_individuals(0, [individual(3, 0.9, test_error=0.2)])

    model.data_type = "test"
    assert pairs(model.update_best_functions()) == [(3, 0.2)]

    model.data_type = "train"
    assert pairs(model.update_best_functions()) == [(3, 0.9)]


def test_an_individual_without_a_test_error_stays_off_the_test_front():
    model = Model()
    model.register_process(0)
    model.add_individuals(0, [individual(3, 0.9), individual(5, 0.1, test_error=0.2)])

    model.data_type = "test"
    assert pairs(model.update_best_functions()) == [(5, 0.2)]
