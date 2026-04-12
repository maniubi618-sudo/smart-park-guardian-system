import pymysql

# 读取SQL文件内容
with open('yolo_safety.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

try:
    # 连接到数据库
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='123456',
        database='yolo_safety'
    )
    cursor = conn.cursor()
    
    # 执行SQL语句
    # 分割SQL语句并执行
    sql_statements = sql_content.split(';')
    for statement in sql_statements:
        statement = statement.strip()
        if statement:
            try:
                cursor.execute(statement)
                conn.commit()
                print(f"执行SQL成功: {statement[:50]}...")
            except Exception as e:
                print(f"执行SQL失败: {statement[:50]}...")
                print(f"错误信息: {str(e)}")
                conn.rollback()
    
    print("数据库初始化完成！")
    
    # 关闭连接
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"数据库操作失败：{str(e)}")
