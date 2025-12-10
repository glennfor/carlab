from src.com.xbee import XBeeCommunicator
from src.actions.car import Car
from src.asr.transcriber import Transcriber
from src.llm.google import GoogleLLM
from src.tts.vocalizer import Vocalizer
from src.vision.aruco_follower import ArUcoFollower
from src.actions.executor import Executor

from typing import Any, Callable, Dict, List, Optional
import os
import json


class Orchestrator:
    def __init__(self):
        self.function_map_list = self._load_config('functions.json')
        self.car = Car()
        self.aruco_follower = ArUcoFollower(car=self.car, marker_id=0, target_distance=0.15)
        self.transcriber = Transcriber(device_index=2)
        self.vocalizer = Vocalizer()
        self.google_llm = GoogleLLM(functions=self.function_map_list,)
        self.xbee_communicator = XBeeCommunicator()
        self.executor = Executor(car=self.car, 
                                follower=self.aruco_follower, 
                                vocalizer=self.vocalizer, 
                                llm=self.google_llm, 
                                config=self.function_map_list
                                )

    def start(self):
        self.executor.start()
        # self.aruco_follower.start()
        self.vocalizer.run()
        # self.google_llm.start()
        # self.xbee_communicator.start()
        self.transcriber.run()
        self.transcriber.set_command_callback(self.executor.add_command)
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load function mappings from config.json."""
        config_path = os.path.join(
            # os.path.dirname(os.path.dirname(__file__)),
            os.path.dirname(__file__),
            path
        )
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {config_path} not found. Using defaults.")
            return {"function_mappings": {}, "subsystems": {}}

    def stop(self):
        self.aruco_follower.stop()
        self.transcriber.stop()
        self.vocalizer.stop()
        self.google_llm.stop()
        self.xbee_communicator.stop()