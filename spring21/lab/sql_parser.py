import os
from tqdm import tqdm
import re
from datetime import datetime

def astype(v, t):
    if not v:
        return None

    if (t == 'int'):
        return int(v)
    elif(t == 'double'):
        return float(v)
    elif(t == 'string'):
        return v
    elif(t == 'bool'):
        return bool(v)
    elif(t == 'date'):
        return datetime.fromisoformat(v)

def read_columns(file):
    fields, types = [], []
    while(True):
        line = file.readline()

        if not line:
            break
        
        m = re.match(r'^\s+\`(\w+)\`\s([a-zA-Z]+)', line)
        
        if not m:
            break
            
        fields.append(m.group(1))
        column_type = m.group(2).upper()
        
        field_type = 'string'
        if ('INT' in column_type):
            field_type = 'int'
        elif (column_type == 'BOOL'):
            field_type = 'bool'
        elif (column_type == 'FLOAT'):
            field_type = 'double'
        elif (column_type == 'TIMESTAMP'):
            field_type = 'date'
        
        types.append(field_type)
        
    return fields, types, file
    
def read_insert(s):
    rows = []
    i = 0
    while (i < len(s)):
        row = []
        while s[i] != ')':
            i+=1
            new_s = ''
            if s[i] == '\'':
                escaped = False

                while True:
                    i += 1
                    if (escaped):
                        escaped = False
                    elif(s[i]=='\\'):
                        escaped = True
                    elif(s[i]=='\''):
                        break
                    new_s += s[i]
                i+=1
            else:
                while s[i] != ',' and s[i] != ')':
                    new_s += s[i]
                    i+=1
                if new_s == 'NULL':
                    new_s = None
                    
            row.append(new_s)
        rows.append(row)
        i+=2
    return rows

def batch_read_inserts(file, pbar, n=1):
    rows = []
    while(line := file.readline()):
        m = re.search(r'VALUES (.*)$', line)

        if m:
            s = m.group(1)
            rows.extend(read_insert(s))
            if (len(rows) >= n):
                yield rows
                rows.clear()
            pbar.update(1)
            
    if len(rows):
        yield rows

def parse_dump(path, db, toMigrate = None, keys = []):
    for filename in os.listdir(path):
        m = re.match(r'(.*?)\.sql$', filename)

        if m:
            prefix = m.group(1)
            col = db[prefix]

            if toMigrate and prefix not in toMigrate:
                continue

            filepath = f'{path}{prefix}.sql'

            with open(filepath, encoding='utf-8', errors='ignore') as file:
                while('CREATE TABLE' not in file.readline()):
                    pass

                fields, types, file = read_columns(file)

                cnt = 0
                while(line := file.readline()):
                    cnt += 'VALUES' in line


            if (prefix in keys):
                col.create_index(
                    keys[prefix],
                    unique=True
                )
            elif 'id' in fields[0]:
                fields[0] = '_id'
            N = len(fields)

            def to_doc(row):
                return {fields[i] : astype(row[i], types[i]) for i in range(N)}

            with open(filepath, encoding='utf-8', errors='ignore') as file, tqdm(total=cnt) as pbar:
                pbar.set_description(prefix)
                for rows in batch_read_inserts(file, pbar, 1000000):
                    docs = list(map(to_doc, rows))
                    try:
                        col.insert_many(docs, ordered=False)
                    except:
                        pass