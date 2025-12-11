move:
	venv/bin/python src/actions/tests/test_movements.py
mov:
	venv/bin/python src/actions/tests/t.py
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
asr2:
	venv/bin/python -m src.asr.deepgram_transcriber
main:
	venv/bin/python main.py