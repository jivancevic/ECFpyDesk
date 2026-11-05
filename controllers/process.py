import logging
import os
import subprocess
import threading
import psutil
from utils.publisher import Publisher

logger = logging.getLogger(__name__)

IDLE = 'idle'
RUNNING = 'running'
PAUSED = 'paused'

class ProcessManager(Publisher):
    """Runs the SRM Processes of a run.

    A run is IDLE, RUNNING or PAUSED. Each Process has a thread that keeps SRM going: when SRM
    finishes it starts again, so results keep improving until the user stops the run. Pause
    suspends SRM and holds the threads, abort kills SRM and ends them.
    """
    EVALUATION_TIMEOUT = 60  # seconds, an evaluation run normally takes milliseconds
    JOIN_TIMEOUT = 5

    def __init__(self, executable_path, working_directory=None):
        super().__init__()
        self.executable_path = executable_path
        self.working_directory = working_directory
        self.state = IDLE
        self.lock = threading.Lock()
        self.resume_event = threading.Event()
        self.processes = {}
        self.parameters_paths = []
        self.test_processes = {}
        self.process_threads = {}
        self.failed_processes = set()

    def set_parameters_paths(self, parameters_paths):
        self.parameters_paths = parameters_paths

    def active_process_count(self):
        return sum(thread.is_alive() for thread in self.process_threads.values())

    def start_all_processes(self):
        with self.lock:
            if self.state != IDLE:
                return
            self.state = RUNNING
            self.resume_event.set()
        self.failed_processes.clear()
        self.process_threads = {}
        for id, params_path in enumerate(self.parameters_paths):
            self.process_threads[id] = threading.Thread(target=self.run_process_loop, args=(id, params_path), daemon=True)
            self.process_threads[id].start()

    def run_process_loop(self, id, params_path):
        try:
            self.keep_process_running(id, params_path)
        except Exception as e:
            logger.exception(f"Process {id} ended on an error")
            self.failed_processes.add(id)
            self.invoke_callback('process_failed', id, str(e))

    def keep_process_running(self, id, params_path):
        while True:
            self.resume_event.wait()
            if self.state == IDLE:
                return
            self.invoke_callback('pre_process_start', id)
            process = self.start_train_process(id, params_path)
            if process is None:
                return
            returncode = process.wait()
            with self.lock:
                self.processes.pop(id, None)
                if self.state == IDLE:
                    return
            self.invoke_callback('process_finished', id, returncode)
            if id in self.failed_processes:
                return

    def start_train_process(self, id, params_path):
        with self.lock:
            if self.state == IDLE:
                return None
            try:
                output_path = os.path.join(os.path.dirname(params_path), 'output.txt')
                with open(output_path, 'w') as output:
                    process = self.run_process(self.executable_path, params_path, stdout=output)
            except OSError as e:
                logger.error(f"Error running train ECF process: {e}")
                self.failed_processes.add(id)
                self.invoke_callback('process_failed', id, str(e))
                return None
            self.processes[id] = process
            if self.state == PAUSED:
                self.suspend_process(process)
            return process

    def run_test_process(self, id, parameters_path, individual_path, output_path):
        """Runs SRM on one Individual and waits for it. Returns True if SRM finished normally."""
        try:
            with open(output_path, 'w') as output:
                process = self.run_process(self.executable_path, parameters_path, individual_path, stdout=output)
        except OSError as e:
            logger.error(f"Error running ECF test process {id}: {e}")
            return False

        with self.lock:
            self.test_processes[id] = process
        try:
            return process.wait(timeout=self.EVALUATION_TIMEOUT) == 0
        except subprocess.TimeoutExpired:
            logger.error(f"ECF test process {id} did not finish in {self.EVALUATION_TIMEOUT} s")
            process.kill()
            process.wait()
            return False
        finally:
            with self.lock:
                self.test_processes.pop(id, None)

    def run_process(self, *args, stdout):
        """SRM's output goes straight to a file. A pipe the app does not keep reading fills up
        after about 64 KB, and SRM then blocks forever on its next write."""
        command = [args[0]] + [self.relative_path(arg) for arg in args[1:]]
        return subprocess.Popen(
            command,
            cwd=self.working_directory,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=subprocess.STDOUT,
            # Without this a packaged Windows app opens a console for every run
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )

    def relative_path(self, path):
        if self.working_directory is None:
            return path
        return os.path.relpath(path, self.working_directory)

    def pause_all_processes(self):
        with self.lock:
            if self.state != RUNNING:
                return
            self.state = PAUSED
            self.resume_event.clear()
            for process in self.processes.values():
                self.suspend_process(process)

    def continue_all_processes(self):
        with self.lock:
            if self.state != PAUSED:
                return
            self.state = RUNNING
            for process in self.processes.values():
                self.resume_process(process)
            self.resume_event.set()

    def stop_all_processes(self):
        with self.lock:
            self.state = IDLE
            self.resume_event.set()
            # kill, not terminate: a suspended process does not act on SIGTERM until it resumes
            for process in list(self.processes.values()) + list(self.test_processes.values()):
                process.kill()
        for thread in self.process_threads.values():
            if thread is not threading.current_thread():
                thread.join(self.JOIN_TIMEOUT)

    def mark_failed(self, id):
        self.failed_processes.add(id)

    def suspend_process(self, process):
        # psutil suspends the same way on every platform: SIGSTOP on macOS and Linux,
        # NtSuspendProcess on Windows, which has no such signals
        try:
            psutil.Process(process.pid).suspend()
        except psutil.NoSuchProcess:
            pass

    def resume_process(self, process):
        try:
            psutil.Process(process.pid).resume()
        except psutil.NoSuchProcess:
            pass
