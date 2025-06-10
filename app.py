from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Dados globais
usuarios = []
contas = []
AGENCIA = "0001"
LIMITE_SAQUES = 3
LIMITE_SAQUE_VALOR = 500.0

def buscar_conta(numero_conta):
    for conta in contas:
        if conta["numero_conta"] == numero_conta:
            return conta
    return None

def criar_usuario(nome, data_nascimento, bairro, cidade, logradouro, estado, cpf, sigla_estado):
    return {
        "nome": nome,
        "data_nascimento": data_nascimento,
        "bairro": bairro,
        "cidade": cidade,
        "logradouro": logradouro,
        "estado": estado,
        "cpf": cpf,
        "sigla_estado": sigla_estado,
    }

def criar_conta_para_usuario(usuario):
    numero_conta = len(contas) + 1
    conta = {
        "agencia": AGENCIA,
        "numero_conta": numero_conta,
        "usuario": usuario,
        "saldo": 0.0,
        "extrato": "",
        "numero_saques": 0,
    }
    contas.append(conta)
    return conta

def depositar(saldo, valor, extrato):
    if valor > 0:
        saldo += valor
        extrato += f"Depósito: R$ {valor:.2f}\n"
        return saldo, extrato, "Depósito realizado com sucesso!", "success"
    else:
        return saldo, extrato, "Operação falhou! O valor informado é inválido.", "error"

def sacar(*, saldo, valor, extrato, limite, numero_saques, limite_saques):
    if valor <= 0:
        return saldo, extrato, numero_saques, "Operação falhou! O valor informado é inválido.", "error"
    if valor > saldo:
        return saldo, extrato, numero_saques, "Operação falhou! Você não tem saldo suficiente.", "error"
    if valor > limite:
        return saldo, extrato, numero_saques, "Operação falhou! O valor do saque excede o limite.", "error"
    if numero_saques >= limite_saques:
        return saldo, extrato, numero_saques, "Operação falhou! Número máximo de saques excedido.", "error"

    saldo -= valor
    extrato += f"Saque: R$ {valor:.2f}\n"
    numero_saques += 1
    return saldo, extrato, numero_saques, "Saque realizado com sucesso!", "success"


@app.route('/', methods=["GET"])
def index():
    numero_conta = request.args.get("conta", type=int)
    conta = None
    if numero_conta:
        conta = buscar_conta(numero_conta)

    if conta:
        usuario = conta["usuario"]
        return render_template("index.html",
                               numero_conta=numero_conta,
                               nome_usuario=usuario["nome"],
                               saldo=f"{conta['saldo']:.2f}",
                               extrato_content=conta["extrato"] if conta["extrato"] else "Não foram realizadas movimentações.",
                               message=None,
                               message_type=None)
    else:
        return render_template("criar_conta.html", message=None)

@app.route('/criar-conta', methods=["POST"])
def criar_conta_route():
    # Receber dados do formulário
    nome = request.form.get("nome")
    data_nascimento = request.form.get("data_nascimento")
    bairro = request.form.get("bairro")
    cidade = request.form.get("cidade")
    logradouro = request.form.get("logradouro")
    estado = request.form.get("estado")
    cpf = request.form.get("cpf")
    sigla_estado = request.form.get("sigla_estado")

    usuario = criar_usuario(nome, data_nascimento, bairro, cidade, logradouro, estado, cpf, sigla_estado)
    conta = criar_conta_para_usuario(usuario)
    return redirect(url_for('index', conta=conta["numero_conta"]))

@app.route('/depositar', methods=['POST'])
def depositar_route():
    numero_conta = request.args.get("conta", type=int)
    conta = buscar_conta(numero_conta)
    if not conta:
        return redirect(url_for('index'))

    try:
        valor = float(request.form['valor'])
    except (ValueError, KeyError):
        valor = -1

    saldo, extrato, message, message_type = depositar(conta['saldo'], valor, conta['extrato'])

    conta['saldo'] = saldo
    conta['extrato'] = extrato

    usuario = conta["usuario"]
    return render_template("index.html",
                           numero_conta=numero_conta,
                           nome_usuario=usuario["nome"],
                           saldo=f"{saldo:.2f}",
                           extrato_content=extrato if extrato else "Não foram realizadas movimentações.",
                           message=message,
                           message_type=message_type)

@app.route('/sacar', methods=['POST'])
def sacar_route():
    numero_conta = request.args.get("conta", type=int)
    conta = buscar_conta(numero_conta)
    if not conta:
        return redirect(url_for('index'))

    try:
        valor = float(request.form['valor'])
    except (ValueError, KeyError):
        valor = -1

    saldo, extrato, numero_saques, message, message_type = sacar(
        saldo=conta['saldo'],
        valor=valor,
        extrato=conta['extrato'],
        limite=LIMITE_SAQUE_VALOR,
        numero_saques=conta['numero_saques'],
        limite_saques=LIMITE_SAQUES
    )

    conta['saldo'] = saldo
    conta['extrato'] = extrato
    conta['numero_saques'] = numero_saques

    usuario = conta["usuario"]
    return render_template("index.html",
                           numero_conta=numero_conta,
                           nome_usuario=usuario["nome"],
                           saldo=f"{saldo:.2f}",
                           extrato_content=extrato if extrato else "Não foram realizadas movimentações.",
                           message=message,
                           message_type=message_type)

@app.route('/extrato', methods=['GET'])
def extrato_route():
    numero_conta = request.args.get("conta", type=int)
    conta = buscar_conta(numero_conta)
    if not conta:
        return "Conta não encontrada."

    return conta["extrato"] if conta["extrato"] else "Não foram realizadas movimentações."


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
