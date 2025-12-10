from src.communication.xbee import XBeeCommunicator

from src.actions.car import Car
from src.asr.transcriber import Transcriber
from src.llm.google import GoogleLLM
from src.tts.vocalizer import Vocalizer
from src.vision.aruco_follower import ArUcoFollower


class Orchestrator:
    def __init__(self):
        self.car = Car()
        self.aruco_follower = ArUcoFollower(car=self.car, marker_id=0, target_distance=0.15)
        self.transcriber = Transcriber()
        self.vocalizer = Vocalizer()
        self.google_llm = GoogleLLM()
        self.xbee_communicator = XBeeCommunicator()
        self.executor = Executor(car=self.car, follower=self.aruco_follower, vocalizer=self.vocalizer, llm=self.google_llm)

    def start(self):
        self.executor.start()
        self.aruco_follower.start()
        self.vocalizer.start()
        self.google_llm.start()
        self.xbee_communicator.start()
        self.transcriber.start()

    def stop(self):
        self.aruco_follower.stop()
        self.transcriber.stop()
        self.vocalizer.stop()
        self.google_llm.stop()
        self.xbee_communicator.stop()