"""
Módulo de Notificações - Dispara alertas para canais gratuitos (Telegram + Discord)
"""

import requests
from loguru import logger


class NotificationManager:
    """Gerencia notificações via Telegram e Discord."""
    
    def __init__(self, config):
        self.cfg = config.get('notifications', {})
        
        # Configurações do Telegram
        self.telegram_bot_token = self.cfg.get('telegram_bot_token')      # Token do bot
        self.telegram_chat_id = self.cfg.get('telegram_chat_id')          # Chat ID
        
        # Configurações do Discord
        self.discord_webhook_url = self.cfg.get('discord_webhook_url')

    def send_telegram(self, message):
        """
        Envia mensagem via Telegram Bot (GRATUITO).
        
        Documentação: https://core.telegram.org/bots/api
        Args:
            message (str): Mensagem a ser enviada
            
        Returns:
            bool: True se enviado com sucesso
        """
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("Telegram não configurado. Pulando notificação.")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            data = {
                "chat_id": self.telegram_chat_id,
                "text": f"🤖 **PokeBot**: {message}",
                "parse_mode": "Markdown"  # Suporta negrito, itálico, etc
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.success("✅ Notificação Telegram enviada com sucesso")
                return True
            else:
                logger.error(f"Erro Telegram (status {response.status_code}): {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout ao enviar Telegram (conexão lenta)")
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar Telegram: {e}")
            return False

    def send_discord(self, message):
        """
        Envia mensagem via Discord Webhook (GRATUITO).
        
        Args:
            message (str): Mensagem a ser enviada
            
        Returns:
            bool: True se enviado com sucesso
        """
        if not self.discord_webhook_url:
            logger.warning("Discord não configurado. Pulando notificação.")
            return False
            
        try:
            data = {"content": f"🤖 **PokeBot**: {message}"}
            response = requests.post(self.discord_webhook_url, json=data, timeout=10)
            
            if response.status_code == 204:
                logger.success("✅ Notificação Discord enviada com sucesso")
                return True
            else:
                logger.error(f"Erro Discord (status {response.status_code})")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout ao enviar Discord (conexão lenta)")
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar Discord: {e}")
            return False

    def notify_all(self, message, is_critical=False):
        """
        Dispara notificação para todos os canais configurados.
        
        Args:
            message (str): Corpo da mensagem
            is_critical (bool): Se True, adiciona emoji de alerta
        """
        prefix = "🚨 **CRÍTICO** 🚨" if is_critical else "ℹ️ INFO"
        full_msg = f"{prefix}: {message}"
        
        logger.info(f"Disparando notificação: {full_msg}")
        
        # Tenta enviar para Telegram (prioridade)
        telegram_ok = self.send_telegram(full_msg)
        
        # Tenta enviar para Discord (fallback)
        discord_ok = self.send_discord(full_msg)
        
        if not (telegram_ok or discord_ok):
            logger.warning("⚠️ Falha ao enviar notificação por QUALQUER canal")
            return False
            
        return True

    def notify_shiny_found(self, pokemon_name, location="Desconhecido"):
        """
        Notificação especial para Shiny encontrado.
        
        Args:
            pokemon_name (str): Nome do Pokémon shiny
            location (str): Localização onde foi encontrado
        """
        message = (
            f"\n"
            f"✨ **SHINY ENCONTRADO!** ✨\n"
            f"Pokémon: *{pokemon_name.upper()}*\n"
            f"Local: {location}\n"
            f"Status: Bot pausado aguardando ação\n"
        )
        self.notify_all(message, is_critical=True)

    def notify_battle_status(self, player_pokemon, enemy_pokemon, player_hp_pct, enemy_hp_pct):
        """
        Notificação de status de batalha (para monitoramento).
        
        Args:
            player_pokemon (str): Seu Pokémon
            enemy_pokemon (str): Pokémon inimigo
            player_hp_pct (float): % de HP seu
            enemy_hp_pct (float): % de HP inimigo
        """
        message = (
            f"⚔️ **Status de Batalha**\n"
            f"Seu: {player_pokemon} ({player_hp_pct:.1f}%)\n"
            f"Inimigo: {enemy_pokemon} ({enemy_hp_pct:.1f}%)"
        )
        self.notify_all(message, is_critical=False)

    def notify_error(self, error_msg, context=""):
        """
        Notificação de erro.
        
        Args:
            error_msg (str): Mensagem de erro
            context (str): Contexto do erro
        """
        message = f"❌ **ERRO**: {error_msg}"
        if context:
            message += f"\n📍 Contexto: {context}"
        self.notify_all(message, is_critical=True)
