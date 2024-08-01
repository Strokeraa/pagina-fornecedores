from flask import Flask, request, render_template, redirect, url_for
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Settings
from zeep.transports import Transport
from zeep.helpers import serialize_object
from decimal import Decimal
import json

app = Flask(__name__)

# Função personalizada para converter objetos Decimal
def custom_converter(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f'Tipo não serializável: {type(obj)}')

# URL do WSDL
wsdl = 'http://ciqas08.appcom.org:8008/sap/bc/soap/wsdl11?services=BAPI_QUALNOT_GETDETAIL&sap-client=600'

# Configurando a sessão com autenticação
session = Session()
session.auth = HTTPBasicAuth('lgopereira', 'Sabo@2024')

# Configurando o transporte com a sessão autenticada
transport = Transport(session=session)

# Criando o cliente
client = Client(wsdl=wsdl, transport=transport)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        numero_rnc = request.form['numero_rnc']
        try:
            # Chamando a BAPI com todos os parâmetros necessários
            response = client.service.BAPI_QUALNOT_GETDETAIL(
                NUMBER="000" + numero_rnc,
                NOTIFACTV={},
                NOTITEM={},
                NOTIFCAUS={},
                NOTIFPARTNR={},
                NOTIFTASK={},
                NOTLONGTXT={},
                RETURN={}
            )

            # Convertendo a resposta em um dicionário Python
            response_dict = serialize_object(response)

            # Convertendo o dicionário em uma string JSON formatada, usando o custom converter para Decimal
            response_str = json.dumps(response_dict, indent=4, ensure_ascii=False, default=custom_converter)

            # Salvando a resposta em um arquivo de texto
            with open('resposta_rnc.txt', 'w', encoding='utf-8') as file:
                file.write(response_str)

            # Extraindo as informações necessárias
            data = {
                "fornecedor": response_dict['NOTIFHDTEXT']['VENDOR_NAME'],
                "material": response_dict['NOTIFHDTEXT']['MATL_DESC'],
                "no": response_dict['NOTIFHEADER_EXPORT']['NOTIF_NO'],
                "descricao_problema": response_dict['NOTIFHEADER_EXPORT']['SHORT_TEXT'],
                "data": response_dict['NOTIFHEADER_EXPORT']['NOTIF_DATE'],
                "codigo": response_dict['NOTIFHEADER_EXPORT']['MATERIAL'],
                "quantidade_interditada": response_dict['NOTIFHEADER_EXPORT']['QUANT_COMPLAINT'],
                "contato": response_dict['NOTIFPARTNR']['item'][1]['PARTNER'] + "@sabo.com.br"
            }

            return render_template('formulario.html', data=data)
        except Exception as e:
            return f"Erro ao chamar o serviço: {e}"
    return render_template('index.html', response='')

@app.route('/formulario')
def formulario():
    return render_template('formulario.html', data={})

@app.route('/salvar_respostas', methods=['POST'])
def salvar_respostas():
    respostas = request.form.to_dict()

    # Convertendo o dicionário em uma string JSON formatada
    respostas_str = json.dumps(respostas, indent=4, ensure_ascii=False, default=custom_converter)

    # Salvando as respostas em um arquivo de textoa
    with open('resposta_final.txt', 'w', encoding='utf-8') as file:
        file.write(respostas_str)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
