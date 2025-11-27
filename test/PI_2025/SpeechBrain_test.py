from speechbrain.pretrained import EncoderDecoderASR

asr = EncoderDecoderASR.from_hparams(
    source="speechbrain/asr-crdnn-rnnlm-librispeech",
    savedir="tmp_asr",
    run_opts={"device":"cpu"}  # ou "cuda" si GPU
)
print(asr.transcribe_file("test_poeme_anglais.wav"))