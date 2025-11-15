"""LLM inference service using llama.cpp."""
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
    """Wrapper for llama.cpp inference engine."""

    def __init__(self):
        """Initialize LLM engine."""
        self.model: Optional[Llama] = None
        self.model_loaded = False
        self.model_path = settings.MODEL_PATH

    def load_model(self) -> bool:
        """Load the LLM model."""
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
                verbose=False
            )
            self.model_loaded = True
            print("Model loaded successfully.")
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            self.model_loaded = False
            return False

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> str | Iterator[str]:
        """Generate text from prompt."""
        if not self.model_loaded or not self.model:
            # Return mock response if model not loaded
            return self._mock_generate(prompt, stream)

        try:
            output = self.model(
                prompt,
                max_tokens=max_tokens or settings.MODEL_MAX_TOKENS,
                temperature=temperature or settings.MODEL_TEMPERATURE,
                top_p=settings.MODEL_TOP_P,
                echo=False,
                stream=stream,
                stop=["</s>", "<|user|>", "<|system|>", "\nUser:", "\nAI:", "\nAssistant:", "User:", "AI:"],  # Stop tokens
                repeat_penalty=1.1  # Penalize repetition to avoid dialogue loops
            )

            if stream:
                return self._stream_output(output)
            else:
                response = output['choices'][0]['text'].strip()
                # Remove dialogue prefixes if model generates them
                response = self._clean_response(response)
                return response

        except Exception as e:
            print(f"Generation error: {e}")
            return f"Error generating response: {str(e)}"

    def _stream_output(self, output) -> Iterator[str]:
        """Stream output tokens."""
        buffer = ""
        first_token = True
        for chunk in output:
            token = chunk['choices'][0]['text']
            if token:
                buffer += token
                # Clean first token if it starts with dialogue prefix
                if first_token:
                    buffer = self._clean_response(buffer)
                    if buffer:
                        yield buffer
                        buffer = ""
                        first_token = False
                else:
                    yield token

    def _clean_response(self, text: str) -> str:
        """Remove dialogue prefixes from model output."""
        # Remove common dialogue prefixes
        prefixes = ["AI:", "AI :", "Assistant:", "Assistant :", "A:", "A :", "User:", "User :"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].lstrip()
                break
        return text

    def _mock_generate(self, prompt: str, stream: bool) -> str | Iterator[str]:
        """Generate mock response when model not available."""
        # Extract user query from prompt
        user_query = "your question"
        if "<|user|>" in prompt:
            parts = prompt.split("<|user|>")
            if len(parts) > 1:
                last_user_msg = parts[-1].split("</s>")[0].strip()
                if last_user_msg:
                    user_query = last_user_msg[:50]

        response = f"[MOCK MODE] You asked: '{user_query}'. The actual LLM model is not loaded. To use a real model, please download a GGUF file to ./models/tinyllama-1.1b-chat-q4.gguf"

        if stream:
            # Simulate token-by-token streaming
            words = response.split(' ')
            def word_generator():
                for i, word in enumerate(words):
                    # Add small delay to simulate real generation
                    time.sleep(0.05)  # 50ms delay per word
                    if i == 0:
                        yield word
                    else:
                        yield ' ' + word
            return word_generator()
        return response

    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "model_path": self.model_path,
            "model_loaded": self.model_loaded,
            "n_ctx": settings.MODEL_N_CTX,
            "n_threads": settings.MODEL_N_THREADS,
            "n_gpu_layers": settings.MODEL_N_GPU_LAYERS,
            "temperature": settings.MODEL_TEMPERATURE,
            "top_p": settings.MODEL_TOP_P,
            "max_tokens": settings.MODEL_MAX_TOKENS
        }


class ModelInferenceService:
    """High-level service for LLM inference with caching."""

    def __init__(self, cache_manager, llm_engine: LLMEngine):
        """Initialize inference service."""
        self.cache_manager = cache_manager
        self.llm_engine = llm_engine

    def infer(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_cache: bool = True
    ) -> tuple[str, bool]:
        """
        Run inference with optional caching.

        Returns:
            tuple: (response, cached)
        """
        # Check cache first
        if use_cache:
            cached_response = self.cache_manager.get(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            if cached_response:
                return cached_response, True

        # Generate response
        response = self.llm_engine.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False
        )

        # Cache the response
        if use_cache and isinstance(response, str):
            self.cache_manager.set(
                prompt,
                response,
                max_tokens=max_tokens,
                temperature=temperature
            )

        return response, False

    def stream_infer(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Iterator[str]:
        """
        Stream inference response (no caching for streams).
        """
        return self.llm_engine.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        )
