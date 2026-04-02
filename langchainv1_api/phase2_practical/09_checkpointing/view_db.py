"""
查看 MySQL 数据库内容的简单脚本
"""

import os
from dotenv import load_dotenv

try:
    import mysql.connector
except ImportError:
    print("❌ 请先安装 mysql-connector-python：pip install mysql-connector-python")
    exit(1)

load_dotenv(override=True)

def view_database(db_config):
    """查看 MySQL 数据库的表和数据"""
    
    print(f"\n{'='*70}")
    print(f"查看 MySQL 数据库：{db_config.get('database', 'unknown')}")
    print(f"{'='*70}")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 查看所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        if not tables:
            print("\n⚠️  数据库中没有表")
            return

        print(f"\n📋 数据库中的表：")
        for table in tables:
            print(f"  - {table[0]}")

        # 查看每个表的数据
        for table in tables:
            table_name = table[0]
            print(f"\n📊 表 '{table_name}' 的内容：")

            try:
                # 获取记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  记录数：{count}")

                # 显示前 5 条记录
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                rows = cursor.fetchall()

                if rows:
                    # 获取列名
                    cursor.execute(f"DESCRIBE {table_name}")
                    columns = [col[0] for col in cursor.fetchall()]
                    print(f"  列：{', '.join(columns)}")

                    print("\n  前 5 条记录：")
                    for i, row in enumerate(rows, 1):
                        # 只显示前 3 个字段，避免输出过长
                        display_row = []
                        for j, val in enumerate(row[:3]):
                            if isinstance(val, bytes):
                                # 处理二进制数据
                                display_row.append(f"<bytes: {len(val)}>")
                            elif isinstance(val, str) and len(val) > 100:
                                # 截断长字符串
                                display_row.append(val[:100] + "...")
                            else:
                                display_row.append(str(val))
                        print(f"    [{i}] {tuple(display_row)}")
                    
                    if count > 5:
                        print(f"\n  ... 还有 {count - 5} 条记录未显示")
                else:
                    print("  （空表）")

            except mysql.connector.Error as e:
                print(f"  ❌ 错误：{e}")

        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"\n❌ 数据库连接错误：{err}")
        print("\n💡 请检查:")
        print("  1. .env 文件中的 MYSQL_URL 是否正确")
        print("  2. MySQL 服务是否运行")
        print("  3. 数据库是否存在")

def parse_mysql_url(url:str):
    """
    解析 MySQL 连接 URL
    
    格式：mysql://user:password@host:port/database
    """
    if not url:
        raise ValueError("MYSQL_URL 环境变量未设置")
    
    # 移除前缀
    if url.startswith("mysql://"):
        url = url[8:]
    elif url.startswith("mysql+pymysql://"):
        url = url[16:]
    
    if url.endswith('?charset=utf8mb4'):
        url = url[:-len('?charset=utf8mb4')]
    print(f"解析后的 URL: {url}")
    # 解析各部分
    config = {}
    
    # 分割数据库名
    if '/' in url:
        url_parts = url.split('/', 1)
        url = url_parts[0]
        if len(url_parts) > 1 and url_parts[1]:
            config['database'] = url_parts[1]
    
    # 分割用户信息
    if '@' in url:
        auth_part, host_part = url.rsplit('@', 1)
        
        # 解析用户名和密码
        if ':' in auth_part:
            username, password = auth_part.split(':', 1)
            config['user'] = username
            config['password'] = password
        else:
            config['user'] = auth_part
        
        # 解析主机和端口
        if ':' in host_part:
            host, port = host_part.split(':', 1)
            config['host'] = host
            config['port'] = int(port)
        else:
            config['host'] = host_part
    else:
        # 没有认证信息，只有主机
        config['host'] = url
    
    return config

def main():
    """主函数"""
    print("\n" + "="*70)
    print(" MySQL 数据库查看工具")
    print("="*70)

    # 从环境变量读取 MySQL 连接 URL
    mysql_url = os.getenv("MYSQL_URL")
    
    if not mysql_url:
        print("\n❌ 错误：未找到 MYSQL_URL 环境变量")
        print("\n💡 请在 .env 文件中配置:")
        print("  MYSQL_URL=mysql://user:password@localhost:3306/your_database")
        return

    print(f"\n🔗 连接 URL: {mysql_url[:50]}...")
    
    try:
        # 解析连接信息
        db_config = parse_mysql_url(mysql_url)
        
        print(f"\n📋 连接配置:")
        print(f"  主机：{db_config.get('host', 'unknown')}")
        print(f"  端口：{db_config.get('port', 3306)}")
        print(f"  用户：{db_config.get('user', 'unknown')}")
        print(f"  数据库：{db_config.get('database', 'unknown')}")
        
        # 查看数据库
        view_database(db_config)

        print("\n" + "="*70)
        print(" 完成！")
        print("="*70)
        print("\n💡 提示：")
        print("  - 可以使用 MySQL Workbench 或其他 GUI 工具查看完整内容")
        print("  - 确保数据库中有 LangGraph 创建的 checkpoints 表")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()