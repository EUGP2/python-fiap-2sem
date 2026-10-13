import os
from pathlib import Path

import oracledb
from dotenv import load_dotenv

# O .env fica em ativ-aval04 e nao deve ser enviado para o GitHub.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class ConnectionFactory:
    def conectar(self):
        usuario = os.getenv("ORACLE_USER", "").strip()
        senha = os.getenv("ORACLE_PASSWORD", "")
        if not usuario or not senha:
            raise ValueError("Preencha ORACLE_USER e ORACLE_PASSWORD no arquivo .env.")

        host = os.getenv("ORACLE_HOST", "oracle.fiap.com.br")
        porta = int(os.getenv("ORACLE_PORT", "1521"))
        servico = os.getenv("ORACLE_SERVICE_NAME", "ORCL")
        dsn = oracledb.makedsn(host, porta, service_name=servico)
        return oracledb.connect(
            user=usuario, password=senha, dsn=dsn, tcp_connect_timeout=5
        )
