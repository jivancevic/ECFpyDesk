import subprocess
import signal
import time
import threading
from utils.publisher import Publisher

class ProcessManager(Publisher):
    REFRESH_RATE = 1

    def __init__(self, executable_path):
        super().__init__()
        self.executable_path = executable_path
        self.processes = {}
        self.parameters_paths = []
        self.test_processes = {}
        self.test_parameters_paths = []
        self.evaluation_processes = {}
        self.evaluation_processes_paths = []
        self.process_threads = {}
        self.running = {}
        self.global_running = False
        self.update_timers = {}
        self.thread_num = 1

    def set_thread_num(self, thread_num):
        self.thread_num = thread_num

    def set_parameters_paths(self, parameters_paths):
        self.parameters_paths = parameters_paths

    def set_test_parameters_paths(self, parameters_paths):
        self.test_parameters_paths = parameters_paths

    def reset_running_flags(self):
        self.running = {i: False for i in range(self.thread_num)}

    def start_all_processes(self):
        self.global_running = True
        for i, params_path in enumerate(self.parameters_paths):
            self.start_process(i, params_path)

    def start_process(self, id, params_path):
        print(f"Starting process with id: {id}")
        if id not in self.running or not self.running[id]:
            print(f"Starting process {id}")
            self.running[id] = True
            self.process_threads[id] = threading.Thread(target=self.run_process_loop, args=(id, params_path))
            self.process_threads[id].start()
            print(f"Native ID: {self.process_threads[id].native_id}.")
            self.start_update_timer(id)

    def run_process_loop(self, id, params_path):
        print(f"Running process loop with id: {id}")
        while self.global_running:
            while not self.running[id]:
                print(f"Process {id} paused, waiting...")
                time.sleep(0.2)
            self.invoke_callback('pre_process_start', id)
            self.run_train_process(self.executable_path, params_path, id)
            if not self.global_running:
                break
            time.sleep(0.2)

    def run_train_process(self, executable_path, parameters_path, id):
        # Run the executable with subprocess
        self.running[id] = True

        try:
            self.processes[id] = self.run_process(executable_path, parameters_path)
            while id in self.processes and self.processes[id].poll() is None:
                output = self.processes[id].stdout.readline()
        except Exception as e:
            print(f"Error running train ECF process: {e}")    
        finally:
            print(f"Cleaning up process {id}")
            self.running[id] = False
            if id in self.processes and self.processes[id]:
                # Cleanup the process if it hasn't exited yet
                self.processes[id].terminate()
                self.processes[id].wait()
                del self.processes[id]

            # Cancel the update timer safely
            if id in self.update_timers:
                self.update_timers[id].cancel()
            self.invoke_callback('timer_finished', id)
                

    def run_test_process(self, id, executable_path=None, parameters_path=None, individual_path=None):
        if executable_path is None:
            executable_path = self.executable_path
        if parameters_path is None:
            parameters_path = self.test_parameters_paths[id]
        if individual_path is None:
            print(f"Error running ECF test process {id}: No individual path provided")

        try:
            self.test_processes[id] = self.run_process(self.executable_path, parameters_path, individual_path)
            while self.test_processes[id].poll() is None:
                pass
        except Exception as e:
            print(f"Error running ECF test process {id}: {e}")
        finally:
            self.cleanup_process(id, is_test=True)

    def run_process(self, *args):
        try:
            return subprocess.Popen(
                [*args],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        except Exception as e:
            print(f"Error running ECF process: {e}")
            raise e

    def pause_all_processes(self):
        if self.global_running:
            self.global_running = False
            for id in range(self.thread_num):
                self.pause_process(id)

    def pause_process(self, id):
        if self.running.get(id):
            self.running[id] = False
        if id in self.processes and self.processes[id]:
            self.processes[id].send_signal(signal.SIGSTOP)
        if id in self.update_timers:
            self.update_timers[id].cancel()

    def continue_all_processes(self):
        if not self.global_running:
            self.global_running = True
            for id in range(self.thread_num):
                self.continue_process(id)

    def continue_process(self, id):
        if not self.running.get(id):
            self.running[id] = True
        if self.processes[id]:
            self.processes[id].send_signal(signal.SIGCONT)
        self.start_update_timer(id)

    def stop_all_processes(self):
        if self.global_running:
            self.global_running = False
        print(f"Thread num: {self.thread_num}")
        for id in range(self.thread_num):
            self.stop_process(id)

    def stop_process(self, id):
        self.cleanup_process(id, is_test=True)
        self.cleanup_process(id, is_test=False)
        if id in self.process_threads and self.process_threads[id].is_alive():
            self.process_threads[id].join()
            del self.process_threads[id]

    def cleanup_process(self, id, is_test=False):
        if is_test:
            self.cleanup_test_process(id)
        else:
            self.cleanup_train_process(id)

    def cleanup_train_process(self, id):
        print(f"Cleaning process {id}")
        if id in self.processes and self.processes.get(id):
            try:
                self.processes[id].terminate()
                self.processes[id].wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self.processes[id].kill()
            finally:
                if id in self.processes:
                    del self.processes[id]
        if self.update_timers.get(id):
            self.update_timers[id].cancel()
            del self.update_timers[id]
        if id in self.running:
            print(f"Cleaning running flag for process {id}")
            del self.running[id]

    def cleanup_test_process(self, id):
        print(f"Cleaning test process {id}")
        if id in self.test_processes:
            try:
                self.test_processes[id].terminate()
                self.test_processes[id].wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self.test_processes[id].kill()
            finally:
                if id in self.test_processes:
                    del self.test_processes[id]

    def start_update_timer(self, id):
        if not self.running.get(id) and not self.global_running:
            return
        if id not in self.update_timers:
            self.update_timers[id] = threading.Timer(self.REFRESH_RATE, lambda: self.invoke_callback('timer_finished', id))
            self.update_timers[id].start()
        elif not self.update_timers[id].is_alive():
            self.update_timers[id] = threading.Timer(self.REFRESH_RATE, lambda: self.invoke_callback('timer_finished', id))
            self.update_timers[id].start()