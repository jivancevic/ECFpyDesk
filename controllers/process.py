import subprocess
import signal
import time
import threading
from utils.publisher import Publisher

class ProcessManager(Publisher):
    REFRESH_RATE = 1

    def __init__(self, executable_path, parameters_paths=None, output_handler=None):
        super().__init__()
        self.executable_path = executable_path
        print(f"Parameters_path: {parameters_paths}")
        self.parameters_paths = []
        self.parameters_paths.append(parameters_paths)
        print(f"Parameters_path: {self.parameters_paths}")
        self.output_handler = output_handler
        self.process = {}
        self.process_thread = {}
        self.running = False
        self.update_timer = None
        self.thread_num = 1

    def set_thread_num(self, thread_num):
        self.thread_num = thread_num

    def set_parameters_paths(self, parameters_paths):
        self.parameters_paths = self.parameters_paths.append(parameters_paths)

    def start_process(self, id="train"):
        self.running = True
        self.process_thread[id] = threading.Thread(target=self.run_process_loop)
        self.process_thread[id].start()
        self.start_update_timer()

    def run_process_loop(self):
        while self.running:
            self.invoke_callback('pre_process_start')
            print(f"Starting process {self.thread_num}...")
            print(self.parameters_paths)
            self.run_train_process(self.executable_path, self.parameters_paths[self.thread_num-1])
            # Check if the process should continue running or if a stop has been requested
            if not self.running:
                break  # Exit the loop if the process is flagged to stop
            print("Restarting the process...")
            time.sleep(0.2)

    def run_train_process(self, executable_path, parameters_path):
        # Run the executable with subprocess
        self.running = True
        id = "train"

        try:
            self.run_process(executable_path, parameters_path, id=id)
        except Exception as e:
            print(f"Error running ECF process: {e}")    
        finally:
            if self.process[id]:
                # Cleanup the process if it hasn't exited yet
                self.process[id].terminate()
                self.process[id].wait()

            # Cancel the update timer safely
            if hasattr(self, 'update_timer'):
                self.update_timer.cancel()

            self.invoke_callback('timer_finished')
            del self.process[id]

    def run_test_process(self, executable_path=None, parameters_path=None, individual_path=None):
        if executable_path is None:
            executable_path = self.executable_path
        if parameters_path is None:
            parameters_path = self.parameters_paths[self.thread_num]

        id = "test"
        try:
            print(f"Running test process, executable: {executable_path}, parameters: {parameters_path}, individual: {individual_path}")
            self.run_process(executable_path, parameters_path, individual_path, id=id)
        except Exception as e:
            print(f"Error running ECF process: {e}")    
        finally:
            if self.process[id]:
                # Cleanup the process if it hasn't exited yet
                self.process[id].terminate()
                self.process[id].wait()
                del self.process[id]

    def run_process(self, *args, **kwargs):
        try:
            print(f"Running process with args: {args}")
            id = kwargs.get('id', 'train')
            print(f"Running process with id: {id}")
            self.process[id] = subprocess.Popen(
                [*args],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            while self.running and self.process[id].poll() is None:
                output = self.process[id].stdout.readline()
                if output and len(args) == 2:
                    self.output_handler(output)
                    pass
                else:
                    time.sleep(1)
        except Exception as e:
            print(f"Error running ECF process: {e}")
            raise e

    def pause_process(self, id="train"):
        self.running = False
        if self.process[id]:
            self.process[id].send_signal(signal.SIGSTOP)

    def continue_process(self, id="train"):
        self.running = True
        if self.process[id]:
            self.process[id].send_signal(signal.SIGCONT)

    def stop_process(self, id="train"):
        """Gracefully stop the process if it's running."""
        if self.process[id]:
            try:
                # Attempt to terminate the process gracefully
                self.process[id].terminate()
                # Wait briefly for the process to terminate
                self.process[id].wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                # If the process does not terminate within the timeout, kill it
                print("Process did not terminate gracefully, killing it.")
                self.process[id].kill()
            except Exception as e:
                print(f"Error stopping the process: {e}")
            finally:
                # Ensure all internal flags and states are reset
                self.running = False
                del self.process[id]

                if self.process_thread[id] and self.process_thread[id].is_alive():
                    # Optionally join the thread if it is still running
                    self.process_thread[id].join()
                del self.process_thread[id]

                if self.update_timer:
                    self.update_timer.cancel()  # Stop the update timer

    def cleanup_process(self, id="train"):
        """Ensure the process is terminated and resources are cleaned up."""
        if self.process[id]:
            self.process[id].terminate()
            self.process[id].wait()
            del self.process[id]

    def start_update_timer(self):
        """Starts a timer that updates the solutions frame every second."""
        self.update_timer = threading.Timer(self.REFRESH_RATE, lambda event_name='timer_finished': self.invoke_callback(event_name))
        self.update_timer.start()