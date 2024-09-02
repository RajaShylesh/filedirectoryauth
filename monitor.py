import os
import time
import threading
import getpass
import requests

class Monitor:
    def __init__(self, directory, unauthorized_users):
        self.directory = directory
        self.unauthorized_users = unauthorized_users
        self.snapshot = self.take_snapshot()

    def take_snapshot(self):
        return {f: os.stat(os.path.join(self.directory, f)) for f in os.listdir(self.directory)}

    def monitor(self):
        while True:
            new_snapshot = self.take_snapshot()
            added = [f for f in new_snapshot if f not in self.snapshot]
            removed = [f for f in self.snapshot if f not in new_snapshot]
            modified = [f for f in new_snapshot if f in self.snapshot and new_snapshot[f].st_mtime != self.snapshot[f].st_mtime]

            user = getpass.getuser()
            for f in added:
                if user not in self.unauthorized_users:
                    print(f"Unauthorized access detected! User: {user}, Event: created, Path: {os.path.join(self.directory, f)}")
                    requests.get("http://localhost:5000/monitor")  # Send request to /monitor route
                else:
                    print(f"Authorized event: User: {user}, Event: created, Path: {os.path.join(self.directory, f)}")

            for f in removed:
                if user not in self.unauthorized_users:
                    print(f"Unauthorized access detected! User: {user}, Event: deleted, Path: {os.path.join(self.directory, f)}")
                    requests.get("http://localhost:5000/monitor")  # Send request to /monitor route
                else:
                    print(f"Authorized event: User: {user}, Event: deleted, Path: {os.path.join(self.directory, f)}")

            for f in modified:
                if user not in self.unauthorized_users:
                    print(f"Unauthorized access detected! User: {user}, Event: modified, Path: {os.path.join(self.directory, f)}")
                    requests.get("http://localhost:5000/monitor")  # Send request to /monitor route
                else:
                    print(f"Authorized event: User: {user}, Event: modified, Path: {os.path.join(self.directory, f)}")

            self.snapshot = new_snapshot
            time.sleep(1)

def start_monitoring(directory, unauthorized_users):
    monitor = Monitor(directory, unauthorized_users)
    thread = threading.Thread(target=monitor.monitor)
    thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        thread.join()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    monitored_directory = "./monitored"
    unauthorized_users = ["unauthorized_user1", "unauthorized_user2"]
    start_monitoring(monitored_directory, unauthorized_users)