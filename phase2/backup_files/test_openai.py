#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from openai import AzureOpenAI, __version__ as openai_version
import sys
import traceback

# Charger les variables d'environnement
load_dotenv('.env')

# Récupérer les paramètres de configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
GPT4O_DEPLOYMENT_NAME = os.getenv("GPT4O_DEPLOYMENT_NAME")

print("==== Test d'initialisation du client AzureOpenAI ====")
print(f"Version de la bibliothèque OpenAI: {openai_version}")
print(f"Version de Python: {sys.version}")
print(f"AZURE_OPENAI_API_VERSION: {AZURE_OPENAI_API_VERSION}")
print(f"AZURE_OPENAI_ENDPOINT: {AZURE_OPENAI_ENDPOINT}")
print(f"API KEY disponible: {'✓' if AZURE_OPENAI_API_KEY else '✗'}")
print(f"DEPLOYMENT NAME disponible: {'✓' if GPT4O_DEPLOYMENT_NAME else '✗'}")
print("\n")

# Test 1: Initialisation sans proxies
print("Test 1: Initialisation sans proxies")
try:
    client1 = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    print("✓ Initialisation réussie sans proxies!")
except Exception as e:
    print(f"✗ Erreur: {str(e)}")
    traceback.print_exc()
print("\n")

# Test 2: Initialisation avec proxies vide
print("Test 2: Initialisation avec proxies vide")
try:
    client2 = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        proxies={}
    )
    print("✓ Initialisation réussie avec proxies vide!")
except Exception as e:
    print(f"✗ Erreur: {str(e)}")
    traceback.print_exc()
print("\n")

# Test 3: Initialisation avec timeout
print("Test 3: Initialisation avec timeout")
try:
    client3 = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        timeout=30
    )
    print("✓ Initialisation réussie avec timeout!")
except Exception as e:
    print(f"✗ Erreur: {str(e)}")
    traceback.print_exc()
print("\n")

# Test 4: Initialisation avec base_url au lieu de azure_endpoint
print("Test 4: Initialisation avec base_url au lieu de azure_endpoint")
try:
    client4 = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        base_url=AZURE_OPENAI_ENDPOINT
    )
    print("✓ Initialisation réussie avec base_url!")
except Exception as e:
    print(f"✗ Erreur: {str(e)}")
    traceback.print_exc()
print("\n")

# Test 5: Test complet - initialisation + appel API simple
print("Test 5: Test complet - initialisation + appel API (azure_endpoint)")
try:
    # Initialiser avec azure_endpoint
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    
    # Tenter un appel API simple
    print("Tentative d'appel API...")
    response = client.chat.completions.create(
        model=GPT4O_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "Tu es un assistant utile."},
            {"role": "user", "content": "Dis bonjour!"}
        ],
        max_tokens=10
    )
    print(f"✓ Appel API réussi! Réponse: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ Erreur lors du test complet: {str(e)}")
    traceback.print_exc()
print("\n")

# Test 6: Test complet avec base_url
print("Test 6: Test complet - initialisation + appel API (base_url)")
try:
    # Initialiser avec base_url
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        base_url=AZURE_OPENAI_ENDPOINT
    )
    
    # Tenter un appel API simple
    print("Tentative d'appel API...")
    response = client.chat.completions.create(
        model=GPT4O_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "Tu es un assistant utile."},
            {"role": "user", "content": "Dis bonjour!"}
        ],
        max_tokens=10
    )
    print(f"✓ Appel API réussi! Réponse: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ Erreur lors du test complet: {str(e)}")
    traceback.print_exc() 