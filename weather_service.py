import os
import requests
from datetime import datetime, timedelta
from database import buscar_clima_no_banco, salvar_clima_no_banco


def fahrenheit_to_celcius(temp):
    return round((temp - 32) * 5 / 9, 2) if temp is not None else None


def mph_to_kmph(v_mph):
    return round(v_mph * 1.609, 2) if v_mph is not None else None


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
    if not cidade or len(cidade.strip()) < 2:
        return {'error': True, 'message': 'Nome da cidade inválido.', 'status': 400}

    # 1. Tenta buscar no banco primeiro
    dados_banco = buscar_clima_no_banco(cidade)
    if dados_banco:
        return {'error': False, 'data': dados_banco, 'status': 200}

    # 2. Busca na API se não estiver no banco
    base_url = os.getenv('BASE_URL_VISUAL_CROSSING')
    api_key = os.getenv('VISUAL_CROSSING_API_KEY')

    if not base_url or not api_key:
        return {'error': True, 'message': 'Configurações de API ausentes no servidor.', 'status': 500}

    data_ini = datetime.now().strftime('%Y-%m-%d')
    data_fim = (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')
    url = f"{base_url}{cidade}/{data_ini}/{data_fim}?key={api_key}&unitGroup=us&include=days,current"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            return {'error': True, 'message': 'Cidade não encontrada.', 'status': 404}

        response.raise_for_status()
        dados_processados = transformar_dados_clima(response.json())

        # Salva no banco para futuras buscas
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

        return {'error': False, 'data': dados_processados, 'status': 200}
    except Exception as ex:
        return {'error': True, 'message': f"Erro na API: {str(ex)}", 'status': 500}