import time

from orchestrator import Orchestrator

# error indicator? send if problem
if __name__ == '__main__':
    orchestrator = Orchestrator()
    orchestrator.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        orchestrator.stop()