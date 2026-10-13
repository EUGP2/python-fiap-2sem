import unittest
from unittest.mock import Mock, patch

from requests.exceptions import ConnectionError, HTTPError, Timeout

from eventtech.services.EnderecoAPI import consultar_cep


class ConsultaCEPTest(unittest.TestCase):
    def setUp(self):
        consulta = patch("eventtech.services.EnderecoAPI.requests.get")
        self.get = consulta.start()
        self.addCleanup(consulta.stop)
        self.dados = {"cep": "01001-000", "logradouro": "Praça da Sé",
                      "bairro": "Sé", "localidade": "São Paulo", "uf": "SP"}
        self.resposta = Mock()
        self.resposta.json.return_value = self.dados
        self.get.return_value = self.resposta

    def test_formatos_invalidos_nao_fazem_requisicao(self):
        invalidos = (None, 1001000, "", "0100100", "010010000", "0100-1000",
                     "01001--000", " 01001000", "01001000 ", "01001ABC",
                     "０１００１０００", "٠١٠٠١٠٠٠", "01001000\n")
        for cep in invalidos:
            with self.subTest(cep=cep):
                sucesso, mensagem, status = consultar_cep(cep)
                self.assertFalse(sucesso)
                self.assertEqual(status, 400)
                self.assertIn("8 dígitos", mensagem)
        self.get.assert_not_called()

    def test_sucesso_com_e_sem_hifen(self):
        for cep in ("01001000", "01001-000"):
            with self.subTest(cep=cep):
                sucesso, endereco, status = consultar_cep(cep)
                self.assertTrue(sucesso)
                self.assertEqual(status, 200)
                self.assertEqual(endereco, dict(self.dados,
                                 endereco="Praça da Sé, Sé, São Paulo - SP"))
                self.get.assert_called_with("https://viacep.com.br/ws/01001000/json/",
                                            timeout=8)
        self.assertEqual(self.resposta.raise_for_status.call_count, 2)

    def test_cep_geral_aceita_logradouro_e_bairro_vazios(self):
        self.dados.update(logradouro="", bairro="")
        sucesso, endereco, status = consultar_cep("01001000")
        self.assertTrue(sucesso)
        self.assertEqual(status, 200)
        self.assertEqual(endereco["endereco"], "São Paulo - SP")

    def test_cep_nao_encontrado(self):
        self.resposta.json.return_value = {"erro": True}
        self.assertEqual(consultar_cep("01001000"), (False, "CEP não encontrado.", 404))

    def test_dados_malformados(self):
        invalidos = ([], None, {}, dict(self.dados, bairro=None),
                     dict(self.dados, cep="99999-999"), dict(self.dados, cep="inválido"),
                     dict(self.dados, localidade=" "), dict(self.dados, uf="sp"))
        for dados in invalidos:
            with self.subTest(dados=dados):
                self.resposta.json.return_value = dados
                sucesso, mensagem, status = consultar_cep("01001000")
                self.assertFalse(sucesso)
                self.assertEqual(status, 502)
                self.assertIn("resposta", mensagem)

    def test_erro_http(self):
        self.resposta.raise_for_status.side_effect = HTTPError("detalhe interno")
        sucesso, mensagem, status = consultar_cep("01001000")
        self.assertFalse(sucesso)
        self.assertEqual(status, 502)
        self.assertNotIn("detalhe interno", mensagem)
        self.resposta.json.assert_not_called()

    def test_json_invalido(self):
        self.resposta.json.side_effect = ValueError("JSON inválido")
        self.assertEqual(consultar_cep("01001000"),
                         (False, "O serviço de CEP retornou uma resposta inválida.", 502))

    def test_timeout_e_erro_de_conexao(self):
        for erro, status_esperado in ((Timeout("segredo"), 504),
                                      (ConnectionError("segredo"), 502)):
            with self.subTest(erro=type(erro).__name__):
                self.get.side_effect = erro
                sucesso, mensagem, status = consultar_cep("01001000")
                self.assertFalse(sucesso)
                self.assertEqual(status, status_esperado)
                self.assertNotIn("segredo", mensagem)
