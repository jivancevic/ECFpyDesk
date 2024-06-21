import subprocess
import signal
import time
import threading

class ProcessManager:
    REFRESH_RATE = 1

    def __init__(self, executable_path, parameters_path, output_handler=None):
        self.executable_path = executable_path
        self.parameters_path = parameters_path
        self.output_handler = output_handler
        self.process = None
        self.running = False
        self.update_timer = None
        self.callbacks = {}

    def register_callback(self, name, callback):
        self.callbacks[name] = callback

    def invoke_callback(self, name, *args, **kwargs):
        if name in self.callbacks:
            self.callbacks[name](*args, **kwargs)
        else:
            print(f"No callback registered under the name: {name}")

    def start_process(self):
        self.running = True
        self.process_thread = threading.Thread(target=self.run_process_loop)
        self.process_thread.start()
        self.start_update_timer()

    def run_process_loop(self):
        while self.running:
            self.invoke_callback('pre_process_start')

            self.run_process()
            # Check if the process should continue running or if a stop has been requested
            if not self.running:
                break  # Exit the loop if the process is flagged to stop
            print("Restarting the process...")
            time.sleep(0.2)

    def run_process(self):
        # Run the executable with subprocess
        self.running = True
        try:
            self.process = subprocess.Popen(
                [self.executable_path, self.parameters_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            while self.running and self.process.poll() is None:
                output = self.process.stdout.readline()
                if output:
                    self.output_handler(output)
                else:
                    time.sleep(1)

        except Exception as e:
            print(f"Error running ECF process: {e}")
        finally:
            if self.process:
                # Cleanup the process if it hasn't exited yet
                self.process.terminate()
                self.process.wait()

            # Cancel the update timer safely
            if hasattr(self, 'update_timer'):
                self.update_timer.cancel()

            self.invoke_callback('timer_finished')
            self.process = None # Reset process to None to ensure it can be restarted

    def pause_process(self):
        self.running = False
        if self.process:
            self.process.send_signal(signal.SIGSTOP)

    def continue_process(self):
        self.running = True
        if self.process:
            self.process.send_signal(signal.SIGCONT)

    def stop_process(self):
        """Gracefully stop the process if it's running."""
        if self.process:
            try:
                # Attempt to terminate the process gracefully
                self.process.terminate()
                # Wait briefly for the process to terminate
                self.process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                # If the process does not terminate within the timeout, kill it
                print("Process did not terminate gracefully, killing it.")
                self.process.kill()
            except Exception as e:
                print(f"Error stopping the process: {e}")
            finally:
                # Ensure all internal flags and states are reset
                self.running = False
                self.process = None

                if self.process_thread and self.process_thread.is_alive():
                    # Optionally join the thread if it is still running
                    self.process_thread.join()
                self.process_thread = None

                if self.update_timer:
                    self.update_timer.cancel()  # Stop the update timer

    def cleanup_process(self):
        """Ensure the process is terminated and resources are cleaned up."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def start_update_timer(self):
        """Starts a timer that updates the solutions frame every second."""
        self.update_timer = threading.Timer(self.REFRESH_RATE, lambda event_name='timer_finished': self.invoke_callback(event_name))
        self.update_timer.start()