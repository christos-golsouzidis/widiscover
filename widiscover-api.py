from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
import dotenv
# from config import Config


app = Flask(__name__)



CONFIG_FILE = '.env'
dotenv.load_dotenv('./')


def config_exists():
    try:
        with open('.env') as f:
            pass
        return True
    except:
        return False


@app.route('/')
def index():

    if not config_exists():
        return redirect(url_for('config'))
    return redirect(url_for('app'))


@app.route('/config', methods=['GET'])
def config():
    file = 'config.json'
    if not os.path.isfile(file):
        with open(file,'a+') as f:
            f.write(input('paste the API key here:'))
    else:
        with open(file) as fr:
            secret = fr.read()

    file = 'config.json'
    if not os.path.isfile(file):
        with open(file,'w') as f:
            # 
            json.dump(config_data, f)
    else:
        with open(file) as fr:
            config_data = json.load(fr)


    return 'config'







if __name__ == '__main__':
    app.run(host='0.0.0.0', port='7454', debug=True)