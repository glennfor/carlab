# from pywhispercpp.examples.assistant import Assistant

# my_assistant = Assistant(commands_callback=print, n_threads=8)
# if __name__ == "__main__":
#     print('Should be listening now')
#     my_assistant.start()

# from whispercpp import Whisper
# import time

# w = Whisper.from_pretrained("tiny.en")

# if __name__ == '__main__':
#     print('working')
#     then = time.time()
#     text = w.transcribe(np.ones((1, 16000)))
#     then = time.time()
#     print('Took: ', now - then)
#     print('Text: ', text)


# import whisper
# import numpy as np
# import time

# model = whisper.load_model("tiny.en")

# then = time.time()
# audio = np.ones((16000,), dtype=np.float32)

# text = model.transcribe(audio)  # shape should match audio length
# now = time.time()

# print('Took:', now - then)
# print('Text:', text['text'])
