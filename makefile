move:
	venv/bin/python src/actions/tests/test_movements.py
cam:
	venv/bin/python -m src.vision.aruco_follower
llm:
	venv/bin/python -m src.llm.google