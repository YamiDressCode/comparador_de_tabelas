from flask import Flask, request
import os
import pandas as pd
import google.generativeai as genai

# =======================
# 🔧 CONFIGURAÇÕES INICIAIS
# =======================

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Substitua pela sua chave da API Gemini
genai.configure(api_key="xxxxxxxxxxxxxxxxxxxxxxxx")

# =======================
# 🧱 HTML INCORPORADO
# =======================

INDEX_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <title>Comparador de Tabelas</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #f3f4f6;
      color: #222;
      text-align: center;
      padding: 40px;
    }
    form {
      background: white;
      padding: 30px;
      border-radius: 10px;
      display: inline-block;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    input, button {
      margin-top: 10px;
      padding: 10px;
      font-size: 16px;
    }
    button {
      background: #007BFF;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
    }
    button:hover {
      background: #0056b3;
    }
  </style>
</head>
<body>
  <h2>🔍 Comparador de Tabelas - Ministério</h2>
  <form action="/analisar" method="POST" enctype="multipart/form-data">
    <label>Arquivo Consolidado:</label><br>
    <input type="file" name="arquivo1" accept=".xlsx" required><br><br>

    <label>Arquivo Específico:</label><br>
    <input type="file" name="arquivo2" accept=".xlsx" required><br><br>

    <button type="submit">Analisar e Gerar Relatório</button>
  </form>
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <title>Resultado da Análise</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #fafafa;
      color: #222;
      padding: 40px;
    }
    .resultado {
      background: #fff;
      padding: 20px;
      border-radius: 10px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      margin-top: 20px;
    }
    a {
      display: inline-block;
      margin-top: 20px;
      text-decoration: none;
      background: #007BFF;
      color: white;
      padding: 10px 20px;
      border-radius: 5px;
    }
    a:hover {
      background: #0056b3;
    }
  </style>
</head>
<body>
  <h2>📊 Resultado da Comparação</h2>
  <p><strong>Arquivos analisados:</strong> {{ file1 }} e {{ file2 }}</p>
  <div class="resultado">
    {{ result_html | safe }}
  </div>
  <a href="/">⬅ Voltar</a>
</body>
</html>
"""

# =======================
# 🧠 FUNÇÕES DE ANÁLISE
# =======================

def read_excel_as_markdown(filepath):
    """Lê todas as abas do Excel e retorna texto formatado em Markdown."""
    excel = pd.read_excel(filepath, sheet_name=None)
    text_parts = []
    for sheet_name, df in excel.items():
        df_preview = df.head(20)
        text_parts.append(f"### Aba: {sheet_name}\n")
        text_parts.append(df_preview.to_markdown(index=False))
        text_parts.append("\n\n")
    return "\n".join(text_parts)

def process_files(file1_path, file2_path):
    """Processa e compara os arquivos Excel usando o Gemini."""
    try:
        data1 = read_excel_as_markdown(file1_path)
        data2 = read_excel_as_markdown(file2_path)

        prompt = f"""
        Você é um analista de dados especialista em controle de custos de atendimento.
        Compare as duas tabelas a seguir, identifique discrepâncias e gere um relatório
        completo em HTML contendo:

        - Comparação dos custos faturados e não faturados;
        - Gráficos ou tabelas comparativas (pode usar HTML simples);
        - Análise de diferenças por tipo de atendimento (URA, Chatbot, Humano etc.);
        - Observações sobre inconsistências detectadas;
        - Um resumo consolidado final.

        ### Tabela Consolidada (Geral):
        {data1}

        ### Tabela Específica:
        {data2}
        """

        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content(prompt, request_options={"timeout": 600})

        return response.text or "<p>Erro: Nenhuma resposta gerada pela IA.</p>"
    except Exception as e:
        return f"<p>Erro ao processar os arquivos: {str(e)}</p>"

# =======================
# 🌐 ROTAS FLASK
# =======================

@app.route('/')
def index():
    return INDEX_HTML

@app.route('/analisar', methods=['POST'])
def analisar():
    try:
        file1 = request.files['arquivo1']
        file2 = request.files['arquivo2']

        path1 = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        path2 = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)
        file1.save(path1)
        file2.save(path2)

        result_html = process_files(path1, path2)

        # Renderização manual simples
        html = RESULT_HTML.replace("{{ file1 }}", file1.filename)
        html = html.replace("{{ file2 }}", file2.filename)
        html = html.replace("{{ result_html | safe }}", result_html)
        return html

    except Exception as e:
        return f"<h3>Erro: {str(e)}</h3>"

# =======================
# 🚀 EXECUÇÃO
# =======================

if __name__ == '__main__':
    app.run(debug=True)

