import whisper

def transcribe(file, model="base"):
    model = whisper.load_model(model)
    result = model.transcribe(file)
    return result["text"]

if '__main__'==__name__:
    result = transcribe("test.mp3")
    print(result)