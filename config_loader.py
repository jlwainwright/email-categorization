#!/usr/bin/env python3
"""
Centralized configuration loader with environment variable overrides.
Prefers encrypted config via credential_manager when available.
"""
from __future__ import annotations

import os
import configparser
from typing import Optional


def _ensure_sections(config: configparser.ConfigParser) -> None:
    if not config.has_section('IMAP'):
        config['IMAP'] = {}
    if not config.has_section('Hugging Face'):
        config['Hugging Face'] = {}
    if not config.has_section('OpenAI'):
        config['OpenAI'] = {}


def _apply_env_overrides(config: configparser.ConfigParser) -> None:
    # IMAP
    if os.getenv('IMAP_SERVER'):
        config['IMAP']['server'] = os.getenv('IMAP_SERVER')
    if os.getenv('IMAP_PORT'):
        config['IMAP']['port'] = os.getenv('IMAP_PORT')
    if os.getenv('IMAP_USERNAME'):
        config['IMAP']['username'] = os.getenv('IMAP_USERNAME')
    if os.getenv('IMAP_PASSWORD'):
        config['IMAP']['password'] = os.getenv('IMAP_PASSWORD')

    # Hugging Face
    if os.getenv('HUGGINGFACE_API_KEY'):
        config['Hugging Face']['api_key'] = os.getenv('HUGGINGFACE_API_KEY')
    if os.getenv('HF_MODEL'):
        config['Hugging Face']['model'] = os.getenv('HF_MODEL')
    if os.getenv('HF_BASE_URL'):
        config['Hugging Face']['base_url'] = os.getenv('HF_BASE_URL')
    if os.getenv('HF_TIMEOUT'):
        config['Hugging Face']['timeout'] = os.getenv('HF_TIMEOUT')

    # OpenAI
    if os.getenv('OPENAI_API_KEY'):
        config['OpenAI']['api_key'] = os.getenv('OPENAI_API_KEY')
    if os.getenv('OPENAI_MODEL'):
        config['OpenAI']['model'] = os.getenv('OPENAI_MODEL')
    if os.getenv('OPENAI_BASE_URL'):
        config['OpenAI']['base_url'] = os.getenv('OPENAI_BASE_URL')
    if os.getenv('OPENAI_TIMEOUT'):
        config['OpenAI']['timeout'] = os.getenv('OPENAI_TIMEOUT')


def load_config_with_env(config_file: str = 'config.ini', encrypted_file: str = 'config.encrypted') -> configparser.ConfigParser:
    """Load configuration securely if possible, then apply environment overrides and defaults.

    Sections: [IMAP], [Hugging Face], [OpenAI]
    Supported env vars: IMAP_*, HUGGINGFACE_API_KEY, HF_MODEL, HF_BASE_URL, HF_TIMEOUT,
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL, OPENAI_TIMEOUT
    """
    config = None

    # Try secure loader first
    try:
        from credential_manager import load_config_secure  # type: ignore
        config = load_config_secure(config_file, encrypted_file)
    except Exception:
        config = None

    # Fallback to plaintext
    if config is None:
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file)
        else:
            # Start with empty config
            pass

    _ensure_sections(config)

    # Defaults
    config['Hugging Face'].setdefault('model', 'distilbert-base-uncased-finetuned-sst-2-english')
    config['Hugging Face'].setdefault('base_url', 'https://api-inference.huggingface.co/models')
    config['Hugging Face'].setdefault('timeout', '15')

    config['OpenAI'].setdefault('model', 'gpt-3.5-turbo')
    config['OpenAI'].setdefault('base_url', 'https://api.openai.com/v1')
    config['OpenAI'].setdefault('timeout', '15')

    _apply_env_overrides(config)

    return config