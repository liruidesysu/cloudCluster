import traceback

from flask import Flask, render_template, request
import pymysql

app = Flask(__name__)


# 默认路径访问登录页面
@app.route('/', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

# 默认路径访问注册页面
@app.route('/regist')
def regist():
    return render_template('regist.html')

@app.route('/registuser')

def getRigistRequest():
    # 把用户名和密码注册到数据库中
    # 连接数据库,此前在数据库中创建数据库TESTDB
    db = pymysql.connect("localhost","root","liruide","cluster" )

    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # SQL 插入语句
    sql = "INSERT INTO user(user, password) VALUES ("+request.args.get('user')+", "+request.args.get('password')+")"

    try:
        # 执行sql语句
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
         # 注册成功之后跳转到登录页面
        return render_template('login.html')
    except:
        #抛出错误信息
        traceback.print_exc()
        # 如果发生错误则回滚
        db.rollback()
        return '注册失败'
    # 关闭数据库连接
    db.close()


if __name__ == '__main__':
    app.run()


# import requests, json
# github_url = "
# data = json.dumps({'name':'test', 'description':'some test repo'})
# r = requests.post(github_url, data, auth=('user', '*****'))
# print r.json
