import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from datasets import load_dataset
import torchaudio
class Whisper:
     def generate_response(self,user_audio_path):
        print("in whisper: "+user_audio_path)
        audio_path = r"C:\backup\guc\bachelor\backend\temp_audio.wav"
        waveform, sample_rate = torchaudio.load(audio_path)

        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        model_id = "openai/whisper-large-v3-turbo"

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        model.to(device)

        processor = AutoProcessor.from_pretrained(model_id)

        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=device,
        )

        # dataset = load_dataset("distil-whisper/librispeech_long", "clean", split="validation")
        # sample = dataset[0]["audio"]
        # Hugging Face expects a dictionary like this:
        sample = {
            "array": waveform.squeeze().numpy(),  # Convert to 1D NumPy array
            "sampling_rate": sample_rate
        }

        result = pipe(sample,generate_kwargs={"language": "english"})#, return_timestamps=True
        # print("Detected language:", result.get("language", "unknown"))
        return result["text"]


# import torch
# print("Torch version:", torch.__version__)
# print("CUDA available:", torch.cuda.is_available())
# print("CUDA version:", torch.version.cuda)
# print("Device name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU found")

# very important
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

