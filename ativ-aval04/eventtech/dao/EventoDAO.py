from . import ConnectionFactory
import oracledb

class EventoDAO:
    def __init__(self, banco=None):
        self.banco = banco if banco is not None else ConnectionFactory.ConnectionFactory()

    def incluir(self, evento):
        conn = None
        cursor = None
        try:
            conn = self.banco.conectar()
            cursor = conn.cursor()
            sql = """
                insert into eventos (
                ID_EVENTO,
                NOME_EVENTO,
                CATEGORIA,
                DATA_EVENTO,
                LOCAL_EVENTO,
                CAPACIDADE,
                VALOR_INGRESSO,
                RESPONSAVEL,
                STATUS,
                DATA_CADASTRO
                )
                values (
                :id_evento,
                :nome_evento,
                :categoria,
                :data_evento,
                :local_evento,
                :capacidade,
                :valor_ingresso,
                :responsavel,
                :status,
                :data_cadastro
                )
                """
            cursor.execute(
                sql,
                {
                    "id_evento": evento.id_evento,
                    "nome_evento": evento.nome_evento,
                    "categoria": evento.categoria,
                    "data_evento": evento.data_evento,
                    "local_evento": evento.local_evento,
                    "capacidade": evento.capacidade,
                    "valor_ingresso": evento.valor_ingresso,
                    "responsavel": evento.responsavel,
                    "status": evento.status,
                    "data_cadastro": evento.data_cadastro,
                }
            )
            conn.commit()
            return True, "Evento cadastrado com sucesso!"
        except (oracledb.Error, ValueError) as erro:
            if conn:
                conn.rollback()
            detalhe = erro.args[0] if erro.args else None
            if getattr(detalhe, "code", None) == 1:
                return False, "Já existe um evento com esse ID."
            return False, "Não foi possível cadastrar o evento. Tente novamente."
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def listar_eventos(self):
        conn = None
        cursor = None
        try:
            conn = self.banco.conectar()
            cursor = conn.cursor()
            sql = """
                select
                    ID_EVENTO,
                    NOME_EVENTO,
                    CATEGORIA,
                    DATA_EVENTO,
                    LOCAL_EVENTO,
                    CAPACIDADE,
                    VALOR_INGRESSO,
                    RESPONSAVEL,
                    STATUS,
                    DATA_CADASTRO
                from eventos
                order by ID_EVENTO
            """
            cursor.execute(sql)
            eventos = cursor.fetchall()
            return True, eventos
        except (oracledb.Error, ValueError):
            return False, "Não foi possível listar os eventos. Tente novamente."
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def buscar_evento_por_id(self, id_evento):
        conn = None
        cursor = None
        try:
            conn = self.banco.conectar()
            cursor = conn.cursor()
            sql = """
                select
                    ID_EVENTO,
                    NOME_EVENTO,
                    CATEGORIA,
                    DATA_EVENTO,
                    LOCAL_EVENTO,
                    CAPACIDADE,
                    VALOR_INGRESSO,
                    RESPONSAVEL,
                    STATUS,
                    DATA_CADASTRO
                from eventos
                where ID_EVENTO = :id_evento
            """
            cursor.execute(sql, {"id_evento": id_evento})
            evento = cursor.fetchone()
            if evento is None:
                return False, "Evento não encontrado."
            return True, {
                "id_evento": evento[0],
                "nome_evento": evento[1],
                "categoria": evento[2],
                "data_evento": evento[3],
                "local_evento": evento[4],
                "capacidade": evento[5],
                "valor_ingresso": evento[6],
                "responsavel": evento[7],
                "status": evento[8],
                "data_cadastro": evento[9],
            }
        except (oracledb.Error, ValueError):
            return False, "Não foi possível consultar o evento. Tente novamente."
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def alterar_evento(self, evento):
        conn = None
        cursor = None
        try:
            conn = self.banco.conectar()
            cursor = conn.cursor()
            sql = """
                update eventos
                set
                    NOME_EVENTO = :nome_evento,
                    CATEGORIA = :categoria,
                    DATA_EVENTO = :data_evento,
                    LOCAL_EVENTO = :local_evento,
                    CAPACIDADE = :capacidade,
                    VALOR_INGRESSO = :valor_ingresso,
                    RESPONSAVEL = :responsavel,
                    STATUS = :status
                where ID_EVENTO = :id_evento
            """
            cursor.execute(
                sql,
                {
                    "id_evento": evento.id_evento,
                    "nome_evento": evento.nome_evento,
                    "categoria": evento.categoria,
                    "data_evento": evento.data_evento,
                    "local_evento": evento.local_evento,
                    "capacidade": evento.capacidade,
                    "valor_ingresso": evento.valor_ingresso,
                    "responsavel": evento.responsavel,
                    "status": evento.status,
                }
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Evento não encontrado."
            return True, "Evento alterado com sucesso!"
        except (oracledb.Error, ValueError):
            if conn:
                conn.rollback()
            return False, "Não foi possível alterar o evento. Tente novamente."
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def excluir_evento(self, id_evento):
        conn = None
        cursor = None
        try:
            conn = self.banco.conectar()
            cursor = conn.cursor()
            sql = """
                delete from eventos
                where ID_EVENTO = :id_evento
            """
            cursor.execute(sql, {"id_evento": id_evento})
            conn.commit()

            if cursor.rowcount > 0:
                return True, "Evento excluído com sucesso!"
            return False, "Evento não encontrado."
        except (oracledb.Error, ValueError):
            if conn:
                conn.rollback()
            return False, "Não foi possível excluir o evento. Tente novamente."
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
