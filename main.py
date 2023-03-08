from flask import Flask, render_template,redirect, request, url_for, make_response, jsonify
app = Flask(__name__)
import os
from dotenv import load_dotenv
import requests
from  linkedroles import Client, AccessToken
import utils
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from threading import Thread
import time
load_dotenv()


client = Client(os.getenv("TOKEN"), os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"),os.getenv("URL_BASE")+"/receive")
client.update_linked_roles([    
    {
        "type": 2,
        "key": "exp",
        "name": "Farming EXP",
        "description": "User's Farming EXP"
    },
    {
        "type": 2,
        "key": "level",
        "name": "Farming Level",
        "description": "User's Farming Level"
    },
    {
        "type": 2,
        "key": "gold",
        "name": "Gold Medals",
        "description": "User's Gold Medals Won"
            
    }
    # ,{
    #     "type": 2,
    #     "key": "weight",
    #     "name": "Farming Weight",
    #     "description": "User's Farming Weight"
    # }
    ])

# url = "https://discord.com/api/v10/applications/1059288523187949578/guilds/1071825301501382768/commands"
# json = {"name": "update", "type": 1,"description": "Updates your linked roles","options": [],"dm_permission":False}
# headers = {"Authorization": f"Bot {os.getenv('TOKEN')}"}
# time.sleep(5)

# r = requests.post(url, headers=headers, json=json)
# print(r.json())

@app.route('/', methods = ['POST', 'GET'])
def index():
    return make_response(redirect(f"https://discord.com/api/oauth2/authorize?client_id={os.getenv('CLIENT_ID')}&redirect_uri={os.getenv('URL_BASE')}/receive&response_type=code&scope=identify%20role_connections.write"))


@app.route('/api/new', methods = ['GET'])
def do_everthing():
    code = request.args.get('code')
    error = "Error: Unknown Error Occured :(, Please try again later or contact the developer at CosmicCrow#6355" 
 
    try:
        token = client.exchange(code)
        user = token.fetch_user()["user"]   
        profile = utils.get_profile(user["id"])  
    except Exception as e:
        print(e)
        return jsonify({"status":0,"msg":"Invalid discord response token, please try again"})
    ign = utils.get_ign(user["id"])  

    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        ip = request.environ['REMOTE_ADDR']
    else:
        ip = request.environ['HTTP_X_FORWARDED_FOR']
    if ign:
        if profile:
            data = utils.get_farming_data(ign,profile)
            weight = utils.calculate_farming_weight(ign,profile)
            utils.new_user(ign,user["id"],profile,token.accessToken,token.refresh,token.expires,ip)
            if data[0] == 1 and weight[0] == 1:
                #token.update_metadata("Skyblock Farming Stats", f"{ign} ({profile})", level = data[1][0], exp = data[1][1], gold = data[1][2],weight = int(weight[1]))
                token.update_metadata("Skyblock Farming Stats(beta)", f"{ign} ({profile})", level = data[1][0], exp = data[1][1], gold = data[1][2])
                return jsonify({"status":1,"msg":f"Connected to player: {ign} with profile: {profile}. \nTo change your profile, please use use the /link command in discord."})
            else:
                error = data[1]
        error = "No profile found with the name: " + ign
    error = f"No ign found for {user['username']}, please link your account with /link <ign> in the discord server" 
    try:
        utils.delete_user(int(user["id"]))
    except:
        pass
    return jsonify({"status":0,"msg":error})

@app.route('/receive', methods = ['GET'])
def receive():
    return make_response(render_template("index.html",url = os.getenv("URL_BASE")))

@app.route('/api/update', methods = ['POST'])
def update():
    id = request.args.get('id')
    key1 = request.args.get('key1')
    key2 = request.args.get('key2')
    key3 = request.args.get('key3')
    if key1 != "YHhGf6niyg4miqO20bvb0nedlgFSjjDW" and key2!="GFNYr8Mvh4ARYWAOpwBU5VgcjGlE2785"and key3!="F4bornqOxsJp20oSztUXfulHVBcKzB2S":   
        return jsonify({"status":0,"msg":"Invalid key"})
    token = utils.get_token(id)
    if token:
        try:
            ign = utils.get_ign(id)
            profile = utils.get_profile(id)
        except:
            return jsonify({"status":0,"msg":"IGN or profile not found"})
        if not ign:
            try:
                utils.delete_user(id)
            except:
                pass
            return jsonify({"status":0,"msg":"IGN not found, please link your account with /link <ign> in the discord server"})
        try:
            tk = AccessToken(client,token[4],token[5],int(token[6]))
        except:
            return jsonify({"status":0,"msg":"Invalid discord token, please remove this as a authorized app in your discord settings and try again!"})
        data = utils.get_farming_data(ign,profile)
        weight = utils.calculate_farming_weight(ign,profile)
        #tk.update_metadata("Skyblock Farming Stats", f"{ign} ({profile})", level = data[1][0], exp = data[1][1], gold = data[1][2],weight = int(weight[1]))
        try:
            tk.update_metadata("Skyblock Farming Stats(beta)", f"{ign} ({profile})", level = data[1][0], exp = data[1][1], gold = data[1][2])
        except:
            return jsonify({"status":0,"msg":"Invalid discord token, please remove this as a authorized app in your discord settings and try again!"})
        return jsonify({"status":1,"msg":f"Connected to player: {ign} with profile: {profile}."})

if __name__ == '__main__':
    app.run(debug=True,port=80)
