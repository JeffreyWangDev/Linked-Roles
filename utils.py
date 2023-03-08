import requests
from dotenv import load_dotenv
import utils
import os
import mysql.connector
load_dotenv()
conn  = mysql.connector.connect(
  host=os.getenv("DB_HOST"),
  user=os.getenv("DB_USERNAME"),
  password=os.getenv("DB_PASSWORD"),
  database = os.getenv("DB_NAME"),
  port = 32813
)
cur = conn.cursor()
# cur.execute("DROP TABLE IF EXISTS linked_users")
# conn.commit()

cur.execute("""CREATE TABLE IF NOT EXISTS linked_users (
                    user_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                    ign TEXT NOT NULL,
                    profile TEXT NOT NULL,
                    discord_id BIGINT NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    expires_in BIGINT,
                    ip TEXT NOT NULL
                    )""")
conn.commit()
cur.close()

def try_it(member,collat):
    try:
        return int(member["collection"][collat])
    except:
        return 1

def calculate_farming_weight(ign,profile = ""):
    response = requests.get(f"{os.getenv('API_ENDPOINT')}/api/skyblock/profile/{ign}/{profile}")
    player = requests.get(f"{os.getenv('API_ENDPOINT')}/api/players/{ign}").json()
    if not response.ok:
        return [0,response.json()["error"]]
    json = response.json()
    try:
        error = json["error"]
        return [2,error]
    except:
        pass
    try:
        weight = 0
        json = response.json()
        member = None
        for i in json["members"]:
            if json["members"][i]["uuid"] == player["uuid"]:
                member = json["members"][i]
    except:
        pass
    if member:
        try:
            farming_level = int(member["skills"]["farming"]["level"])
        except:
            farming_level = 0
        cactus = try_it(member,"CACTUS")
        carrot = try_it(member,"CARROT_ITEM")
        cocoa = try_it(member,"INK_SACK:3")
        melon = try_it(member,"MELON")
        mushroom = try_it(member,"MUSHROOM_COLLECTION")
        wart = try_it(member,"NETHER_STALK")
        potato = try_it(member,"POTATO")
        pumpkin = try_it(member,"PUMPKIN")
        sugar = try_it(member,"SUGAR_CANE")
        wheat = try_it(member,"WHEAT")
        total= cactus/169389 + carrot/300000 + cocoa/303092 + melon/435466 + wart/250000 + potato/300000 + pumpkin/87095 + sugar/200000 + wheat/100000
        doubleBreakRatio = (cactus/169389 + sugar/200000) / total
        normalRatio = (total - cactus/169389 - sugar/200000) / total
        mushroomWeight = doubleBreakRatio * (mushroom / (2 * 168925.53)) + normalRatio * (mushroom / 168925.53)

        weight +=mushroomWeight
        weight += total
        if farming_level >= 60:
            weight += 250
        elif farming_level >= 50:
            weight += 100
        for i in json["unlocked_minions"]:
            if i in ["CACTUS","CARROT","COCOA","MELON","MUSHROOM","NETHER_WARTS","POTATO","PUMPKIN","SUGAR_CANE","WHEAT"]:
                if json["unlocked_minions"][i] == 12:
                    weight+=5
        try:
            weight += member["jacob2"]["perks"]["double_drops"]*2
        except:
            pass
        gold = 0
        for i in member["jacob2"]["contests"]:
            try:
                if member["jacob2"]["contests"][i]["claimed_medal"] == "gold":
                    gold+=1
            except:
                try:
                    if member["jacob2"]["contests"][i]["claimed_position"]<=member["jacob2"]["contests"][i]["claimed_participants"] * 0.05 + 1:
                        gold+=1
                except:
                    pass
                pass
        if gold >=1000:
            weight += 500
        else:
            weight += gold*0.50
        
        return [1,weight]
    else:
        return [0,"Error: No player found. Please try again later or contact the developer at CosmicCrow#6355."]

def new_user(ign:str,discord_id:int,profile:str,access_token:str,refresh_token:str,expires_in:int,ip:str):
    cur = conn.cursor()
    cur.execute("SELECT * FROM linked_users WHERE discord_id=%s",(discord_id,))
    resp = cur.fetchall()
    if resp:
        cur.execute("UPDATE linked_users SET ign = %s,profile=%s, access_token=%s,refresh_token=%s,expires_in=%s WHERE discord_id = %s",(ign,profile,access_token,refresh_token,int(expires_in),discord_id))
    else:
        cur.execute("INSERT INTO linked_users (ign,discord_id,profile,access_token,refresh_token,expires_in,ip) VALUES (%s,%s,%s,%s,%s,%s,%s)",(ign,int(discord_id),profile,access_token,refresh_token,int(expires_in),str(ip)))
    conn.commit()
    cur.close()


def get_farming_data(user,profile=""):
    response = requests.get(f"{os.getenv('API_ENDPOINT')}/api/skyblock/profile/{user}/{profile}")
    player = requests.get(f"{os.getenv('API_ENDPOINT')}/api/players/{user}").json()
    if response.ok:
        json = response.json()
        try:
            error = json["error"]
            return [2,error]
        except:
            pass
        try:
            json = response.json()
            member = None
            for i in json["members"]:
                if json["members"][i]["uuid"] == player["uuid"]:
                    member = json["members"][i]
            farming_level = int(member["skills"]["farming"]["level"])
            farming_xp = int(member["skills"]["farming"]["xp"])
            gold = 0
            for i in member["jacob2"]["contests"]:
                try:
                    if member["jacob2"]["contests"][i]["claimed_medal"] == "gold":
                        gold+=1
                except:
                    try:
                        if member["jacob2"]["contests"][i]["claimed_position"]<=member["jacob2"]["contests"][i]["claimed_participants"] * 0.05 + 1:
                            gold+=1
                    except:
                        pass
                    pass
            return [1,[farming_level,farming_xp,gold]]
        except:
            return [0,"Error: Unkown Error. Please try again later or contact the developer at CosmicCrow#6355."]
    else:
        return [2,response.json()["error"]]

def get_most_recent_profile(name):
    response = requests.get(f"{os.getenv('API_ENDPOINT')}/api/skyblock/profile/{name}")
    if response.ok:
        return response.json()["cute_name"]
    else:
        return None

def get_ign(discord_id):
    cur = conn.cursor()
    cur.execute("SELECT ign FROM verification WHERE user_id=%s",(int(discord_id),))
    resp = cur.fetchone()
    if resp:
        return resp[0]
    else:
        return None
def get_profile(discord_id):
    cur = conn.cursor()
    cur.execute("SELECT profile FROM verification WHERE user_id=%s",(int(discord_id),))
    resp = cur.fetchone()
    if resp:
        return resp[0]
    else:
        return None

def get_token(discord_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM linked_users WHERE discord_id=%s",(int(discord_id),))
    resp = cur.fetchone()
    if resp:
        return resp
    else:
        return None

