"""
Chat Handler - Módulo para gerar respostas naturais em chat usando LLM
Suporta múltiplas APIs: Ollama (local), Gemini, OpenAI
"""

import requests
import json
import time
import random
from loguru import logger


class ChatHandler:
    def __init__(self, config=None, input_simulator=None):
        """
        Inicializa o chat handler.
        
        Args:
            config: Dicionário de configuração com chaves 'chat'
            input_simulator: Instância de InputSimulator para digitar respostas
        """
        self.cfg = config or {}
        chat_cfg = self.cfg.get('chat', {})
        
        self.enabled = chat_cfg.get('enabled', False)
        self.provider = chat_cfg.get('provider', 'ollama')  # ollama, gemini, openai
        self.model = chat_cfg.get('model', 'llama3')
        self.api_key = chat_cfg.get('api_key', '')
        self.base_url = chat_cfg.get('base_url', 'http://localhost:11434')
        self.response_chance = float(chat_cfg.get('response_chance', 0.3))
        self.min_response_time = float(chat_cfg.get('min_response_time', 2.0))
        self.max_response_time = float(chat_cfg.get('max_response_time', 5.0))
        
        self.input_sim = input_simulator
        self.personality = chat_cfg.get('personality', 'casual')
        
        # Personalidades predefinidas
        self.personalities = {
            'casual': "Você é um jogador casual de PokeOne. Responda de forma curta, relaxada e amigável.",
            'competitive': "Você é um jogador competitivo de PokeOne. Responda com foco em estratégia e otimização.",
            'friendly': "Você é muito amigável e gosta de fazer amigos. Responda de forma calorosa e sociável.",
            'quiet': "Você é tímido e prefere respostas curtas. Use poucas palavras.",
        }
    
    def should_respond(self):
        """Decide aleatoriamente se deve responder baseado em response_chance."""
        if not self.enabled:
            return False
        return random.random() < self.response_chance
    
    def generate_response(self, text_detected):
        """
        Gera uma resposta natural para o texto detectado.
        
        Args:
            text_detected: Texto detectado no chat do jogo
            
        Returns:
            String com a resposta gerada ou None se houver erro
        """
        if not self.enabled or not text_detected:
            return None
        
        try:
            personality_prompt = self.personalities.get(
                self.personality,
                self.personalities['casual']
            )
            
            prompt = f"{personality_prompt}\n\nAlguém disse no chat: '{text_detected}'\n\nResponda de forma natural e curta (máximo 50 caracteres):"
            
            if self.provider == 'ollama':
                response = self._call_ollama(prompt)
            elif self.provider == 'gemini':
                response = self._call_gemini(prompt)
            elif self.provider == 'openai':
                response = self._call_openai(prompt)
            else:
                logger.warning(f"Provider desconhecido: {self.provider}")
                return None
            
            # Limita o tamanho da resposta
            if response and len(response) > 50:
                response = response[:47] + "..."
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return None
    
    def _call_ollama(self, prompt):
        """Chama API do Ollama (local)."""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "top_p": 0.9,
                }
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.ConnectionError:
            logger.warning("Ollama não está rodando. Inicie com: ollama serve")
            return None
        except Exception as e:
            logger.error(f"Erro ao chamar Ollama: {e}")
            return None
    
    def _call_gemini(self, prompt):
        """Chama API do Google Gemini."""
        try:
            if not self.api_key:
                logger.warning("API key do Gemini não configurada")
                return None
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": 50,
                }
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text.strip()
            
        except Exception as e:
            logger.error(f"Erro ao chamar Gemini: {e}")
            return None
    
    def _call_openai(self, prompt):
        """Chama API da OpenAI."""
        try:
            if not self.api_key:
                logger.warning("API key da OpenAI não configurada")
                return None
            
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 50,
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            text = result['choices'][0]['message']['content']
            return text.strip()
            
        except Exception as e:
            logger.error(f"Erro ao chamar OpenAI: {e}")
            return None
    
    def type_response(self, response_text):
        """
        Digita a resposta no jogo com timing humanizado.
        
        Args:
            response_text: Texto a ser digitado
        """
        if not response_text or not self.input_sim:
            return
        
        # Simula tempo de leitura e digitação
        reading_time = random.uniform(self.min_response_time, self.max_response_time)
        logger.info(f"Aguardando {reading_time:.2f}s antes de responder...")
        time.sleep(reading_time)
        
        # Abre o chat (geralmente com Enter ou T)
        self.input_sim.press('return')
        time.sleep(random.uniform(0.1, 0.3))
        
        # Digita caractere por caractere com variação humana
        for char in response_text:
            self.input_sim.press(char)
            # Delay variável entre teclas (50-150ms)
            delay = random.uniform(0.05, 0.15)
            # Pausas maiores em espaços e pontuação
            if char in ' ,.!?':
                delay *= random.uniform(1.5, 2.5)
            time.sleep(delay)
        
        # Envia a mensagem
        time.sleep(random.uniform(0.2, 0.5))
        self.input_sim.press('return')
        
        logger.info(f"Resposta enviada: {response_text}")
    
    def handle_detected_chat(self, text_detected):
        """
        Processa texto detectado no chat e responde se apropriado.
        
        Args:
            text_detected: Texto detectado pelo OCR no chat
            
        Returns:
            True se respondeu, False caso contrário
        """
        if not text_detected or not self.should_respond():
            return False
        
        logger.info(f"Mensagem detectada: {text_detected}")
        
        response = self.generate_response(text_detected)
        
        if response:
            self.type_response(response)
            return True
        
        return False
