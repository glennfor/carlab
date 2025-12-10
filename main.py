import time

from orchestrator import Orchestrator

# error indicator? send if problem
if __name__ == '__main__':
    orchestrator = Orchestrator()
    orchestrator.start()
    print('='*50)
    print('[ON] - All Up and Running')
    print(':'*60)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        orchestrator.stop()
    print('[Done] - Done running')