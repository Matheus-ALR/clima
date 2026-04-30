import os
from datetime import datetime, timedelta
import requests

from database import buscar_clima_no_banco, salvar_clima_no_banco


def fahrenheit_to_celcius(temp):
    if temp is not None:
        return round((temp - 32) * 5 / 9, 2)
    return None


def mph_to_kmph(v_mph):
    if v_mph is not None:
        return round(v_mph * 1.609, 2)
    return None


def validar_nome_cidade(cidade):
    if not cidade or not isinstance(cidade, str):
        return 'O nome da cidade é obrigatório.'

    if len(cidade.strip()) < 2:
        return 'O nome da cidade deve ter pelo menos 2 caracteres'

    return None


def transformar_dados_clima(dados_clima):
    clima_atual = dados_clima.get('currentConditions', {})
    dias = dados_clima.get('days', [])[:7]

    data_atual = datetime.now().strftime('%d/%m/%Y')

    dados_processados = {
        'data': data_atual,
        'hora': clima_atual.get('datetime'),
        'cidade': dados_clima.get('resolvedAddress'),
        'temperatura': fahrenheit_to_celcius(clima_atual.get('temp')),
        'umidade': clima_atual.get('humidity'),
        'vento': mph_to_kmph(clima_atual.get('windspeed')),
        'precipitacao': clima_atual.get('precip'),
        'icon': clima_atual.get('icon'),
        'previsao': []
    }

    for dia in dias:
        dados_processados['previsao'].append({
            'data': datetime.strptime(dia['datetime'], "%Y-%m-%d").strftime('%d/%m/%Y'),
            'temperatura_max': fahrenheit_to_celcius(dia.get('tempmax')),
            'temperatura_min': fahrenheit_to_celcius(dia.get('tempmin')),
            'umidade': dia.get('humidity'),
            'vento': mph_to_kmph(dia.get('windspeed')),
            'precipitacao': dia.get('precip'),
            'icon': dia.get('icon'),
        })

    return dados_processados


def buscar_clima_por_cidade(cidade):
    print("🌍 BUSCANDO CLIMA PARA:", cidade)

    msg_erro = validar_nome_cidade(cidade)
    if msg_erro:
        return {
            'error': True,
            'message': msg_erro,
            'status': 400
        }

    # 🔎 1. BUSCA NO BANCO
    dados_banco = buscar_clima_no_banco(cidade)

    if dados_banco:
        print("⚡ RETORNANDO DADOS DO BANCO")
        return {
            'error': False,
            'data': dados_banco,
            'status': 200
        }

    print("🌐 NÃO TEM NO BANCO → CHAMANDO API")

    base_url = os.getenv('BASE_URL_VISUAL_CROSSING')
    api_key = os.getenv('VISUAL_CROSSING_API_KEY')

    if not base_url or not api_key:
        print("❌ API KEY OU URL AUSENTE")
        return {
            'error': True,
            'message': 'Configurações de API ausentes.',
            'status': 500
        }

    data_inicial = datetime.now().strftime('%Y-%m-%d')
    data_final = (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')

    url = f"{base_url}{cidade}/{data_inicial}/{data_final}?key={api_key}&unitGroup=us&include=days,current"

    try:
        response = requests.get(url, timeout=10)

        print("📡 STATUS API:", response.status_code)

        if response.status_code == 404:
            return {
                'error': True,
                'message': f"Cidade '{cidade}' não encontrada.",
                'status': 404
            }

        response.raise_for_status()

        dados_response = response.json()
        dados_processados = transformar_dados_clima(dados_response)

        # 🔥 CORREÇÃO CRÍTICA → cidade padronizada
        clima_para_salvar = {
            'cidade': cidade.lower(),
            'data': dados_processados['data'],
            'umidade': dados_processados['umidade'],
            'vento': dados_processados['vento'],
            'precipitacao': dados_processados['precipitacao'],
            'temperatura_min': dados_processados['previsao'][0]['temperatura_min'],
            'temperatura_max': dados_processados['previsao'][0]['temperatura_max'],
        }

        salvar_clima_no_banco(clima_para_salvar)

        return {
            'error': False,
            'data': dados_processados,
            'status': 200
        }

    except Exception as ex:
        print("❌ ERRO GERAL:", str(ex))
        return {
            'error': True,
            'message': f"Erro: {str(ex)}",
            'status': 500
        }