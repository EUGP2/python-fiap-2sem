import json
import unittest
from datetime import datetime
from unittest.mock import patch

with patch("oracledb.connect", side_effect=AssertionError("Oracle não é usado nos testes")):
    from eventtech import App


class DAOEmMemoria:
    """Simula os registros apenas para testar as rotas, sem substituir o DAO real."""
    def __init__(self):
        self.eventos = {}

    def incluir(self, evento):
        if evento.id_evento in self.eventos:
            return False, "Já existe um evento com esse ID."
        self.eventos[evento.id_evento] = evento
        return True, "Evento cadastrado com sucesso!"

    def listar_eventos(self):
        return True, [tuple(vars(self.eventos[id_evento]).values()) for id_evento in sorted(self.eventos)]

    def buscar_evento_por_id(self, id_evento):
        if id_evento not in self.eventos:
            return False, "Evento não encontrado."
        return True, vars(self.eventos[id_evento]).copy()

    def alterar_evento(self, evento):
        if evento.id_evento not in self.eventos:
            return False, "Evento não encontrado."
        self.eventos[evento.id_evento] = evento
        return True, "Evento alterado com sucesso!"

    def excluir_evento(self, id_evento):
        if id_evento not in self.eventos:
            return False, "Evento não encontrado."
        del self.eventos[id_evento]
        return True, "Evento excluído com sucesso!"


class TestEventTech(unittest.TestCase):
    def setUp(self):
        self.dao = DAOEmMemoria()
        for troca in (patch.object(App, "dao", self.dao),
                      patch.dict(App.app.config, TESTING=True, SECRET_KEY="teste"),
                      patch("oracledb.connect", side_effect=AssertionError("Sem Oracle")),
                      patch("requests.get", side_effect=AssertionError("Sem API real"))):
            troca.start()
            self.addCleanup(troca.stop)
        self.client = App.app.test_client()

    def dados(self, id_evento=1, **alteracoes):
        dados = dict(id_evento=str(id_evento), nome_evento=f"Evento {id_evento}", categoria="Tecnologia",
                     data_evento="2026-11-01", local_evento="Auditório", capacidade="50",
                     valor_ingresso="25.50", responsavel="Equipe", status="ATIVO")
        dados.update(alteracoes)
        return dados

    def enviar(self, caminho, dados):
        self.client.get(caminho)
        with self.client.session_transaction() as sessao:
            token = sessao["csrf_token"]
        return self.client.post(caminho, data=dict(dados, csrf_token=token))

    def cadastrar(self, id_evento=1, **alteracoes):
        return self.enviar("/eventos/cadastrar", self.dados(id_evento, **alteracoes))

    def test_01_cadastrar_tres_e_listar(self):
        for id_evento in (1, 2, 3):
            self.assertEqual(self.cadastrar(id_evento).status_code, 303)
        self.assertEqual(len(self.dao.eventos), 3)
        pagina = self.client.get("/eventos").get_data(as_text=True)
        for nome in ("Evento 1", "Evento 2", "Evento 3"):
            self.assertIn(nome, pagina)

    def test_02_id_duplicado_preserva_formulario(self):
        self.cadastrar()
        resposta = self.cadastrar(nome_evento="Nova tentativa")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Já existe", resposta.get_data(as_text=True))
        self.assertIn('value="Nova tentativa"', resposta.get_data(as_text=True))
        self.assertEqual(self.dao.eventos[1].nome_evento, "Evento 1")

    def test_03_validacao_preserva_dados_e_rejeita_limites(self):
        invalidos = [dict(id_evento="0"), dict(id_evento="abc"), dict(capacidade="0"),
                     dict(capacidade="1.5"), dict(nome_evento=""), dict(local_evento="x" * 101),
                     dict(responsavel=""), dict(categoria="Inventada"), dict(status="INVÁLIDO"),
                     dict(data_evento="2026-02-30"), dict(valor_ingresso="-1"),
                     dict(valor_ingresso="NaN"), dict(valor_ingresso="1.001"),
                     dict(valor_ingresso="100000000"), dict(id_evento=str(10 ** 38))]
        for alteracoes in invalidos:
            with self.subTest(alteracoes=alteracoes):
                resposta = self.cadastrar(**alteracoes)
                self.assertEqual(resposta.status_code, 422)
                if "responsavel" not in alteracoes:
                    self.assertIn('value="Equipe"', resposta.get_data(as_text=True))
        self.assertFalse(self.dao.eventos)

    def test_04_alteracao_ignora_id_e_data_cadastro_forjados(self):
        self.cadastrar()
        cadastro_original = datetime(2020, 1, 2)
        self.dao.eventos[1].data_cadastro = cadastro_original
        dados = self.dados(999, nome_evento="Evento atualizado", data_cadastro="1999-01-01")
        self.assertEqual(self.enviar("/eventos/editar/1", dados).status_code, 303)
        self.assertEqual(list(self.dao.eventos), [1])
        self.assertEqual(self.dao.eventos[1].nome_evento, "Evento atualizado")
        self.assertEqual(self.dao.eventos[1].data_cadastro, cadastro_original)

    def test_05_consulta_existente_inexistente_e_id_invalido(self):
        self.cadastrar()
        resposta = self.client.get("/eventos/consultar?id_evento=1", follow_redirects=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Evento 1", resposta.get_data(as_text=True))
        self.assertEqual(self.client.get("/eventos/999").status_code, 404)
        for valor in ("", "abc", "0", "-1"):
            self.assertEqual(self.client.get("/eventos/consultar", query_string={"id_evento": valor}).status_code, 400)

    def test_06_exclusao_confirmada_remove_registro(self):
        self.cadastrar()
        self.assertEqual(self.enviar("/eventos/excluir/1", {"confirmar": "S"}).status_code, 303)
        self.assertFalse(self.dao.eventos)
        self.assertEqual(self.client.get("/eventos/1").status_code, 404)

    def test_07_get_cancelamento_e_csrf_nao_excluem(self):
        self.cadastrar()
        self.assertEqual(self.client.get("/eventos/excluir/1").status_code, 200)
        for dados in ({"confirmar": "N"}, {}):
            self.assertEqual(self.enviar("/eventos/excluir/1", dados).status_code, 303)
            self.assertIn(1, self.dao.eventos)
        self.assertEqual(self.client.post("/eventos/excluir/1", data={"confirmar": "S"}).status_code, 400)
        self.assertIn(1, self.dao.eventos)

    def test_08_api_e_exportacoes_refletem_alteracao(self):
        self.cadastrar()
        antes = self.client.get("/api/eventos").get_json()
        self.enviar("/eventos/editar/1", self.dados(nome_evento="Nome alterado", valor_ingresso="12,34"))
        api = self.client.get("/api/eventos").get_json()
        arquivo = self.client.get("/eventos/exportar/json")
        self.assertEqual(json.loads(arquivo.get_data(as_text=True)), api)
        self.assertNotEqual(antes, api)
        self.assertEqual(api[0]["valor_ingresso"], 12.34)
        self.assertEqual(api[0]["data_evento"], "01/11/2026")
        for caminho, nome in (("/eventos/exportar/json", "eventtech.json"), ("/eventos/exportar/html", "eventtech.html")):
            resposta = self.client.get(caminho)
            self.assertIn(nome, resposta.headers["Content-Disposition"])
            self.assertIn("Nome alterado", resposta.get_data(as_text=True))
            self.assertNotIn("Evento 1", resposta.get_data(as_text=True))

    def test_09_lista_e_exportacoes_vazias(self):
        self.assertEqual(self.client.get("/api/eventos").get_json(), [])
        self.assertEqual(self.client.get("/eventos/exportar/json").get_json(), [])
        for caminho in ("/eventos", "/eventos/exportar/html"):
            resposta = self.client.get(caminho)
            self.assertEqual(resposta.status_code, 200)
            self.assertIn("Nenhum evento cadastrado", resposta.get_data(as_text=True))

    def test_10_falhas_banco_e_api_sao_mostradas(self):
        with patch.object(self.dao, "listar_eventos", return_value=(False, "Banco indisponível.")):
            for caminho in ("/eventos", "/api/eventos", "/eventos/exportar/json", "/eventos/exportar/html"):
                self.assertEqual(self.client.get(caminho).status_code, 503)
        with patch.object(self.dao, "buscar_evento_por_id", return_value=(False, "Banco indisponível.")):
            self.assertEqual(self.client.get("/eventos/1").status_code, 503)
        with patch.object(App, "consultar_cep", return_value=(False, "CEP indisponível.", 504)) as consulta:
            resposta = self.client.get("/api/cep/01001-000")
            self.assertEqual(resposta.status_code, 504)
            self.assertEqual(resposta.get_json(), {"erro": "CEP indisponível."})
            consulta.assert_called_once_with("01001-000")
        endereco = {"cep": "01001-000", "endereco": "Praça da Sé, Sé, São Paulo - SP"}
        with patch.object(App, "consultar_cep", return_value=(True, endereco, 200)):
            resposta = self.client.get("/api/cep/01001-000")
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(resposta.get_json(), endereco)

    def test_11_campos_html_sao_escapados(self):
        ataque = "<script>alert('x')</script>"
        self.cadastrar(nome_evento=ataque, local_evento=ataque, responsavel=ataque)
        for caminho in ("/eventos", "/eventos/1", "/eventos/editar/1", "/eventos/excluir/1", "/eventos/exportar/html"):
            html = self.client.get(caminho).get_data(as_text=True)
            self.assertNotIn(ataque, html)
            self.assertIn("&lt;script&gt;", html)
        resposta = self.cadastrar(2, nome_evento=ataque, capacidade="0")
        self.assertEqual(resposta.status_code, 422)
        self.assertNotIn(ataque, resposta.get_data(as_text=True))
        self.assertIn("&lt;script&gt;", resposta.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
