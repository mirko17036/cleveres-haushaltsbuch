
from flask import Flask, render_template_string, request, send_file
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)
eintraege = []

html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cleveres Haushaltsbuch</title>
    <style>
        body { font-family: Arial; padding: 20px; background: #f9f9f9; color: #333; }
        .startscreen { text-align: center; margin-top: 100px; }
        .logo { width: 100px; }
        .btn-start { padding: 12px 24px; background: #ffb400; border: none; font-size: 16px; cursor: pointer; }
        .container { max-width: 500px; margin: auto; background: white; padding: 20px; border-radius: 10px; }
        input, select, button { width: 100%; margin-top: 10px; padding: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
    </style>
</head>
<body>
    {% if not gestartet %}
    <div class="startscreen">
        <img src="/static/logo.png" class="logo">
        <h1>Cleveres Haushaltsbuch</h1>
        <p>Behalte deine Einnahmen & Ausgaben im Blick. Kostenlos & einfach.</p>
        <form method="get"><button class="btn-start" name="starten" value="1">Jetzt starten</button></form>
    </div>
    {% else %}
    <div class="container">
        <h2>Haushaltsbuch</h2>
        <form method="POST">
            <input type="number" step="0.01" name="betrag" placeholder="Betrag (€)" required>
            <select name="typ"><option value="Einnahme">Einnahme</option><option value="Ausgabe">Ausgabe</option></select>
            <input type="text" name="kategorie" placeholder="Kategorie" required>
            <button type="submit">Hinzufügen</button>
        </form>

        <form method="GET">
            <select name="monat" onchange="this.form.submit()">
                <option value="">Alle Monate</option>
                {% for monat in monate %}
                <option value="{{ monat }}" {% if monat == ausgewaehlter_monat %}selected{% endif %}>{{ monat }}</option>
                {% endfor %}
            </select>
            <input type="hidden" name="starten" value="1">
        </form>

        {% if eintraege %}
        <table>
            <tr><th>Datum</th><th>Typ</th><th>Betrag</th><th>Kategorie</th></tr>
            {% for e in eintraege %}
            <tr><td>{{ e['datum'] }}</td><td>{{ e['typ'] }}</td><td>{{ e['betrag'] }}</td><td>{{ e['kategorie'] }}</td></tr>
            {% endfor %}
        </table>
        <p><strong>Saldo: {{ saldo }} €</strong></p>
        <a href="/export_csv?monat={{ ausgewaehlter_monat }}">📁 CSV</a> |
        <a href="/export_pdf?monat={{ ausgewaehlter_monat }}">📄 PDF</a>
        {% endif %}
    </div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    gestartet = "starten" in request.args
    if request.method == "POST":
        eintraege.append({
            "datum": datetime.now().strftime("%Y-%m-%d"),
            "typ": request.form["typ"],
            "betrag": float(request.form["betrag"]),
            "kategorie": request.form["kategorie"]
        })

    monat = request.args.get("monat", "")
    gefiltert = [e for e in eintraege if monat == "" or e["datum"].startswith(monat)]
    monate = sorted(set(e["datum"][:7] for e in eintraege))
    saldo = round(sum(e["betrag"] if e["typ"] == "Einnahme" else -e["betrag"] for e in gefiltert), 2)

    return render_template_string(html_template, gestartet=gestartet, eintraege=gefiltert, saldo=saldo, monate=monate, ausgewaehlter_monat=monat)

@app.route("/export_csv")
def export_csv():
    monat = request.args.get("monat", "")
    df = pd.DataFrame([e for e in eintraege if monat == "" or e["datum"].startswith(monat)])
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="haushaltsbuch.csv", mimetype="text/csv")

@app.route("/export_pdf")
def export_pdf():
    monat = request.args.get("monat", "")
    gefiltert = [e for e in eintraege if monat == "" or e["datum"].startswith(monat)]
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    y = 800
    c.drawString(50, y, "Haushaltsbuch PDF")
    y -= 30
    for e in gefiltert:
        c.drawString(50, y, f"{e['datum']} | {e['typ']} | {e['betrag']} € | {e['kategorie']}")
        y -= 20
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="haushaltsbuch.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
