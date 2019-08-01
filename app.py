from flask import Flask, render_template, request

app = Flask(__name__)


# 启动服务器后运行的第一个函数，显示对应的网页内容
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('login.html')

# 对登录的用户名和密码进行判断
@app.route('/login', methods=['POST'])
def login():
    # 需要从request对象读取表单内容：
    if request.form['username'] == 'root' and request.form['password'] == 'admin':
        return render_template('admin.html')
    if request.form['username'] == 'usually' and request.form['password'] == 'usually':
        return render_template('admin.html')


if __name__ == '__main__':
    app.run()


# import requests, json
# github_url = "
# data = json.dumps({'name':'test', 'description':'some test repo'})
# r = requests.post(github_url, data, auth=('user', '*****'))
# print r.json
