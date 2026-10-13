class Evento:
    def __init__(self, id_evento, nome_evento, categoria, data_evento, local_evento, capacidade, valor_ingresso, responsavel, status, data_cadastro):
        self.id_evento = id_evento
        self.nome_evento = nome_evento
        self.categoria = categoria
        self.data_evento = data_evento
        self.local_evento = local_evento
        self.capacidade = capacidade
        self.valor_ingresso = valor_ingresso
        self.responsavel = responsavel
        self.status = status
        self.data_cadastro = data_cadastro

    def para_dict(self):
        # Datas precisam virar texto para aparecer no arquivo JSON.
        return {
            "id_evento": int(self.id_evento),
            "nome_evento": self.nome_evento,
            "categoria": self.categoria,
            "data_evento": self.data_evento.strftime("%d/%m/%Y") if self.data_evento else None,
            "local_evento": self.local_evento,
            "capacidade": int(self.capacidade),
            "valor_ingresso": float(self.valor_ingresso) if self.valor_ingresso is not None else None,
            "responsavel": self.responsavel,
            "status": self.status,
            "data_cadastro": self.data_cadastro.strftime("%d/%m/%Y") if self.data_cadastro else None,
        }
