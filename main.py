import time

from orchestrator import Orchestrator

# error indicator? send if problem
if __name__ == '__main__':
    orchestrator = Orchestrator()
    print('='*50)
    print('[ON] - All Up and Running')
    print(':'*60)
    orchestrator.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        orchestrator.stop()
    print('[Done] - Done running')