

from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def setup_sqlite3_pragmas(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        print("setup_sqlite3_pragmas")
        cursor = connection.cursor()
        # 设置缓存大小为64MB (负值表示KiB)
        cursor.execute('PRAGMA cache_size = -65535')
        # 启用写前日志模式
        cursor.execute('PRAGMA journal_mode = WAL')
        # 增加临时存储空间到内存
        cursor.execute('PRAGMA temp_store = MEMORY')

