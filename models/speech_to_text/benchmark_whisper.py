import whisper
import time
import os
import json
import jiwer  # pip install jiwer

def transcribe(file, model_name="base",output_dir="interface/backend/outputs/stt"):
    # loading model
    start_load = time.time()
    model = whisper.load_model(model_name)
    end_load = time.time()
    load_time = end_load-start_load

    # transcription
    start_transcribe = time.time()
    result = model.transcribe(file)
    end_transcribe = time.time()
    transcription_time = end_transcribe-start_transcribe

    # statistics
    stats = {}
    stats["load_time"]=load_time
    stats["transcription_time"]=transcription_time
    stats["total_process_time"]=load_time+transcription_time
    stats["model_used"]=model_name

    file_name = os.path.splitext(os.path.basename(file))[0]
    # create outputs dir
    output_dir = os.path.join(output_dir, file_name)
    os.makedirs(output_dir, exist_ok=True)
    
    txt_path = os.path.join(output_dir, f"{file_name}.txt")
    json_path = os.path.join(output_dir, f"{file_name}.json")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result["text"])
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)

    return result["text"], stats

if __name__ == '__main__':
    # --- CONFIGURATION DU BENCHMARK ---
    audio_file = "test_poeme_anglais.wav"
    # /!\ REMPLACE PAR LE VRAI TEXTE DU POÈME /!\
    reference_text = """Two roads diverged in a yellow wood,
                        And sorry I could not travel both
                        And be one traveler, long I stood
                        And looked down one as far as I could
                        To where it bent in the undergrowth;"""
    
    models_to_test = ["tiny", "base"]
    iterations = 10
    results_file = "benchmark_whisper.txt"

    with open(results_file, "w", encoding="utf-8") as f:
        f.write(f"=== BENCHMARK WHISPER : {audio_file} ===\n\n")

        for model_name in models_to_test:
            f.write(f"--- MODEL: {model_name} ---\n")
            print(f"Test of model: {model_name}...")
            
            model_stats = []
            
            for i in range(iterations):
                print(f"  Iteration {i+1}/{iterations}...")
                text, stats = transcribe(audio_file, model_name=model_name, output_dir="benchmark")
                
                # Calculate WER
                current_wer = jiwer.wer(reference_text.lower(), text.lower())
                stats["wer"] = current_wer
                model_stats.append(stats)
                
                # Write iteration details
                f.write(f"Iteration {i+1} : Temps = {stats['transcription_time']:.2f}s | WER = {current_wer:.4f}\n")

            # Calculate averages
            avg_load = sum(s["load_time"] for s in model_stats) / iterations
            avg_transcribe = sum(s["transcription_time"] for s in model_stats) / iterations
            avg_wer = sum(s["wer"] for s in model_stats) / iterations
            accuracy = (1 - avg_wer) * 100

            # final summary
            summary = (
                f"\n> AVERAGES FOR {model_name.upper()}:\n"
                f"  - Load time: {avg_load:.2f}s\n"
                f"  - Transcription time: {avg_transcribe:.2f}s\n"
                f"  - Average WER: {avg_wer:.4f}\n"
                f"  - Estimated accuracy: {accuracy:.2f}%\n"
                f"{'='*40}\n\n"
            )
            f.write(summary)
            print(f"Finished for {model_name}.\n")

    print(f"Benchmark saved: {results_file}")