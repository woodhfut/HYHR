import mySQLdb

db = mySQLdb.connect(host='10.57.51.87', user='hyhradmin', passwd='Mohan@123', db='hyhrdb')

cur = db.cursor()

#clear auth_user table
cur.execute('delete from auth_user where username <> "sa"')

#sb_district
cur.execute('delete from sb_district')
cur.execute('insert into sb_district("name") values ("北京丰台")')
cur.execute('insert into sb_district("name") values ("北京海淀")')
cur.execute('insert into sb_district("name") values ("北京朝阳")')
cur.execute('insert into sb_district("name") values ("北京东城")')
cur.execute('insert into sb_district("name") values ("北京西城")')
cur.execute('insert into sb_district("name") values ("北京大兴")')
cur.execute('insert into sb_district("name") values ("北京石景山")')
cur.execute('insert into sb_district("name") values ("北京门头沟")')
cur.execute('insert into sb_district("name") values ("北京昌平")')
cur.execute('insert into sb_district("name") values ("北京顺义")')
cur.execute('insert into sb_district("name") values ("北京怀柔")')
cur.execute('insert into sb_district("name") values ("北京延庆")')
cur.execute('insert into sb_district("name") values ("北京通州")')
cur.execute('insert into sb_district("name") values ("北京平谷")')

#sb_payment
cur.execute('delete from sb_paymethod')
cur.execute('insert into sb_paymethod("name") values("微信")')
cur.execute('insert into sb_paymethod("name") values("支付宝")')
cur.execute('insert into sb_paymethod("name") values("银行卡")')
cur.execute('insert into sb_paymethod("name") values("淘宝")')

#sb_ordertype
cur.execute('delete from sb_ordertype')
cur.execute('insert into sb_ordertype("name") values("正常缴费")')
cur.execute('insert into sb_ordertype("name") values("年内补缴")')
cur.execute('insert into sb_ordertype("name") values("跨年补缴")')
cur.execute('insert into sb_ordertype("name") values("最近三个月补缴")')

db.commit()
cur.close()
db.close()