from src.com.xbee import XBeeCommunicator
from src.actions.car import Car
from src.asr.transcriber import Transcriber
from src.llm.google import GoogleLLM
from src.tts.vocalizer import Vocalizer
from src.vision.aruco_follower import ArUcoFollower
from src.actions.executor import Executor
import json


class Orchestrator:
    def __init__(self):
        self.car = Car()
        self.aruco_follower = ArUcoFollower(
                                car=self.car,
                                marker_id=0,
                                target_distance=0.15,
                                # distance control
                                distance_kp=0.8,
                                distance_ki=0.05,
                                distance_kd=0.02,
                                # angle control
                                angle_kp=0.08,
                                angle_ki=0.05,
                                angle_kd=0.02,
                            )
        self.transcriber = Transcriber(device_index=2)
        self.vocalizer = Vocalizer(sample_rate=48000, device_index=3)
        # self.google_llm = GoogleLLM(functions=self.function_map_list,)
        self.xbee_communicator = XBeeCommunicator()
        self.executor = Executor(car=self.car, follower=self.aruco_follower, vocalizer=self.vocalizer)

    def start(self):
        self.executor.start()
        # self.aruco_follower.start()
        self.vocalizer.run()
        # self.google_llm.start()
        # self.xbee_communicator.start()
        self.transcriber.set_command_callback(self.executor.add_command)
        self.transcriber.run()

    def stop(self):
        self.aruco_follower.stop()
        self.transcriber.stop()
        self.vocalizer.stop()
        # self.google_llm.stop()
        # self.xbee_communicator.stop()