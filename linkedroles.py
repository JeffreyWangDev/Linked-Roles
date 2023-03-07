import requests
from datetime import datetime
import time

class AccessToken():
    def __init__(self, client, token:str, refresh:str, expires:int): 
        self.client : Client = client
        self.accessToken = token
        self.refresh = refresh
        self.expires = expires
    def cheek_token(self):
        if self.accessToken == None:
            self.refresh_token()
        if self.expires < time.time():
            self.refresh_token()

    def refresh_token(self):
        """
        Refreshes the access token
        """
        data = {
            'client_id': self.client.id,
            'client_secret': self.client.secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        resp = requests.post("https://discord.com/api/oauth2/token",data=data,headers=headers)
        print(resp.json())
        if resp.ok:
            json = resp.json()
            self.accessToken = json["access_token"]
            self.refresh = json["refresh_token"]
            self.expires = time.time()+int(json["expires_in"])
            return self
        elif resp.status_code == 429:
            raise Exception.RateLimited("Rate limited")
        elif resp.status_code == 400:
            raise Exceptions.HTTPException("Code, client_id, or client_secret is invalid.")
        elif resp.status_code == 401:
            raise Exceptions.HTTPException("Client secret is invalid.")
        elif resp.status_code == 403:
            raise Exceptions.HTTPException("Client is not authorized to use the grant type.")
        else:
            raise Exception.HTTPException("Unknown error")

    def fetch_metadata(self):
        """
        Fetches the [metadata](https://discord.com/developers/docs/resources/user#application-role-connection-object) for this application. Requires the `role_connections.write` scope
        """
        self.cheek_token()
        response = requests.get(f"https://discord.com/api/v10/users/@me/applications/{self.client.id}/role-connection", headers={"authorization": f"Bearer {self.accessToken}"})
        if response.ok:
            return response.json()
        elif response.status_code == 429:
            raise Exception.RateLimited("Rate limited")
        elif response.status_code == 403:
            raise Exception.Forbidden("Forbidden")
        return(response.json())
    def update_metadata(self, title, subtitle, **metadata):
        """
        Updates the user's metadata for this application. Requires the `role_connections.write` scope

        title: Displayed at the top of the user's profile in gray text
        subtitle: Displayed right under the title in white text
        metadata: list key pairs for metadata, Allows `bool`, `int`, `datetime`, and `str` (only iso timestamps) values
        """
        self.cheek_token()
        response = requests.put(f"https://discord.com/api/v10/users/@me/applications/{self.client.id}/role-connection", headers={
        "authorization": f"Bearer {self.accessToken}"}, json={
            "platform_name": title,
            "platform_username": subtitle,
            "metadata": {key: value for key, value in metadata.items()}
        })
        if response.ok:
            return response.json()
        return(response.json())
    def fetch_user(self):
        self.cheek_token()
        responce = requests.get(f"https://discord.com/api/v10/oauth2/@me", headers={"authorization": f"Bearer {self.accessToken}"})
        if responce.ok:
            return responce.json()
        return(responce.json())
class Client:
    def __init__(self, bot_token,id,secret,redirect):
        self.token = bot_token
        self.id = id
        self.secret = secret
        self.redirect = redirect
    def exchange(self, code) -> AccessToken:
        """
        Exchanges a code from a redirect url for an access token
        """
        data = {
        'client_id': self.id,
        'client_secret': self.secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': self.redirect
        }
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }
        resp = requests.post("https://discord.com/api/oauth2/token",data=data,headers=headers)
        if resp.ok:
            json = resp.json()
            token = AccessToken(self,json["access_token"], json["refresh_token"], time.time()+int(json["expires_in"]))
            return token
        elif resp.status_code == 429:
            raise Exception.RateLimited("Rate limited")
        elif resp.status_code == 400: 
            raise Exceptions.HTTPException("Code, client_id, or client_secret is invalid.")
        return(resp.json())
    
    def from_refreshToken(self, refreshtoken,time = 0) -> AccessToken:
        """
        Exchanges a refreshtoken for an access token
        """

        token = AccessToken(self,None, refreshtoken, 1)
        token.cheek_token()
        return token

    def update_linked_roles(self,metadata: list[dict]):
        """
        Updates the linked roles for the bot

        metadata: list of [application role connection metadata](https://discord.com/developers/docs/resources/application-role-connection-metadata#application-role-connection-metadata-object)
        """
        status = requests.put(f"https://discord.com/api/v10/applications/{self.id}/role-connections/metadata", headers={"authorization": f"Bot {self.token}"}, json=metadata)
        if status.ok:
            return status.json()
        elif status.status_code == 429:
            raise Exception.RateLimited("Rate limited")
        elif status.status_code == 403:
            raise Exception.Forbidden("Forbidden")
        return(status.json())

class Exceptions():
    class BaseException(Exception):
        pass

    class HTTPException(BaseException):
        pass

    class RateLimited(HTTPException):
        def __init__(self, text, retry_after):
            self.retry_after = retry_after
            super().__init__(text)
  
    class Forbidden(HTTPException):
        pass


