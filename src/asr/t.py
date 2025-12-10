from pipeline import ASR


asr = ASR(
    wake_word="hey pi",
    whisper_model="base.en",
    device_index=1  
)

if __name__ == '__main__':
    print('Testing ASR')
    asr.run()
    print('test done')