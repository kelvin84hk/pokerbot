#!/usr/bin/env python

from threading import Thread
from bottle    import get, post, run, request, response
from time      import sleep
from dotenv    import load_dotenv
from sys       import exit
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate

import requests
import os

load_dotenv()

port          = 3000
username      = 'kelvin84hk'#os.getenv('USERNAME')
api_token     = os.getenv('API_TOKEN')
bot_endpoint  = os.getenv('BOT_ENDPOINT')
notifications = False

def card_convert(tableCards):
    community_card=[]
    for t in tableCards:
        if t['suit']=='spades':
            conv_str ='S'
        if t['suit']=='hearts':
            conv_str ='H'
        if t['suit']=='clubs':
            conv_str ='C'
        if t['suit']=='diamonds':
            conv_str ='D'
        if t['rank']=='ace':
            conv_str = conv_str +'A'
        if t['rank']=='deuce':
            conv_str = conv_str +'2'
        if t['rank']=='three':
            conv_str = conv_str +'3'
        if t['rank']=='four':
            conv_str = conv_str +'4'
        if t['rank']=='five':
            conv_str = conv_str +'5'
        if t['rank']=='six':
            conv_str = conv_str +'6'
        if t['rank']=='seven':
            conv_str = conv_str +'7'
        if t['rank']=='eight':
            conv_str = conv_str +'8'
        if t['rank']=='nine':
            conv_str = conv_str +'9'
        if t['rank']=='ten':
            conv_str = conv_str +'T'
        if t['rank']=='jack':
            conv_str = conv_str +'J'
        if t['rank']=='queen':
            conv_str = conv_str +'Q'
        if t['rank']=='king':
            conv_str = conv_str +'K'
        community_card.append(conv_str)
    return community_card
        

@post('/pokerwars.io/play')
def play():
    # This endpoint is called by pokerwars.io to request your bot next move on a tournament.
    # You have the current state of the table in the game_info object, which you can use to decide
    # your next move.
    game_info = request.json
    #print(game_info["tableCards"])
    #print(card_convert(game_info["tableCards"]))
    community_card=gen_cards(card_convert(game_info["tableCards"]))
    #print(game_info["yourCards"])
    #print(card_convert(game_info["yourCards"]))
    my_hole_card =gen_cards(card_convert(game_info["yourCards"]))
    player_active=0
    players = game_info["players"]
    pot=0
    for p in players:
        pot = pot + p['pot']
        if p['hasFolded']== False:
            player_active = player_active +1
        if p['username']==username:
            bet_max = p['chips']-p['pot']
    win_prob = estimate_hole_card_win_rate(nb_simulation=250, nb_player=player_active, hole_card=my_hole_card, community_card=community_card)
    response.content_type = 'application/json'
    if win_prob>0.25:
        if win_prob>0.75:
            #print(bet_max)
            #print(game_info["minRaise"])
            #print(int(pot*win_prob))
            bet = min(bet_max,max(int(game_info["smallBlindValue"]),int(pot*win_prob)))
            if  bet>=int(game_info["smallBlindValue"]) :
                
                if game_info["canCheckOrBet"]:
                    act= {"action": "bet","chips":bet}
                else:
                    act= {"action": "raise","chips":bet}
               
            else:
                act= {"action": "check"}
            
        else:
            if game_info["canCheckOrBet"]:
                act= {"action": "check"}
            else:
                act= {"action": "call"}
    else:
        if game_info["canCheckOrBet"]:
            act= {"action": "check"}
        else:
            act= {"action": "fold"}
    print(act)        
    return act        


@get('/pokerwars.io/ping')
def ping():
    # This is used by pokerwars.io when your bot subscribe to verify that is alive and responding
    print('Received ping from pokerwars.io, responding with a pong')
    response.content_type = 'application/json'
    return {"pong": True}

@post('/pokerwars.io/notifications')
def notifications():
    print('Received notification')
    print(request.json)
    response.content_type = 'application/json'
    return

def subscribe():
    down = True
    print(username)
    print(api_token)
    print(bot_endpoint)
    while down:
        try:
            print('Trying to subscribe to pokerwars.io ...')
            r = requests.get(bot_endpoint + '/pokerwars.io/ping')

            if r.status_code == 200:
                down = False
                r = requests.post('https://play.pokerwars.io/v1/pokerwars/subscribe', json={'username': username, 'token': api_token, 'botEndpoint': bot_endpoint, 'notifications': bool(notifications)})

                print('Subscription --> Status code: ' + str(r.status_code))
                print('Subscription --> Body: ' + str(r.json()))

                if r.status_code != 202:
                    print('Failed to subscribe, aborting ...')
                    exit()
        except requests.ConnectionError:
            print('connection error')
            exit()
        except requests.Timeout:
            print('timeout error')
            exit()
        except:
            print('error')
            exit()

        sleep(2)

if __name__ == '__main__':
    s = Thread(target=subscribe)
    s.daemon = True
    s.start()

    run(port=port)
