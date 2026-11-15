# Developer guide

How to get the source running, how it fits together, and how to extend it. For using the app, see the [user guide](user-guide.md). Terms such as *Process*, *Individual* and *Pareto front* are in [GLOSSARY.md](../GLOSSARY.md).

## 1. Get it running

You need Git, Python 3.14 (CI uses 3.14; the code has not been tried on other versions), CMake 3.24 or newer, and a C++ compiler: Xcode command line tools on macOS, GCC or Clang on Linux, Visual Studio 2022 on Windows. On Linux the app also needs Tk for Python (`sudo apt install python3-tk`).

```bash
git clone https://github.com/jivancevic/ECFpyDesk.git
cd ECFpyDesk
```

Build SRM, the C++ program the app drives. The binary lands in `srm/SRM` (`srm/SRM.exe` on Windows), where the app looks for it. [native/README.md](../native/README.md) has the details (Boost, Intel Macs, why runs differ between builds).

```bash
cmake -S native -B build
cmake --build build --config Release --parallel 4
python native/smoke_test.py      # python3 on systems without a `python`
```

The first configure downloads Boost (about 100 MB) unless you have Boost 1.83 or newer installed (`brew install boost`, `sudo apt install libboost-dev`). The smoke test runs a short evolution for GP, GEP and AP on the sample data.

Install the Python dependencies in a virtual environment and start the app:

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
python main.py
```

`requirements.txt` holds what the app needs, `requirements-dev.txt` adds pytest. Start the app from anywhere: it finds its own files. `venv/` and `build/` are gitignored.

### Tests

```bash
python -m pytest
```

The suite takes about half a minute. Tests that need the SRM binary skip themselves when `srm/SRM` is missing, so a checkout without a build still runs the rest. `tests/test_end_to_end.py` drives the real controller, model and SRM with stand-in widgets, and recomputes errors from the evaluated points to check them. CI (`.github/workflows/ci.yml`) builds SRM, runs the smoke test and the tests on Linux, macOS and Windows.

### Where the app keeps its files

The app never writes beside its own files. Everything it writes goes to a per-user folder:

| System | Folder |
| --- | --- |
| macOS | `~/Library/Application Support/ECFpyDesk` |
| Windows | `%LOCALAPPDATA%\ECFpyDesk` |
| Linux | `$XDG_DATA_HOME/ECFpyDesk`, or `~/.local/share/ECFpyDesk` |

Set `ECFPYDESK_DATA_DIR` to use another folder, for instance an empty one for a clean first start. Inside it, `parameters/` holds the settings saved with Apply, and `temp/` is the working folder of the SRM processes, cleared at every start. To reset the app, delete the folder.

## 2. How it fits together

The app is a Python desktop program (customtkinter) in the MVC pattern. It does not evolve anything itself: it writes parameter files, starts several SRM processes, reads their best individuals while they run, and shows the Pareto front. Plots are evaluated by SRM too, so what is plotted is exactly what SRM computes.

```
main.py                 builds Model, View and Controller and starts the window
models/
  main.py               Model: the user's choices, input data, the run's results and the Pareto front
  config.py             ConfigurationManager: reads and writes the parameter files, splits train and test
  best_file.py          parses SRM's best file and an evaluation run's output
  parameters.py         paths of the parameters the model needs by name
controllers/
  main.py               Controller: start, pause, continue, stop, collecting results, evaluating for plots
  process.py            ProcessManager: starts, suspends, resumes and kills SRM processes
  input.py, results.py, navigation.py   one controller per screen
views/
  main.py               the window; input.py, results.py, navigation.py are the screens
  base.py               shared widgets and layout constants
utils/
  parameters.py         the options the Input screen offers (functions, parameters, dropdowns, plot options)
  tooltips.py           the hover texts, and the class that shows them
  paths.py              where files are read from and written to
native/ecf, native/SRM  the C++ side, see native/README.md
srm/                    parameter file templates (srmGP, srmGEP, srmAP, srm_eval), sample data, and the built binary
config.json             path of SRM and the refresh interval of the Results screen
```

### One run, step by step

1. **Start.** `Controller.start_all_processes` splits the input into a train and a test file (rows are copied as text, so no value changes), then asks the `Model` for one parameter file per process. Each process draws its template from GP, GEP and AP at probabilities 0.8, 0.1 and 0.1, and the values on screen are written into it.
2. **Processes.** `ProcessManager` starts one SRM per parameter file in the temp folder. SRM writes its best individual to a *best file* every `log.frequency` generations, and the app keeps restarting SRM until you press Stop. Pause and continue suspend and resume the processes through `psutil` (SIGSTOP and SIGCONT on macOS and Linux, `NtSuspendProcess` on Windows). Stop kills them.
3. **Collecting.** One thread per process reads new blocks from its best file (`models/best_file.py` keeps a half-written block for the next read). With a test set, each new individual is evaluated on it by running SRM once more with the file `srm/srm_eval.txt`, because the test error is printed only on SRM's output.
4. **Showing.** A timer on the main thread, every `refresh_interval_ms` from `config.json`, builds the Pareto front across all processes and updates the list. Tk and matplotlib are touched from the main thread only.
5. **Plotting.** Selecting a row has SRM evaluate that individual on the train or test rows, and the figure is drawn from the values it returns.

SRM is started with the temp folder as its working directory and gets relative paths, so spaces or non-ASCII characters in a home folder never reach it.

### Parameter files and templates

The files in `srm/` are templates and are never modified. The app reads the user's saved copy from `parameters/` when there is a usable one, else the template, applies what is on screen, and writes the result into the temp folder. Apply saves a copy per template; "Change Manually" edits only the GP copy, so the GEP and AP templates and the evaluation file do not get a manual edit (values shown in the form do reach all of them).

Inside the XML, `ECF/Genotype/Entry/functionset` is shorthand used throughout the app for the function set of whichever genotype the template has (`Tree`, `GEPChromosome` or `APGenotype`). Parameters are addressed by a path of this form, which `ConfigurationManager.find_param_elements` understands: the element names down to the entry, then the `key`. `ECF/Registry/Entry/population.size` is `<Registry><Entry key="population.size">`.

## 3. Adding a function

Say you want to add `abs`. Functions live in two places that must agree: SRM, which evaluates them, and the app, which offers them.

**SRM side** (`native/SRM/`):

1. Write the primitive for ECF's tree. Copy `Avg.h` (header only) or `Sqrt.h` and `Sqrt.cpp`, set `name_ = "abs"` and the number of arguments in the constructor, and compute the result in `execute`.
2. Register it in `main.cpp`. Create the primitive and call `addFunction` on the genotypes that should use it: `tree` for GP, `ap` for the AP genotype and `gep` for GEP (see how `avgPrimitive` is added to each). If you add a `.cpp` file, list it in `native/SRM/CMakeLists.txt`.
3. Teach the evaluator that plots and test errors use. In `Evaluator.h` add the name to the `Functions` enum, in `Evaluator.cpp` add `funcNames.push_back("abs")` in `initFunctionNames` (in the same position as in the enum) and a `case` in `execute`. ECF already provides `+ - * / sin cos pos ifpos ifgt min max`, so only the names that are not built in need a primitive of your own.
4. If the function should print as `abs(x)` rather than infix, add its name to the list in `infixTree.h` next to `avg`, `min` and `max`.
5. Optional: SRM keeps interval-arithmetic versions of some functions (`IASqrt.*` and friends, registered on `iaTree`). Add one only if the new function should take part in that. Without it, SRM runs as before.

Rebuild with the two `cmake` commands above.

**App side**:

1. Add `("Absolute value", "abs")` to `options["Functions"]` in `utils/parameters.py`. The label is what the checkbox shows, the second value is the name SRM knows. The checkbox appears on its own, and is ticked when the saved function set contains it.
2. Add a hover text under the key `"abs"` in `utils/tooltips.py`.
3. Add the symbol to the `functionset` of the templates in `srm/` if it should be on by default.

There is no numpy version of a function to write: the plots are evaluated by SRM, so the C++ side is the single definition. (The thesis-era instruction to add a numpy function to `utils/plot.py` no longer applies; that file is gone.)

To check it, build, start the app, tick the new function and run on a data set whose target uses it. Add a case to `native/smoke_test.py` or a test if the function has a protected form (like division and logarithm do).

## 4. Adding a parameter

**A number or text field in the parameter list.** Add a pair to `options["Registry parameters"]` in `utils/parameters.py`:

```python
("Tournament size", "ECF/Algorithm/SteadyStateTournament/Entry/tsize"),
```

The first value is the label and the second is the path of the entry in the XML. The field appears with the value read from the parameter file, and what you type reaches the file of every process whose template has that element. Add a hover text under the same path as the key in `utils/tooltips.py`. A new section next to "Functions" and "Registry parameters" is a new key in the `options` dictionary, and the screen draws every section it finds (a section other than "Functions" is drawn as labelled text fields).

**A dropdown.** Add a tuple to `search_options` (or `plot_options` for the Results screen): the variable name, the label, and a list of `(label shown, value)` pairs. For a search option, the value must end up somewhere: if the variable is an entry in the parameter file, add its name and path to `param_paths` in `models/parameters.py` and `Model.set_variable` stores it there; anything else is set as an attribute of the `Model` and has to be used by whoever reads it. The hover text key is the variable name.

**Something SRM does not read yet.** Add the code to SRM first (it reads its parameters from the `Registry` through ECF's `state->getRegistry()`), then the entry to the templates in `srm/`, then expose it as above.

## 5. Conventions

- English in code, docs and UI.
- No absolute paths in the repo. A test (`tests/test_paths.py`) keeps `srm/` and `config.json` clean.
- Work goes in small pull requests; `ci` must be green. The repo's own rules are in [AGENTS.md](../AGENTS.md).
- The reason for keeping ECF and SRM in the repo is in [ADR 0001](adr/0001-vendor-ecf-and-srm-private-until-confirmed.md), and why SRM is published under MIT in [ADR 0002](adr/0002-publish-the-repo-with-srm-under-mit.md).

## 6. Releases

Pushing a tag that starts with `v` runs `.github/workflows/release.yml`. It builds both packages from the tagged commit with PyInstaller (`packaging/ECFpyDesk.spec`, driven by `packaging/build.py`, with SRM bundled), smoke-tests each one, and only then creates the GitHub Release with `ECFpyDesk-<version>-macos-arm64.zip` and `ECFpyDesk-<version>-windows-x64.zip`. A tag with a hyphen, such as `v1.0.0-rc.1`, becomes a pre-release.

```bash
git tag v1.0.0 && git push origin v1.0.0
```

The smoke test (`packaging/smoke_test.py`) unzips the package outside the repository, into a path with a space and non-ASCII characters, starts it with a fresh home folder, and reads the report of the app's built-in self-test. The self-test is also available by hand:

```bash
python main.py --self-test report.json
```

It opens the real window, presses the real Start, Stop and Select File buttons, runs GP, GEP and AP, checks the Pareto front, pause and continue, and the plot options, then writes a JSON report after every step. An error dialog, a Tk callback exception or a logged error fails it.

Hand out only packages built by CI. A package built on your own machine may need a newer system than the minimum, because it follows the Python that built it. The packages are unsigned: see the [user guide](user-guide.md#1-start-the-app) for the first-launch steps users need. Windows packages have been verified by CI only.
