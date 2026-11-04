import collections
import os
import xml.etree.ElementTree as ET

import pytest

from models.config import ALL_FUNCTIONS, EVALUATION_POPULATION_SIZE, ConfigurationManager
from models.main import Model
from utils import paths

TEMPLATES = ["srmGP.txt", "srmGEP.txt", "srmAP.txt", "srm_eval.txt"]


def template_bytes():
    return {name: open(paths.resource_path("srm", name), "rb").read() for name in TEMPLATES}


def entry(root, key):
    return [element.text for element in root.iter("Entry") if element.get("key") == key]


def generated(model, process_id=0, is_test=False):
    model.prepare_run()
    path = model.create_process_config(process_id, is_test=is_test)
    return ET.parse(path).getroot()


@pytest.fixture
def model():
    model = Model()
    model.set_input_path(paths.resource_path("srm", "data_2var.txt"))
    model.set_function_set("+ - * /")
    model.set_terminal_set("x1 x2 [-1 1]")
    return model


@pytest.fixture
def gp(model, monkeypatch):
    monkeypatch.setattr("models.config.choose_random_element_with_probability", lambda choices: choices[0][0])
    return model


@pytest.fixture
def gep(model, monkeypatch):
    monkeypatch.setattr("models.config.choose_random_element_with_probability", lambda choices: choices[1 if len(choices) > 1 else 0][0])
    return model


def test_paths_in_a_parameter_file_are_relative_to_the_temp_directory(gp):
    root = generated(gp)

    assert entry(root, "input_file") == ["train.txt"]
    assert entry(root, "bestfile") == [os.path.join("0", "best.txt")]
    assert entry(root, "log.filename") == [os.path.join("0", "log.txt")]


def test_values_from_the_gui_reach_the_parameter_file_without_apply(gp):
    gp.set_variable_with_path("ECF/Registry/Entry/term.maxgen", "77")
    gp.set_variable("search_metric", "mean_absolute_error")
    gp.set_variable("linear_scaling", "false")

    root = generated(gp)

    assert entry(root, "term.maxgen") == ["77"]
    assert entry(root, "error_metric") == ["mean_absolute_error"]
    assert entry(root, "linear_scaling") == ["false"]
    assert entry(root, "functionset") == ["+ - * /"]


def test_an_empty_gui_value_keeps_the_template_value(gp):
    gp.set_variable_with_path("ECF/Registry/Entry/term.maxgen", "")

    assert entry(generated(gp), "term.maxgen") == ["1000"]


@pytest.mark.parametrize("variables,depth", [("x1", 5), ("x1 x2 x3 x4", 6), (" ".join(f"x{i}" for i in range(1, 17)), 8)])
def test_tree_depth_follows_the_variable_count(gp, variables, depth):
    gp.set_terminal_set(variables)

    assert entry(generated(gp), "maxdepth") == [str(depth)]


def test_ap_dimension_follows_the_variable_count(model, monkeypatch):
    monkeypatch.setattr("models.config.choose_random_element_with_probability", lambda choices: choices[-1][0])
    model.set_terminal_set("x1 x2 x3 x4")

    root = generated(model)

    assert entry(root, "dimension") == ["12"]
    assert entry(root, "functionset") == ["+ - * /", "+ - * /"]


def test_templates_are_drawn_at_the_agreed_probabilities(model):
    draws = collections.Counter()
    for _ in range(3000):
        model.create_process_config(0)
        draws[os.path.basename(model.config_manager.configurations[0].template_path)] += 1

    assert 0.76 < draws["srmGP.txt"] / 3000 < 0.84
    assert 0.07 < draws["srmGEP.txt"] / 3000 < 0.13
    assert 0.07 < draws["srmAP.txt"] / 3000 < 0.13


def test_linking_functions_stay_inside_the_function_set(gep):
    gep.set_function_set("+ * /")

    assert entry(generated(gep), "linkingfunctions") == ["+ *"]


def test_gep_without_any_linking_function_falls_back_to_gp(gep):
    gep.set_function_set("sin cos")
    gep.prepare_run()
    gep.create_process_config(0)

    assert os.path.basename(gep.config_manager.configurations[0].template_path) == "srmGP.txt"


def test_an_evaluation_run_can_read_any_individual(model):
    model.set_function_set("sin")

    root = generated(model, "eval", is_test=True)

    assert set(entry(root, "functionset")[0].split()) >= set(ALL_FUNCTIONS)
    assert entry(root, "linear_scaling") == ["false"]
    assert entry(root, "input_file") == ["test.txt"]


def test_a_test_set_evaluation_turns_linear_scaling_off(model):
    root = generated(model, 0, is_test=True)

    assert entry(root, "linear_scaling") == ["false"]
    assert entry(root, "bestfile") == [os.path.join("0", "best_test.txt")]


def test_error_weights_use_the_split_file(gp, tmp_path):
    gp.set_error_path(str(tmp_path / "weights.txt"))

    assert entry(generated(gp), "error_weights.file") == ["train_weights.txt"]
    assert entry(generated(gp, 0, is_test=True), "error_weights.file") == ["test_weights.txt"]


def test_no_error_weights_entry_unless_a_file_was_selected(gp):
    assert entry(generated(gp), "error_weights.file") == []


def test_apply_saves_for_the_user_and_leaves_the_templates_alone(gp):
    before = template_bytes()
    gp.set_variable_with_path("ECF/Registry/Entry/term.maxgen", "77")
    gp.set_input_path("/somewhere/else/data.txt")

    gp.update_default_parameters_file()

    assert template_bytes() == before
    saved = ET.parse(os.path.join(paths.saved_parameters_dir(), "srmGP.txt")).getroot()
    assert entry(saved, "term.maxgen") == ["77"]


def test_saved_values_are_the_initial_values_of_the_next_session(gp):
    gp.set_variable_with_path("ECF/Registry/Entry/term.maxgen", "77")
    gp.update_default_parameters_file()

    next_session = Model()

    assert next_session.config_manager.get_current_param_value("ECF/Registry/Entry/term.maxgen") == "77"
    assert next_session.get_current_function_set() == "+ - * /"


def test_initial_values_come_from_the_template_when_nothing_was_saved():
    model = Model()

    assert model.get_current_terminal_set() == "x1 x2 [-1 1]"
    assert model.get_current_input_path() == paths.resource_path("srm", "data_2var.txt")


def test_manual_edit_is_saved_for_the_user_and_read_back():
    manager = ConfigurationManager()
    before = template_bytes()

    manager.save_manual_parameters(manager.read_manual_parameters().replace(">1000<", ">55<"))

    assert template_bytes() == before
    assert manager.get_current_param_value("ECF/Registry/Entry/term.maxgen") == "55"
    assert ">55<" in manager.read_manual_parameters()


def test_manual_edit_with_broken_xml_is_refused():
    manager = ConfigurationManager()

    with pytest.raises(ValueError):
        manager.save_manual_parameters("<ECF><oops")

    assert not os.path.exists(manager.saved_path("srmGP.txt"))


def test_an_unreadable_saved_file_falls_back_to_the_template():
    manager = ConfigurationManager()
    with open(manager.saved_path("srmGP.txt"), "w") as file:
        file.write("<ECF><oops")

    assert manager.get_current_param_value("ECF/Registry/Entry/term.maxgen") == "1000"


def test_run_settings_are_checked_before_a_run(model):
    model.load_input_data()
    assert model.validate_run_settings() is None

    model.set_terminal_set("")
    assert "terminal set" in model.validate_run_settings()

    model.set_terminal_set("x1")
    model.set_function_set("")
    assert "function set" in model.validate_run_settings()

    model.set_function_set("- /")
    assert "Linear scaling" in model.validate_run_settings()

    model.set_variable("linear_scaling", "false")
    assert model.validate_run_settings() is None


def test_an_unreadable_input_file_stops_a_run(model, tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("not\tnumbers\n")
    model.set_input_path(str(bad))
    model.load_input_data()

    assert "could not be read" in model.validate_run_settings()


def test_evaluation_uses_a_small_population(model):
    model.set_variable_with_path("ECF/Registry/Entry/population.size", "5000")

    assert entry(generated(model, "eval", is_test=True), "population.size") == [str(EVALUATION_POPULATION_SIZE)]
    assert entry(generated(model, 0), "population.size") == ["5000"]


def test_every_process_and_every_restart_gets_its_own_seed(gp):
    gp.thread_num = 2
    gp.prepare_run()
    paths_by_id = {id: gp.create_process_config(id) for id in (0, 1)}

    seeds = []
    for _ in range(3):
        for id, path in paths_by_id.items():
            gp.config_manager.set_new_seed(id)
            seeds += entry(ET.parse(path).getroot(), "randomizer.seed")

    assert len(set(seeds)) == 6
    assert "0" not in seeds
    assert all(0 < int(seed) < 2**31 for seed in seeds)


def test_a_seed_the_user_chose_stays(gp):
    gp.set_variable_with_path("ECF/Registry/Entry/randomizer.seed", "42")
    gp.prepare_run()
    path = gp.create_process_config(0)

    gp.config_manager.set_new_seed(0)

    assert entry(ET.parse(path).getroot(), "randomizer.seed") == ["42"]


def test_a_run_keeps_its_parameters_when_the_input_panel_changes(gp, tmp_path):
    gp.set_error_path(str(tmp_path / "weights.txt"))
    gp.prepare_run()

    gp.set_variable("search_metric", "mean_absolute_error")
    gp.set_function_set("sin")
    gp.params.pop("ECF/Registry/Entry/error_weights.file")
    root = ET.parse(gp.create_process_config("eval", is_test=True)).getroot()

    assert entry(root, "error_metric") == ["mean_square_error"]
    assert entry(root, "error_weights.file") == ["test_weights.txt"]


def test_apply_saves_paths_inside_the_app_as_relative(gp):
    """A packaged app unpacks to a new place on each launch."""
    gp.set_input_path(paths.resource_path("srm", "data_2var.txt"))

    gp.update_default_parameters_file()

    saved = ET.parse(os.path.join(paths.saved_parameters_dir(), "srmGP.txt")).getroot()
    assert entry(saved, "input_file") == ["srm/data_2var.txt"]
    assert Model().get_current_input_path() == paths.resource_path("srm", "data_2var.txt")


def test_apply_keeps_a_users_own_file_absolute(gp, tmp_path):
    own_file = str(tmp_path / "data.txt")
    gp.set_input_path(own_file)

    gp.update_default_parameters_file()

    assert Model().get_current_input_path() == own_file


@pytest.mark.parametrize("old,new,missing", [
    ('<Entry key="functionset">- / + log *</Entry>', "", "functionset"),
    ('<Entry key="terminalset">x1 x2 [-1 1]</Entry>', "", "terminalset"),
    ('<Entry key="functionset">- / + log *</Entry>', '<Entry key="functionset"> </Entry>', "functionset"),
])
def test_manual_edit_without_a_required_entry_is_refused(old, new, missing):
    manager = ConfigurationManager()
    text = manager.read_manual_parameters()
    assert old in text

    with pytest.raises(ValueError, match=missing):
        manager.save_manual_parameters(text.replace(old, new))

    assert not os.path.exists(manager.saved_path("srmGP.txt"))


@pytest.mark.parametrize("content", [
    '<ECF><Registry/></ECF>',
    '<ECF><Genotype><Tree><Entry key="functionset">+</Entry><Entry key="terminalset">x1</Entry></Tree></Genotype></ECF>',
])
def test_a_saved_file_the_app_cannot_use_is_ignored(content):
    manager = ConfigurationManager()
    with open(manager.saved_path("srmGP.txt"), "w") as file:
        file.write(content)

    model = Model()

    assert model.get_current_function_set() == "- / + log *"
    assert model.get_current_terminal_set() == "x1 x2 [-1 1]"


def test_a_saved_error_metric_is_a_current_value():
    manager = ConfigurationManager()
    manager.save_manual_parameters(manager.read_manual_parameters().replace("mean_square_error", "mean_absolute_error"))

    assert Model().get_current_variable("search_metric") == "mean_absolute_error"


def test_an_old_front_does_not_leak_into_a_run_with_fewer_processes(model):
    model.thread_num = 2
    model.prepare_run()
    model.add_individuals(1, [{"size": 1, "error": 0.1, "function": "old"}])

    model.thread_num = 1
    model.prepare_run()

    assert model.update_best_functions() == []
    assert list(model.process_states) == [0]


def test_a_one_row_data_file_keeps_its_shape(tmp_path):
    data = tmp_path / "data.txt"
    data.write_text("1\t2\t3\n")

    assert Model().load_data(str(data)) == [[1.0], [2.0], [3.0]]


def test_a_one_row_test_set_can_be_plotted(model, tmp_path):
    data = tmp_path / "data.txt"
    data.write_text("".join(f"{i}\t{i + 1}\t{i + 2}\n" for i in range(5)))
    model.set_input_path(str(data))
    model.set_variable("train_test_split", 0.8)
    model.set_variable("test_sample", "sequential")

    model.split_train_test()
    model.plot_x_index = 0

    assert model.get_plot_data("test") == ([4.0], [6.0])


def test_the_plot_falls_back_to_row_numbers_for_a_variable_the_data_lacks(model):
    model.test_input_data = [[1.0, 2.0], [3.0, 4.0]]
    model.plot_x_index = 1

    assert model.get_plot_data("test") == ([0, 1], [3.0, 4.0])
