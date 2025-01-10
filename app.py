import os
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
UPLOAD_FOLDER = 'data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.secret_key = 'your_secret_key'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files.get("file")
        if not file:
            flash("Пожалуйста, загрузите файл.")
            return redirect(url_for("index"))

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Загрузка данных
        data = pd.read_csv(filepath)
        data.columns = data.columns.str.strip()

        # Проверка на наличие необходимых колонок
        if 'Date' not in data.columns or 'Price' not in data.columns:
            flash("Файл должен содержать колонки 'Date' и 'Price'.")
            return redirect(url_for("index"))

        # Получение выбранных индикаторов
        indicators = request.form.getlist("indicators")
        if not indicators:
            flash("Выберите хотя бы один индикатор для анализа.")
            return redirect(url_for("index"))

        days = int(request.form.get("days"))
        if not days:
            flash("Неверное количество дней")
            return redirect(url_for("index"))

        # Обработка данных
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data.set_index("Date", inplace=True)
        data['Price'] = pd.to_numeric(data['Price'], errors='coerce')
        data.dropna(subset=['Price'], inplace=True)

        plot_urls = []

        # Построение графика цены и индикаторов
        plt.figure(figsize=(14, 7))
        plt.plot(data.index, data['Price'], label="Price", color="blue")

        if 'SMA' in indicators:
            data['SMA'] = ta.sma(data['Price'], length=days)
            plt.plot(data.index, data['SMA'].shift(-days), label=f"SMA-{days}", color="orange")

        if 'BB' in indicators:
            bb = data.ta.bbands(close=data['Price'], length=days)
            plt.fill_between(data.index, bb[f'BBL_{days}_2.0'].shift(-days), bb[f'BBU_{days}_2.0'].shift(-days), color="gray", alpha=0.3, label="Bollinger Bands")

        plt.title("Технический анализ")
        plt.xlabel("Дата")
        plt.ylabel("Цена закрытия")
        plt.legend()
        plt.grid()

        # Сохранение основного графика
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_urls.append(base64.b64encode(img.getvalue()).decode())

        # Если выбран RSI, создаем отдельный график
        if 'RSI' in indicators:
            data['RSI'] = ta.rsi(data['Price'], length=days)
            plt.figure(figsize=(14, 7))
            plt.plot(data.index, data['RSI'].shift(-days), label="RSI", color="purple")
            plt.title("RSI Analysis")
            plt.xlabel("Дата")
            plt.ylabel("RSI")
            plt.legend()
            plt.grid()

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_urls.append(base64.b64encode(img.getvalue()).decode())

        return render_template("analysis.html", plot_urls=plot_urls)

    except Exception as e:
        flash(f"Ошибка анализа: {e}")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
