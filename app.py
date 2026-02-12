from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os, io, csv, hashlib, datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'kawai-secret-douglas'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return '<h1>🌸 Kawai Lingerie API OK! Acesse: <a href="/entrada">Entrada</a> | <a href="/vendas">Vendas</a> | <a href="/dashboard">Dashboard</a></h1>'

@app.route('/initdb')
def initdb():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS produtos (
                cod TEXT PRIMARY KEY, nome_input TEXT, ref TEXT, tipo TEXT, custo_fornecedor REAL,
                frete REAL, preco_venda REAL, foto TEXT, qtd_estoque INTEGER DEFAULT 0,
                fornecedor_nome TEXT, fornecedor_contato TEXT, fornecedor_estado TEXT
            );
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY, vendedor TEXT, bairro TEXT, cod_produto TEXT,
                qtd INTEGER, preco_venda REAL, perc_desconto REAL, subtotal REAL,
                data_hora TEXT, cpf_cliente TEXT
            );
        ''')
        db.commit()
    return 'DB OK! Vá para /entrada'

@app.route('/entrada', methods=['GET', 'POST'])
def entrada():
    if request.method == 'POST':
        cod = request.form['cod']
        qtd = int(request.form['qtd'])
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT OR IGNORE INTO produtos (cod, nome_input, ref, tipo, custo_fornecedor, frete, preco_venda, qtd_estoque, fornecedor_nome) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (cod, request.form['nome'], request.form['ref'], request.form['tipo'], 
                    float(request.form['custo']), float(request.form['frete']), float(request.form['preco']),
                    qtd, request.form['fornecedor']))
        cur.execute("UPDATE produtos SET qtd_estoque = qtd_estoque + ? WHERE cod = ?", (qtd, cod))
        db.commit()
        db.close()
        return '<h2>✅ Produto ' + cod + ' ADICIONADO!</h2><a href="/entrada">Novo</a>'
    return '''
    <h2>🌸 Kawai - Entrada Estoque</h2>
    <form method="POST">
        Código: <input name="cod" required><br>
        Nome input: <input name="nome"><br>
        Referência: <input name="ref"><br>
        Tipo: <select name="tipo">
            <option>calcinha</option><option>sutiã</option><option>conjunto lingerie</option>
            <option>top</option><option>leg</option><option>short</option>
        </select><br>
        Custo fornecedor: <input name="custo" type="number" step="0.01"><br>
        Frete: <input name="frete" type="number" step="0.01"><br>
        Preço venda: <input name="preco" type="number" step="0.01"><br>
        Quantidade: <input name="qtd" type="number"><br>
        Fornecedor: <input name="fornecedor"><br>
        <button>Adicionar!</button>
    </form>
    '''

@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO vendas (vendedor, bairro, cod_produto, qtd, preco_venda, perc_desconto, subtotal, data_hora) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (request.form['vendedor'], request.form['bairro'], request.form['cod'],
                    int(request.form['qtd']), float(request.form['preco']), 
                    float(request.form.get('desconto', 0)), float(request.form['subtotal']),
                    datetime.datetime.now().isoformat()))
        cur.execute("UPDATE produtos SET qtd_estoque = qtd_estoque - ? WHERE cod = ?", 
                   (int(request.form['qtd']), request.form['cod']))
        db.commit()
        db.close()
        return '<h2>✅ VENDA OK!</h2><a href="/vendas">Nova venda</a>'
    return '''
    <h2>💰 Vendas Kawai</h2>
    <form method="POST">
        Vendedor: <input name="vendedor"><br>
        Bairro: <input name="bairro"><br>
        Código: <input name="cod"><br>
        Qtd: <input name="qtd" type="number"><br>
        Preço: <input name="preco" type="number" step="0.01"><br>
        Desconto %: <input name="desconto" type="number" step="0.01" value="0"><br>
        Subtotal: <input name="subtotal" type="number" step="0.01"><br>
        <button>Vender!</button>
    </form>
    '''

@app.route('/dashboard')
def dashboard():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT SUM(preco_venda * qtd_estoque) as faturamento FROM produtos")
    faturamento = cur.fetchone()['faturamento'] or 0
    cur.execute("SELECT SUM(subtotal) as vendas FROM vendas")
    vendas = cur.fetchone()['vendas'] or 0
    cur.execute("SELECT * FROM produtos WHERE qtd_estoque < 10")
    baixo = cur.fetchall()
    db.close()
    return f'''
    <h2>📊 Dashboard Kawai</h2>
    <p>💰 Estoque Valor: R${faturamento:.2f} | Vendas: R${vendas:.2f}</p>
    <h3>⚠️ Estoque Baixo:</h3>
    {' | '.join([r['cod'] for r in baixo]) or 'OK!'}
    <br><a href="/reset">RESET (senha: ceci)</a>
    '''

@app.route('/reset', methods=['POST'])
def reset():
    if request.form.get('senha') == 'ceci':
        db = get_db()
        db.executescript('DELETE FROM vendas; DELETE FROM produtos;')
        db.commit()
        db.close()
        return '🔥 RESET OK!'
    return '❌ Senha errada!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
