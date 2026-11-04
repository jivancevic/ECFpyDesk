import collections
import os
import xml.etree.ElementTree as ET

import pytest

from models.config import ALL_FUNCTIONS, ConfigurationManager
from models.main import Model
from utils import paths

TEMPLATES = ["srmGP.txt", "srmGEP.txt", "srmAP.txt", "srm_eval.txt"]


def template_bytes():
    return {name: open(paths.resource_path("srm", name), "rb").read() for name in TEMPLATES}


def entry(root, key):
    return [element.text for element in root.iter("Entry") if element.get("key") == key]


def generated(model, process_id=0, is_test=False):
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
