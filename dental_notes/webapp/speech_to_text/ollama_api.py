import requests
import logging

logger = logging.getLogger(__name__)

class OllamaAPI:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
    def generate_summary(self, text, model="llama3"):
        try:
            prompt = f"Please summarize the following text concisely:\n\n{text}"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            logger.info(f"Sending request to Ollama API with model: {model}")
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info("Successfully received summary from Ollama")
            return result.get('response', '')
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise 