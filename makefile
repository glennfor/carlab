move:
	venv/bin/python src/actions/tests/test_movements.py
cam:
	venv/bin/python -m src.vision.aruco_follower
llm:
	venv/bin/python -m src.llm.google
sys:
	venv/bin/python main.py
snd:
	venv/bin/python -m src.tts.vocalizer
asr:
	venv/bin/python -m src.asr.transcriber
main:
	venv/bin/python main.py