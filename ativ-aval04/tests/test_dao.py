import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

import oracledb
from eventtech.dao.EventoDAO import EventoDAO
from eventtech.entity.Evento import Evento


class TestEventoDAO(unittest.TestCase):
    def setUp(self):
        self.cursor = Mock(rowcount=1)
        self.conexao = Mock()
        self.conexao.cursor.return_value = self.cursor
        self.banco = Mock()
        self.banco.conectar.return_value = self.conexao
        self.dao = EventoDAO(self.banco)
        self.evento = Evento(1, "Nome ' teste", "Tecnologia", datetime(2026, 11, 1), "Auditório",
                             50, 25.5, "Equipe", "ATIVO", datetime(2020, 1, 2))

    def conferir_fechamento(self):
        self.cursor.close.assert_called_once()
        self.conexao.close.assert_called_once()

    def test_escritas_usam_binds_commit_e_fechamento(self):
        for metodo, argumento in (("incluir", self.evento), ("alterar_evento", self.evento), ("excluir_evento", 1)):
            with self.subTest(metodo=metodo):
                self.setUp()
                self.assertTrue(getattr(self.dao, metodo)(argumento)[0])
                sql, binds = self.cursor.execute.call_args.args
                self.assertIn(":id_evento", sql)
                self.assertEqual(binds["id_evento"], 1)
                self.assertNotIn(self.evento.nome_evento, sql)
                if metodo == "incluir":
                    self.assertEqual(binds["data_cadastro"], self.evento.data_cadastro)
                if metodo == "alterar_evento":
                    self.assertNotIn("DATA_CADASTRO", sql.upper())
                    self.assertNotIn("data_cadastro", binds)
                if metodo == "excluir_evento":
                    self.assertIn("DELETE FROM EVENTOS", sql.upper())
                    self.assertNotIn("UPDATE", sql.upper())
                self.conexao.commit.assert_called_once()
                self.conexao.rollback.assert_not_called()
                self.conferir_fechamento()

    def test_rowcount_zero_nao_informa_sucesso(self):
        for metodo, argumento in (("alterar_evento", self.evento), ("excluir_evento", 1)):
            self.setUp()
            self.cursor.rowcount = 0
            self.assertEqual(getattr(self.dao, metodo)(argumento), (False, "Evento não encontrado."))
            self.conferir_fechamento()

    def test_consultas_fecham_recursos_e_distinguem_ausencia(self):
        registro = tuple(vars(self.evento).values())
        self.cursor.fetchall.return_value = [registro]
        self.assertEqual(self.dao.listar_eventos(), (True, [registro]))
        self.conferir_fechamento()
        self.setUp()
        self.cursor.fetchone.return_value = registro
        self.assertEqual(self.dao.buscar_evento_por_id(1), (True, vars(self.evento)))
        self.assertEqual(self.cursor.execute.call_args.args[1], {"id_evento": 1})
        self.conferir_fechamento()
        self.setUp()
        self.cursor.fetchone.return_value = None
        self.assertEqual(self.dao.buscar_evento_por_id(999), (False, "Evento não encontrado."))
        self.conferir_fechamento()

    def test_duplicado_rollback_sem_expor_detalhe_oracle(self):
        self.cursor.execute.side_effect = oracledb.IntegrityError(SimpleNamespace(code=1))
        self.assertEqual(self.dao.incluir(self.evento), (False, "Já existe um evento com esse ID."))
        self.conexao.rollback.assert_called_once()
        self.conexao.commit.assert_not_called()
        self.conferir_fechamento()

    def test_erros_oracle_e_configuracao_sao_tratados(self):
        for metodo, argumento in (("incluir", self.evento), ("alterar_evento", self.evento),
                                  ("excluir_evento", 1), ("buscar_evento_por_id", 1), ("listar_eventos", None)):
            with self.subTest(metodo=metodo):
                self.setUp()
                self.cursor.execute.side_effect = oracledb.DatabaseError("detalhe privado")
                chamada = getattr(self.dao, metodo)
                resultado = chamada(argumento) if argumento is not None else chamada()
                self.assertFalse(resultado[0])
                self.assertNotIn("detalhe privado", resultado[1])
                self.conexao.commit.assert_not_called()
                if metodo in ("incluir", "alterar_evento", "excluir_evento"):
                    self.conexao.rollback.assert_called_once()
                self.conferir_fechamento()
                self.setUp()
                self.banco.conectar.side_effect = ValueError("configuração privada")
                chamada = getattr(self.dao, metodo)
                resultado = chamada(argumento) if argumento is not None else chamada()
                self.assertFalse(resultado[0])
                self.assertNotIn("configuração privada", resultado[1])


if __name__ == "__main__":
    unittest.main()
