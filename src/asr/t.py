from pipeline import ASR


asr = ASR(
    wake_word="hey pi",
    whisper_model="ggml-base.en.bin",
    device_index=0  # SPH0645 I2S mic
)

if __name__ == '__main__':
    print('Testing ASR')
    asr.run()
    print('test done')