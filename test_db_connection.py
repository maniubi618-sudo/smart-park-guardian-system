import pymysql

try:
    # 尝试连接数据库
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='123456',
        database='yolo_safety'
    )
    print("数据库连接成功！")
    conn.close()
except Exception as e:
    print(f"数据库连接失败：{str(e)}")
