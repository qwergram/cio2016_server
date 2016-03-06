import bottle
import os
import sqlite3
import json

class CRUD:

    def __init__(self, location='/etc/luna/'):
        self.location = location
        self.reset()

    def reset(self):
        with open(self.location + 'active.sqlite3', 'w') as r:
            r.write('')
        self.conn = sqlite3.connect(self.location + 'active.sqlite3')
        self.c = self.conn.cursor()
        self.c.execute('CREATE TABLE users (first text, last text, status text)')
        self.conn.commit()

    def get(self, key=None):
        self.c.execute('SELECT * FROM users WHERE status=? LIMIT 1', ('',))
        line = self.c.fetchone()
        if line and key:
            self.c.execute('UPDATE users SET status = ? WHERE first = ? AND last = ? AND status = ?', (key, line[0], line[1], ''))
            self.conn.commit()
            return list(line)
        elif line:
            return list(line)
        else:
            return False

    def confirm(self, fname, lname, key):
        self.c.execute('SELECT * FROM users WHERE first = ? AND last = ? AND status = ?', (fname, lname, key))
        line = self.c.fetchone()
        if line:
            self.remove(fname, lname)
            return True
        else:
            return False

    def rturn(self, fname, lname, key):
        self.c.execute('SELECT * FROM users WHERE status=? LIMIT 1', (key,))
        line = self.c.fetchone()
        if line:
            self.c.execute('UPDATE users SET status = ? WHERE first = ? AND last = ? AND status = ?', ('', line[0], line[1], key))
            self.conn.commit()
            return True
        else:
            return False


    def add(self, first, last, status=''):
        self.c.execute('INSERT INTO users VALUES (?,?,?)', (first, last, status))
        self.conn.commit()

    def remove(self, first, last):
        self.c.execute('DELETE FROM users WHERE first = ? AND last = ?', (first, last))
        self.conn.commit()

    def inport(self):
        with open(self.location + 'import.csv') as to_import:
            to_import = to_import.readlines()
        for line in to_import:
            line = line.strip().split(',')
            if line[0] == 'add':
                self.add(line[1], line[2], '')
            elif line[0] == 'remove':
                self.remove(line[1], line[2])

    def export(self):
        self.c.execute('SELECT * FROM users')
        exp = self.c.fetchall()
        for i, line in enumerate(exp):
            exp[i] = ','.join(line)
        with open(self.location + 'export.csv', 'w') as to_export:
            to_export = '\n'.join(exp)

C = CRUD()

def check_environment(location):
    global LOCATION
    LOCATION = location
    print("Checking Server environment...")
    if os.path.exists(location):
        print("Luna has been run before!")
        return True
    else:
        os.makedirs(location)
    print("Building Luna config files...")
    os.system("sudo touch " + location + 'stats.json')
    os.system("sudo touch " + location + 'config.json')
    os.system("sudo touch " + location + 'import.csv')
    os.system("sudo touch " + location + 'export.csv')
    os.system("sudo touch " + location + 'active.sqlite3')

STATS = {
    "key_usage": {},
    "left": [],
    "unconfirmed": [],
    "completed": [],
    "errors": 0,
}


def log_key(key, action):
    if not key in STATS['key_usage']:
        STATS['key_usage'][key] = {
            "get": 0,
            "confirm": 0,
            "return": 0,
            "coffee_breaks": 0,
        }
    STATS['key_usage'][key][action] += 1
    with open(LOCATION + '/stats.json', 'w') as log:
        log.write(json.dumps(STATS, indent=4))


@bottle.get('/<key>/about')
def about(key):
    global ERRORS, STATS
    bottle.response.content_type = 'application/json'
    log_key(key, "coffee_breaks")
    return json.dumps(STATS, indent=2)


@bottle.get('/<key>/get')
def get(key):
    bottle.response.content_type = 'application/json'
    db_response = C.get(key)
    if not db_response:
        log_key(key, "coffee_breaks")
        return json.dumps({"status": "wait", "duration": 10, "msg": "+1 Coffee"}, indent=2)

    elif db_response:
        if not (db_response[0], db_response[1]) in STATS['unconfirmed']:
            STATS['unconfirmed'].append([db_response[0], db_response[1]])
        log_key(key, 'get')
        return json.dumps({"status": "image", "fname": db_response[0], "lname": db_response[1]}, indent=2)

@bottle.get('/<key>/confirm/<fname>/<lname>')
def confirm(key, fname, lname):
    bottle.response.content_type = 'application/json'

    db_response = C.confirm(fname, lname, key)

    if db_response:
        log_key(key, 'confirm')
        log_key(key, 'coffee_breaks')
        log_key(key, 'coffee_breaks')
        return json.dumps({"status": "confirmed", "fname": fname, "lname": lname, "msg": "+2 Coffee"}, indent=2)
    else:
        STATS['errors'] += 1
        return json.dumps({"status": "error", "error": "LN_4"}, indent=2)

@bottle.get("/<key>/return/<fname>/<lname>")
def rturn(key, fname, lname):
    bottle.response.content_type = 'application/json'
    db_response = C.rturn(fname, lname, key)
    if db_response:
        log_key(key, 'return')
        return json.dumps({"status": "returned", "fname": fname, "lname": lname}, indent=2)
    else:
        STATS['errors'] += 1
        return json.dumps({"status": "error", "error": "LN_2"}, indent=2)


def main(location='/etc/luna/'):
    check_environment(location)
    # with open(location + 'config.json') as config:
        # config = json.loads(config.read().strip())
    print("[n] What would you like to do?")
    print("[n] 1. Import a csv")
    print("[n] 2. Export a csv")
    print("[n] 3. Reset active server")
    print("[n] 4. Launch the server")
    while True:
        option = input("[n] Type the order you want: (e.g. 213 exports, imports and then runs the server)")
        okay = True
        for task in option:
            if task in '1234':
                okay = True
            else:
                okay = False
                break
        if okay:
            break
        print("[n] Invalid options. ")

    for task in option:
        if task == '1':
            C.inport()
        elif task == '2':
            C.export()
        elif task == '3':
            C.reset()
        elif task == '4':
            bottle.run(host='0.0.0.0', port=8000, debug=True)


if __name__ == "__main__":
    print("Hello. Activating Luna build RS25B7!")
    main()
