from flask import Flask, request, render_template, redirect, url_for, send_file
import sqlite3
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

app = Flask(__name__)

# 设置中文字体
font_path = 'C:\\Windows\\Fonts\\SimHei.ttf'  # 使用你实际的字体文件路径
prop = font_manager.FontProperties(fname=font_path)

plt.rcParams['font.family'] = prop.get_name()  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号问题


# 初始化 SQLite 数据库并创建表格（如果尚未创建）
def init_db():
    conn = sqlite3.connect('survey_data.db')  # 创建/连接数据库文件
    cursor = conn.cursor()

    # 创建表格（如果表格不存在）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS survey_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        q1 INTEGER,
        q2 INTEGER,
        q3 INTEGER,
        q4 INTEGER,
        q5 INTEGER,
        q6 INTEGER
    )
    ''')

    conn.commit()
    conn.close()


# 调用初始化数据库函数
init_db()


# 保存数据到 SQLite 数据库
def save_to_db(data):
    conn = sqlite3.connect('survey_data.db')  # 连接 SQLite 数据库
    cursor = conn.cursor()

    # 插入新数据到数据库
    cursor.execute('''
    INSERT INTO survey_results (q1, q2, q3, q4, q5, q6)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['q1'], data['q2'], data['q3'], data['q4'], data['q5'], data['q6']))

    conn.commit()
    conn.close()


# 计算问题均值并生成雷达图
def generate_radar_chart():
    # 从 SQLite 数据库获取所有问卷数据
    conn = sqlite3.connect('survey_data.db')
    cursor = conn.cursor()

    # 获取所有记录
    cursor.execute('SELECT q1, q2, q3, q4, q5, q6 FROM survey_results')
    rows = cursor.fetchall()  # 获取所有的答卷数据

    conn.close()

    # 将数据转换为 pandas DataFrame
    df = pd.DataFrame(rows, columns=["q1", "q2", "q3", "q4", "q5", "q6"])

    # 计算每个问题的均值
    mean_values = df.mean()

    # 打印均值
    print(f"Calculated mean values: \n{mean_values}")

    # 雷达图的标签
    categories = ["运动示范能力", "语言表达能力", "课堂创新能力", "课堂组织能力", "课堂实践效果", "教案设计能力"]

    # 确保均值列表的长度为 6
    values = mean_values.tolist()

    # 闭合雷达图
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    # 创建雷达图
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='blue', alpha=0.25)
    ax.plot(angles, values, color='blue', linewidth=2)

    # 添加每个问题的均值文本标记
    for i, value in enumerate(values[:-1]):
        ax.text(angles[i], value + 0.1, f"{value:.2f}", horizontalalignment='center', size=12, color='blue',
                fontweight='semibold')

    # 设置标签和角度
    categories.append(categories[0])
    ax.set_yticklabels([])
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, fontstyle='italic', fontsize=12)

    # 保存雷达图
    plt.tight_layout()
    plt.savefig('static/radar_chart.png')
    print(f"Radar chart saved to: static/radar_chart.png")


# 根路由：问卷表单
@app.route('/', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        # 获取表单数据
        data = {
            "q1": int(request.form['q1']),
            "q2": int(request.form['q2']),
            "q3": int(request.form['q3']),
            "q4": int(request.form['q4']),
            "q5": int(request.form['q5']),
            "q6": int(request.form['q6'])
        }
        # 保存数据到数据库
        save_to_db(data)

        # 计算均值并生成雷达图
        generate_radar_chart()

        # 重定向到显示雷达图的页面
        return redirect(url_for('show_radar_chart'))

    # 如果是 GET 请求，渲染问卷表单
    return render_template('survey_form.html')


# 显示雷达图
@app.route('/radar_chart')
def show_radar_chart():
    # 显示生成的雷达图
    return send_file('static/radar_chart.png', mimetype='image/png')


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=5001)
