import re

import requests


def consultar_cep(cep):
    if not isinstance(cep, str) or not re.fullmatch(r"[0-9]{5}-?[0-9]{3}", cep):
        return False, "Informe um CEP com 8 dígitos, com ou sem hífen.", 400

    cep_numero = cep.replace("-", "")
    try:
        resposta = requests.get(f"https://viacep.com.br/ws/{cep_numero}/json/", timeout=8)
        resposta.raise_for_status()
        dados = resposta.json()
    except requests.exceptions.Timeout:
        return False, "A consulta de CEP demorou demais. Tente novamente.", 504
    except requests.exceptions.RequestException:
        return False, "Não foi possível acessar o serviço de CEP. Tente novamente.", 502
    except ValueError:
        return False, "O serviço de CEP retornou uma resposta inválida.", 502

    if not isinstance(dados, dict):
        return False, "O serviço de CEP retornou uma resposta inválida.", 502
    if dados.get("erro") is True:
        return False, "CEP não encontrado.", 404

    campos = ("cep", "logradouro", "bairro", "localidade", "uf")
    if any(not isinstance(dados.get(campo), str) for campo in campos):
        return False, "O serviço de CEP retornou uma resposta incompleta.", 502
    if (
        not re.fullmatch(r"[0-9]{5}-?[0-9]{3}", dados["cep"])
        or dados["cep"].replace("-", "") != cep_numero
        or not dados["localidade"].strip()
        or not re.fullmatch(r"[A-Z]{2}", dados["uf"])
    ):
        return False, "O serviço de CEP retornou uma resposta inválida.", 502

    endereco = {campo: dados[campo] for campo in campos}
    partes = [dados["logradouro"].strip(), dados["bairro"].strip()]
    partes.append(f"{dados['localidade'].strip()} - {dados['uf']}")
    endereco["endereco"] = ", ".join(parte for parte in partes if parte)
    return True, endereco, 200
