import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
UPLOAD_FOLDER = 'data'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
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

        periods = int(request.form.get("periods"))
        if not periods:
            flash("Неверное количество периодов")
            return redirect(url_for("index"))

        # Обработка данных
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data.set_index("Date", inplace=True)
        data['Price'] = pd.to_numeric(data['Price'], errors='coerce')
        data.dropna(subset=['Price'], inplace=True)

        plots_and_files = []  # Список для передачи данных в шаблон

        # Построение графика цены и индикаторов
        plt.figure(figsize=(14, 7))
        plt.plot(data.index, data['Price'], label="Price", color="blue")

        if 'SMA' in indicators:
            data['SMA'] = ta.sma(data['Price'], length=periods)
            plt.plot(data.index, data['SMA'].shift(-periods), label=f"SMA-{periods}", color="orange")

        if 'BB' in indicators:
            bb = data.ta.bbands(close=data['Price'], length=periods)
            plt.fill_between(data.index, bb[f'BBL_{periods}_2.0'].shift(-periods), bb[f'BBU_{periods}_2.0'].shift(-periods), color="gray", alpha=0.3, label="Bollinger Bands")

        plt.title("Технический анализ")
        plt.xlabel("Дата")
        plt.ylabel("Цена закрытия")
        plt.legend()
        plt.grid()

        # Сохранение основного графика
        img_path = os.path.join(RESULT_FOLDER, "main_chart.png")
        plt.savefig(img_path)
        plt.close()
        plots_and_files.append(("main_chart.png", "Основной график"))

        # Если выбран RSI, создаем отдельный график
        if 'RSI' in indicators:
            data['RSI'] = ta.rsi(data['Price'], length=periods)
            plt.figure(figsize=(14, 7))
            plt.plot(data.index, data['RSI'].shift(-periods), label="RSI", color="purple")
            plt.title("RSI Analysis")
            plt.xlabel("Дата")
            plt.ylabel("RSI")
            plt.legend()
            plt.grid()

            img_path = os.path.join(RESULT_FOLDER, "rsi_chart.png")
            plt.savefig(img_path)
            plt.close()
            plots_and_files.append(("rsi_chart.png", "RSI график"))

        return render_template("analysis.html", plots_and_files=plots_and_files)

    except Exception as e:
        flash(f"Ошибка анализа: {e}")
        return redirect(url_for("index"))

@app.route("/download/<filename>")
def download(filename):
    filepath = os.path.join(RESULT_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        flash("Файл не найден.")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
