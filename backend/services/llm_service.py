from typing import Optional, Iterator
from config import settings
import os
import time

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False


class LLMEngine:
    def __init__(self):
        self.model: Optional[Llama] = None
        self.model_loaded = False
        self.model_path = settings.MODEL_PATH

    def load_model(self) -> bool:
        if not LLAMA_CPP_AVAILABLE:
            print("llama-cpp-python not available. Model loading disabled.")
            return False

        if not os.path.exists(self.model_path):
            print(f"Model file not found: {self.model_path}")
            print("Please download a model and place it in the correct location.")
            return False

        try:
            print(f"Loading model from {self.model_path}...")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=settings.MODEL_N_CTX,
                n_threads=settings.MODEL_N_THREADS,
                n_gpu_layers=settings.MODEL_N_GPU_LAYERS,
                n_batch=settings.MODEL_N_BATCH,
                add_bos_token=True,
                verbose=True
            )
            self.model_loaded = True
            print("Model loaded successfully.")
            return True
        except Exception as e:
            import traceback
            print(f"Failed to load model: {e}")
            traceback.print_exc()
            self.model_loaded = False
            return False

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> str | Iterator[str]:

        if not self.model_loaded or not self.model:
            return self._mock_generate(prompt, stream)

        try:
            output = self.model(
                prompt,
                max_tokens=max_tokens or settings.MODEL_MAX_TOKENS,
                temperature=temperature if temperature is not None else settings.MODEL_TEMPERATURE,
                top_p=settings.MODEL_TOP_P,
                echo=False,
                stream=stream,
                stop=["<|eot_id|>"],
                repeat_penalty=1.1
            )

            if stream:
                return self._stream_output(output)
            else:
                response = output['choices'][0]['text'].strip()
                response = self._clean_response(response)
                return response

        except Exception as e:
            print(f"Generation error: {e}")
            return f"Error generating response: {str(e)}"

    def _stream_output(self, output) -> Iterator[str]:
        buffer = ""
        full_text = ""
        first_token = True

        for chunk in output:
            token = chunk['choices'][0]['text']
            if not token or token.strip().lower() in ["<think>", "</think>"]:
                continue

            full_text += token

            if first_token:
                buffer += token
                cleaned = self._clean_response(buffer)
                if cleaned:
                    yield cleaned
                buffer = ""
                first_token = False
            else:
                yield token

    def _clean_response(self, text: str) -> str:
        import re
        if not text:
            return text

        text = re.sub(r"(?is)<think>.*?</think>", "", text)
        text = re.sub(r"<\|eot_id\|>", "", text)
        text = re.sub(r"</s>", "", text)

        lines = [l.strip() for l in text.split("\n") if l.strip()]

        reasoning_markers = [
            r"let me", r"i need to", r"i remember", r"wait[, ]",
            r"first[, ]", r"maybe", r"another thing",
            r"i'm trying to", r"now,", r"let's", r"in conclusion"
        ]
        rm = re.compile(r"(?i)(" + "|".join(reasoning_markers) + ")")

        clean_lines = []
        for line in lines:
            if rm.search(line):
                continue
            clean_lines.append(line)

        final = []
        for l in clean_lines:
            if l not in final:
                final.append(l)

        return "\n".join(final).strip()

    def _mock_generate(self, prompt: str, stream: bool) -> str | Iterator[str]:
        user_query = "your question"
        marker = "<|start_header_id|>user<|end_header_id|>"
        if marker in prompt:
            parts = prompt.split(marker)
            if len(parts) > 1:
                tail = parts[-1]
                if "<|eot_id|>" in tail:
                    tail = tail.split("<|eot_id|>")[0]
                last_user_msg = tail.strip()
                if last_user_msg:
                    user_query = last_user_msg[:50]

        response = f"[MODEL NOT LOADED] Could not process: '{user_query}'."

        if stream:
            words = response.split(' ')
            def word_generator():
                for i, w in enumerate(words):
                    time.sleep(0.05)
                    yield (w if i == 0 else " " + w)
            return word_generator()

        return response

    def get_model_info(self) -> dict:
        return {
            "model_path": self.model_path,
            "model_loaded": self.model_loaded,
            "n_ctx": settings.MODEL_N_CTX,
            "n_threads": settings.MODEL_N_THREADS,
            "n_gpu_layers": settings.MODEL_N_GPU_LAYERS,
            "n_batch": settings.MODEL_N_BATCH,
            "temperature": settings.MODEL_TEMPERATURE,
            "top_p": settings.MODEL_TOP_P,
            "max_tokens": settings.MODEL_MAX_TOKENS
        }


class ModelInferenceService:
    def __init__(self, cache_manager, llm_engine: LLMEngine):
        self.cache_manager = cache_manager
        self.llm_engine = llm_engine

    def infer(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None, use_cache: bool = True) -> tuple[str, bool]:
        if use_cache:
            cached = self.cache_manager.get(prompt, max_tokens=max_tokens, temperature=temperature)
            if cached:
                return cached, True

        response = self.llm_engine.generate(prompt, max_tokens=max_tokens, temperature=temperature, stream=False)

        if use_cache and isinstance(response, str):
            self.cache_manager.set(prompt, response, max_tokens=max_tokens, temperature=temperature)

        return response, False

    def stream_infer(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Iterator[str]:
        return self.llm_engine.generate(prompt, max_tokens=max_tokens, temperature=temperature, stream=True)
