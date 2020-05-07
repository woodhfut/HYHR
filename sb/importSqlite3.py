import sqlite3
import pandas as pd
import datetime
from calendar import monthrange

db = sqlite3.connect('../db.sqlite3')

cur = db.cursor()
names = {}
df = pd.read_excel('book_hy.xlsx')

for  row in df.values:
    #customer info
    name = row[7].strip()
    if name in names:
        continue
    pid = ' ' if pd.isnull(row[8]) else row[8].strip()
    
    phone = str(row[9])[0:11] if not pd.isnull(row[9]) else ''
    hukou = 'N' if row[11] in [1629.17, 703.26] else 'C'
    status = 1 if not pd.isnull(row[11]) else 0
    #note = str(row[16])
    # if note and  '个税' in note:
    #     status |=4
    if not pd.isnull(row[12]):
        status |=2
    if not pd.isnull(row[15]):
        status |=8
    print(f'{name} {pid} {phone} {hukou} {status} {row[12]}')
    cur.execute(f'insert into sb_customer("name", "pid", "phone", "hukou", "status") \
        values("{name}", "{pid}", "{phone}", "{hukou}","{status}")')
    names[name]= name

orders = {}
serivces = {}
for row in df.values:
    name = row[7].strip()
    ret = cur.execute(f'select id from sb_customer where name = "{name}"')
    customer = ret.fetchone()[0]
    #print(customer)
    bdate = datetime.date(row[0], row[1], 1)
    edate = datetime.date(row[3], row[4], monthrange(row[3], row[4])[1])
    # if row[4]>1:
    #     edate= datetime.date(row[3], row[4]-1, monthrange(row[3], row[4]-1)[1])
    # else:
    #     edate = datetime.date(row[3]-1, 12, monthrange(row[3]-1, 12)[1])

    fee = float(row[14]) if not pd.isnull(row[14]) else 0
    paymethod = row[6]
    
    ret = cur.execute(f'select id from sb_service where name = "服务费"')
    service = ret.fetchone()[0]
    if not (name, bdate, edate, service) in serivces:
        cur.execute(f'insert into sb_service_order("customer_id", "service_id", "svalidfrom", "svalidto", "stotal_price", "paymethod", "orderDate") \
            values("{customer}", "{service}", "{bdate}", "{edate}", "{fee}","{paymethod}", "{datetime.date.today()}")')
        serivces[(name, bdate, edate, service)] = True
    
    if not pd.isnull(row[10]):
        ret = cur.execute(f'select id from sb_product where name = "社保"')
        product = ret.fetchone()[0]
        product_base = float(row[10])
        fee = float(row[11]) if not pd.isnull(row[11]) else 0
        pbdate = datetime.date(row[17], row[18],1)
        pedate = datetime.date(row[20], row[21], monthrange(row[20], row[21])[1])
        if not (name, pbdate, pedate, product) in orders:
            cur.execute(f'insert into sb_product_order("customer_id", "product_id", "company_id", "ordertype_id",   \
                "validfrom", "validto", "total_price", "paymethod", "orderDate", "product_base") values("{customer}", \
                    "{product}", "1", "1",  "{pbdate}", "{pedate}", "{fee}","{paymethod}", "{datetime.date.today()}",\
                        "{product_base}")')
            orders[(name, pbdate, pedate, product)] = True

    ##TODO:::INSERT GS status

    if not pd.isnull(row[15]):
        ret = cur.execute(f'select id from sb_product where name = "残保金"')
        product = ret.fetchone()[0]
        #product_base=0
        fee = float(row[15])
        if not (name, pbdate, edate, product) in orders:
            cur.execute(f'insert into sb_product_order("customer_id", "product_id", "company_id","ordertype_id",  \
                 "validfrom", "validto", "total_price", "paymethod", "orderDate", "product_base") values("{customer}", \
                     "{product}", "1","1",  "{pbdate}", "{pedate}", "{fee}","{paymethod}", "{datetime.date.today()}", \
                         "{product_base}")')
            orders[(name, pbdate, pedate, product)] = True

    if not pd.isnull(row[12]):
        ret = cur.execute(f'select id from sb_product where name = "公积金"')
        product = ret.fetchone()[0]
        product_base = float(row[12])
        fee = float(row[13]) if not pd.isnull(row[13]) else 0
        if not (name, bdate, edate, product) in orders:
            cur.execute(f'insert into sb_product_order("customer_id", "product_id","company_id", "ordertype_id", \
                  "validfrom", "validto", "total_price", "paymethod", "orderDate", "product_base") \
                      values("{customer}", "{product}", "1", "1", "{pbdate}", "{pedate}", "{fee}","{paymethod}", \
                          "{datetime.date.today()}", "{product_base}")')
            orders[(name, pbdate, pedate, product)] = True

    
# cur.execute(f'delete from sb_customer')
# cur.execute(f'delete from sb_service_order')
# cur.execute(f'delete from sb_product_order')
# cur.execute(f'delete from sb_operations')
db.commit()
cur.close()
db.close()

