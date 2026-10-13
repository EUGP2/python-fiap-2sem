import json
import os
import secrets
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Flask, Response, abort, flash, jsonify, redirect, render_template, request, session, url_for

# Permite executar tanto App.py quanto python -m eventtech.App.
if __package__:
    from .dao.EventoDAO import EventoDAO
    from .entity.Evento import Evento
    from .enums.CategoriasEvento import CategoriasEvento
    from .enums.StatusEvento import StatusEvento
    from .services.EnderecoAPI import consultar_cep
else:
    from dao.EventoDAO import EventoDAO
    from entity.Evento import Evento
    from enums.CategoriasEvento import CategoriasEvento
    from enums.StatusEvento import StatusEvento
    from services.EnderecoAPI import consultar_cep

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.json.ensure_ascii = False
dao = EventoDAO()
categorias = [categoria.value for categoria in CategoriasEvento]
status_eventos = [status.name for status in StatusEvento]


@app.context_processor
def dados_formulario():
    # O token confirma que o POST veio de um formulario aberto neste navegador.
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return {"csrf_token": session["csrf_token"]}


@app.before_request
def conferir_formulario():
    if request.method == "POST":
        token = request.form.get("csrf_token", "")
        esperado = session.get("csrf_token", "")
        if not esperado or not secrets.compare_digest(token.encode("utf-8"), esperado.encode("utf-8")):
            abort(400)


@app.template_filter("data_br")
def data_br(valor):
    if hasattr(valor, "strftime"):
        return valor.strftime("%d/%m/%Y")
    return valor or "Não informado"


@app.template_filter("moeda")
def moeda(valor):
    if valor is None:
        return "Não informado"
    return "R$ " + f"{float(valor):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pagina_erro(mensagem, codigo=503, titulo="Não foi possível concluir"):
    return render_template("erro.html", titulo=titulo, mensagem=mensagem, codigo=codigo), codigo


def formulario(dados, erros=None, editando=False, codigo=200):
    return render_template(
        "formulario.html", dados=dados, erros=erros or [], editando=editando,
        categorias=categorias, status_eventos=status_eventos,
    ), codigo


def montar_evento(dados, id_fixo=None, data_cadastro=None):
    # Validar no Python tambem: o navegador sozinho nao protege os dados.
    try:
        id_evento = id_fixo if id_fixo is not None else int(dados.get("id_evento", ""))
        capacidade = int(dados.get("capacidade", ""))
    except (ValueError, TypeError):
        raise ValueError("ID e capacidade devem ser números inteiros.") from None
    if id_evento <= 0 or capacidade <= 0:
        raise ValueError("ID e capacidade devem ser maiores que zero.")
    if id_evento >= 10 ** 38 or capacidade >= 10 ** 38:
        raise ValueError("ID ou capacidade ultrapassam o limite do banco.")

    textos = {}
    for campo, nome in (("nome_evento", "Nome"), ("local_evento", "Local"), ("responsavel", "Responsável")):
        texto = dados.get(campo, "").strip()
        if not texto or len(texto) > 100:
            raise ValueError(f"{nome} deve ser preenchido com até 100 caracteres.")
        textos[campo] = texto

    categoria = dados.get("categoria", "").strip()
    status = dados.get("status", "").strip().upper()
    if categoria not in categorias:
        raise ValueError("Selecione uma categoria válida.")
    if status not in status_eventos:
        raise ValueError("Selecione um status válido.")
    try:
        data_evento = datetime.strptime(dados.get("data_evento", ""), "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError("Informe uma data válida para o evento.") from None
    try:
        valor = Decimal(dados.get("valor_ingresso", "").strip().replace(",", "."))
        if not valor.is_finite() or valor < 0 or valor > Decimal("99999999.99"):
            raise ValueError
        if valor != valor.quantize(Decimal("0.01")):
            raise ValueError
    except (InvalidOperation, ValueError):
        raise ValueError("Informe um valor não negativo, com até duas casas decimais.") from None

    return Evento(
        id_evento, textos["nome_evento"], categoria, data_evento, textos["local_evento"],
        capacidade, valor, textos["responsavel"], status, data_cadastro or datetime.now(),
    )


def eventos_para_json(registros):
    return [Evento(*registro).para_dict() for registro in registros]


def erro_consulta(mensagem):
    codigo = 404 if mensagem == "Evento não encontrado." else 503
    return pagina_erro(mensagem, codigo)


@app.route("/")
def inicio():
    return render_template("inicio.html")


@app.route("/eventos")
def listar_eventos():
    sucesso, resultado = dao.listar_eventos()
    if not sucesso:
        return pagina_erro(resultado)
    return render_template("eventos.html", eventos=eventos_para_json(resultado))


@app.route("/eventos/consultar")
def consultar_evento():
    try:
        id_evento = int(request.args.get("id_evento", ""))
        if id_evento <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return pagina_erro("Informe um ID inteiro maior que zero.", 400)
    return redirect(url_for("detalhar_evento", id_evento=id_evento))


@app.route("/eventos/<int:id_evento>")
def detalhar_evento(id_evento):
    sucesso, resultado = dao.buscar_evento_por_id(id_evento)
    if not sucesso:
        return erro_consulta(resultado)
    return render_template("detalhe.html", evento=resultado)


@app.route("/eventos/cadastrar", methods=["GET", "POST"])
def cadastrar_evento():
    if request.method == "GET":
        return formulario({"status": "ATIVO", "valor_ingresso": "0"})
    dados = request.form.to_dict()
    try:
        evento = montar_evento(dados)
    except ValueError as erro:
        return formulario(dados, [str(erro)], codigo=422)
    sucesso, mensagem = dao.incluir(evento)
    if not sucesso:
        return formulario(dados, [mensagem], codigo=400)
    flash(mensagem, "sucesso")
    return redirect(url_for("listar_eventos"), code=303)


@app.route("/eventos/editar/<int:id_evento>", methods=["GET", "POST"])
def editar_evento(id_evento):
    sucesso, atual = dao.buscar_evento_por_id(id_evento)
    if not sucesso:
        return erro_consulta(atual)
    if request.method == "GET":
        dados = dict(atual)
        dados["data_evento"] = atual["data_evento"].strftime("%Y-%m-%d")
        return formulario(dados, editando=True)
    dados = request.form.to_dict()
    dados["id_evento"] = id_evento  # O ID da rota nao pode ser alterado pelo formulario.
    try:
        evento = montar_evento(dados, id_evento, atual["data_cadastro"])
    except ValueError as erro:
        return formulario(dados, [str(erro)], True, 422)
    sucesso, mensagem = dao.alterar_evento(evento)
    if not sucesso:
        return formulario(dados, [mensagem], True, 400)
    flash(mensagem, "sucesso")
    return redirect(url_for("listar_eventos"), code=303)


@app.route("/eventos/excluir/<int:id_evento>", methods=["GET", "POST"])
def excluir_evento(id_evento):
    sucesso, resultado = dao.buscar_evento_por_id(id_evento)
    if not sucesso:
        return erro_consulta(resultado)
    if request.method == "GET":
        return render_template("excluir.html", evento=resultado)
    if request.form.get("confirmar") != "S":
        flash("Exclusão cancelada. O evento foi mantido.", "sucesso")
        return redirect(url_for("listar_eventos"), code=303)
    sucesso, mensagem = dao.excluir_evento(id_evento)
    if not sucesso:
        return erro_consulta(mensagem)
    flash(mensagem, "sucesso")
    return redirect(url_for("listar_eventos"), code=303)


@app.route("/api/eventos")
def api_eventos():
    sucesso, registros = dao.listar_eventos()
    if not sucesso:
        return jsonify(erro=registros), 503
    return jsonify(eventos_para_json(registros))


@app.route("/eventos/exportar/json")
def exportar_json():
    sucesso, registros = dao.listar_eventos()
    if not sucesso:
        return pagina_erro(registros)
    conteudo = json.dumps(eventos_para_json(registros), ensure_ascii=False, indent=4, allow_nan=False)
    return Response(conteudo, mimetype="application/json", headers={"Content-Disposition": 'attachment; filename="eventtech.json"'})


@app.route("/eventos/exportar/html")
def exportar_html():
    sucesso, registros = dao.listar_eventos()
    if not sucesso:
        return pagina_erro(registros)
    conteudo = render_template("exportacao.html", eventos=eventos_para_json(registros))
    return Response(conteudo, mimetype="text/html", headers={"Content-Disposition": 'attachment; filename="eventtech.html"'})


@app.route("/api/cep/<cep>")
def api_cep(cep):
    sucesso, resultado, codigo = consultar_cep(cep)
    return (jsonify(resultado) if sucesso else jsonify(erro=resultado)), codigo


@app.errorhandler(400)
def erro_formulario(erro):
    return pagina_erro("Formulário inválido ou expirado. Abra a página novamente e tente de novo.", 400)


@app.errorhandler(404)
def erro_nao_encontrado(erro):
    return pagina_erro("Página não encontrada.", 404)


@app.errorhandler(500)
def erro_interno(erro):
    return pagina_erro("Ocorreu um erro inesperado. Tente novamente mais tarde.", 500)


if __name__ == "__main__":
    # Servidor da atividade: acesso apenas neste computador e sem traceback na tela.
    app.run(host="127.0.0.1", port=5000, debug=False)
