from flask import Flask, request, render_template, redirect, url_for, send_file
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
import mysql.connector  # 使用 mysql.connector 替代 sqlite3
import pandas as pd
from pycirclize import Circos

app = Flask(__name__)

# 设置中文字体
font_path = 'C:\\Windows\\Fonts\\SimHei.ttf'  # 使用你实际的字体文件路径
prop = font_manager.FontProperties(fname=font_path)

plt.rcParams['font.family'] = prop.get_name()  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号问题

# MySQL 连接参数（根据你自己的配置修改）
MYSQL_HOST = 'localhost'         # MySQL 服务器地址
MYSQL_USER = 'survey_user'       # MySQL 用户名
MYSQL_PASSWORD = '1203Zht..'      # MySQL 密码
MYSQL_DB = 'survey_data'         # 使用的数据库名称

# 初始化 MySQL 数据库并创建表格（如果尚未创建）
def init_db():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        cursor = conn.cursor()

        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS survey_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            q1 INT,
            q2 INT,
            q3 INT,
            q4 INT,
            q5 INT,
            q6 INT
        )
        ''')

        conn.commit()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

# 调用初始化数据库函数
init_db()


# 保存数据到 MySQL 数据库
def save_to_db(data):
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()

    # 插入新数据到数据库
    cursor.execute(''' 
    INSERT INTO survey_results (q1, q2, q3, q4, q5, q6) 
    VALUES (%s, %s, %s, %s, %s, %s)
    ''', (data['q1'], data['q2'], data['q3'], data['q4'], data['q5'], data['q6']))

    conn.commit()
    conn.close()


# 连接 MySQL 数据库
def get_db_connection():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    return conn


# 获取所有问卷数据
@app.route('/view_survey_data')
def view_survey_data():
    conn = get_db_connection()  # 获取数据库连接
    cursor = conn.cursor()

    cursor.execute('SELECT id, q1, q2, q3, q4, q5, q6 FROM survey_results')
    rows = cursor.fetchall()  # 获取所有数据

    conn.close()  # 关闭连接

    # 将数据库中的数据传递给前端模板
    return render_template('view_data.html', rows=rows)


# 删除数据库中的所有问卷数据
def clear_survey_data():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()

    cursor.execute('DELETE FROM survey_results')
    conn.commit()
    conn.close()


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

        # 打印用户提交的问卷数据
        print("User submitted data:")
        print(f"q1: {data['q1']}, q2: {data['q2']}, q3: {data['q3']}, q4: {data['q4']}, q5: {data['q5']}, q6: {data['q6']}")

        # 保存数据到数据库
        save_to_db(data)

        # 在保存数据后直接更新雷达图
        generate_radar_chart()

        # 重定向到“感谢您的配合”页面
        return redirect(url_for('thank_you'))

    # 如果是 GET 请求，渲染问卷表单
    return render_template('survey_form.html')


# 路由：感谢页面
@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')


# 生成雷达图并保存到 static 目录
def generate_radar_chart():
    # 从 MySQL 数据库获取所有问卷数据
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()

    # 获取所有记录
    cursor.execute('SELECT q1, q2, q3, q4, q5, q6 FROM survey_results')
    rows = cursor.fetchall()  # 获取所有的答卷数据

    conn.close()

    # 将数据转换为 pandas DataFrame
    df = pd.DataFrame(
        rows,  # 直接传入数据库返回的行数据
        columns=["课堂创新能力", "语言表达能力", "运动示范能力", "教案设计能力", "课堂实践能力", "课堂组织能力"]  # 这些是列名
    )

    # 计算每个问题的均值
    mean_values = df.mean()

    # 打印均值
    print(f"Calculated mean values: \n{mean_values}")

    # 将 mean_values 转换为 DataFrame 格式，并设置行索引
    mean_df = pd.DataFrame(mean_values).T  # 转换为单行 DataFrame
    mean_df.index = ['student1']  # 设置行索引为 'mean'，避免 KeyError

    # 设置雷达图的最大值
    vmax = 5  # 设定最大值为 5
    label_offset = 80  # 标签距图形的偏移量，可调整

    # 使用 Circos 绘制雷达图
    circos = Circos.radar_chart(
        mean_df,  # 传入转换后的 DataFrame
        vmax=vmax,
        marker_size=6,
        grid_interval_ratio=0.2,
    )

    # 绘制图形并设置图例
    fig = circos.plotfig()

    # 添加均值标签，放到雷达图的最外侧
    for i, (col, value) in enumerate(mean_values.items()):
        # 使用 vmax + label_offset 来确保标签放在雷达图的外侧
        circos.ax.text(
            i,
            vmax + label_offset,  # 将标签放置在最大值的外侧
            f"{value:.2f}",  # 标签的文本
            ha='center',  # 标签水平居中
            va='bottom',  # 标签垂直向上
            fontsize=12,  # 字体大小
            fontweight='bold'  # 字体加粗
        )

    _ = circos.ax.legend(loc="upper right", fontsize=10)
    fig.savefig("static/radar_chart_circos.png")  # 保存为图片
    print(f"Radar chart saved to: static/radar_chart_circos.png")


# 路由：显示雷达图
@app.route('/radar_chart')
def show_radar_chart():
    # 返回生成的雷达图并设置响应头，避免缓存
    response = send_file('static/radar_chart_circos.png', mimetype='image/png')
    response.cache_control.no_cache = True  # 禁止缓存
    response.cache_control.no_store = True  # 不缓存
    response.cache_control.must_revalidate = True  # 强制重新验证
    return response


# 清空数据
@app.route('/clear_data', methods=['GET'])
def clear_data():
    clear_survey_data()
    return "数据库中的问卷数据已成功清空！"


# 测试数据库连接
@app.route('/test_db')
def test_db():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        cursor = conn.cursor()
        cursor.execute('SELECT 1')  # 测试查询
        result = cursor.fetchone()
        conn.close()
        return "Database connection test successful: " + str(result)
    except mysql.connector.Error as err:
        return f"Database connection failed: {err}"

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=5001)
