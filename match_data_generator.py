import requests
import json
import sys
import time
import csv
import pandas as pd
from pandas.io.json import json_normalize


# First request made to riot that all of the other calls stem from 
URL = 'https://na1.api.riotgames.com/lol/match/v4/matches/' + str(sys.argv[3]) (#input gameId here)
params = {'api_key':sys.argv[1]}
r = requests.get(url = URL, params = params)

with open('league.csv', 'wb') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',')

# Function to list the account IDs for the given match
def get_players(match_request):
    player_ids = []
    for player_id in match_request.json()["participantIdentities"]:
        print(player_id["player"]["accountId"])
        player_ids.append(player_id["player"]["accountId"])
    return player_ids

# Calling get_players function to get the list of account IDs associated with the first request
player_ids = get_players(r)

# Function to get the list of gameIds for the given player Ids
def get_1000_matches(player_list):
    gameIds = []
    i=1
    for player in player_list:
        URL = 'https://na1.api.riotgames.com/lol/match/v4/matchlists/by-account/'+ player
        r = requests.get(url = URL, params = params)
        r1 = json.loads(json.dumps(r.json()))
		#The below block proceeds only if the account IDs have some data against them
        if list(r1.keys())[0] == 'matches':
            r2 = json_normalize(r1,max_level=1,record_path ='matches')
            r3 = r2[r2['queue'].isin([400,420,440])]  (#Only relevant queue Ids considered here)
            for match in r3["gameId"]:
                gameIds.append(match)
        print(len(gameIds))
		#For every 100 requests, the code below introduces a wait time of 2 minutes
        if i%100 ==0:
            time.sleep(125)
        i+= 1
    return gameIds
print("All match Ids for every player in first match 3187138923")

#Calling the function to get the games corresponding to the 10 account IDs
games = get_1000_matches(player_ids)
        
# Needed columns: Allies, Counters, Runes, Spells, Win Rate, Pick Rate, Perk
# Allies = 3 champions that won the most games with this champion
# Counters=3 champions that won the most games against this champion
# Runes = Top 2 most utilized runes with this champion
# Spells= Given
# Win Rate = Wins/Total y games for champion
# Pick Rate = Picks + games / All games
# Perks = Top Perks for champion 
# Difficulty = Given
#print(json.dumps(r.json(), indent=4))


# Function to populate the match stats and team info for the given gameIds
def populate(request):
    json_request = json.loads(json.dumps(request.json()))
    game_info = json_normalize(json_request)
    game_info.drop(['teams','participants','participantIdentities'],axis=1,inplace=True)
    game_info = game_info.loc[game_info['gameMode'] == 'CLASSIC']
    teams = json_normalize(json_request,record_path=['teams'],meta=['gameId'])
    teams_bans = json_normalize(json_request['teams'],record_path=['bans'],meta=['teamId'])
    r_teams_bans_f = pd.merge(teams,teams_bans,how='inner').drop('bans', axis=1)
    

    r_prtcpts = json_normalize(json_request,record_path=['participants'],meta=['gameId'],max_level=0)
    stats = json_normalize(r_prtcpts['stats'])
    timeline = json_normalize(r_prtcpts['timeline'])
    r_prtcpts = r_prtcpts.drop(columns=['stats', 'timeline'])
    r_prtcpts = pd.merge(timeline, r_prtcpts, on='participantId')
    r_prtcpts = pd.merge(stats, r_prtcpts,    on='participantId')
    
    r_prtcpts_id = json_normalize(json_request,record_path=['participantIdentities'],meta=['gameId'],max_level=0) (#Caution: max_level works only in pandas v0.25.1 and above)
    player = json_normalize(r_prtcpts_id['player'])
    r_prtcpts_id = r_prtcpts_id.drop(columns=['player'])
    r_prtcpts = pd.concat([r_prtcpts, player], axis=1)
    
    match_final = pd.merge(pd.merge(pd.merge(game_info,r_teams_bans_f,on='gameId',how='inner'),r_prtcpts,
                                left_on=['gameId','teamId','pickTurn'],right_on=['gameId','teamId','participantId'],how='inner'),
                       r_prtcpts_id,on=['gameId','participantId'],how='inner')
    match_final = match_final.drop(columns=['participantId',
'longestTimeSpentLiving',
'doubleKills',
'tripleKills',
'quadraKills',
'pentaKills',
'unrealKills',
'perk0Var1',
'perk0Var2',
'perk0Var3',
'perk1Var1',
'perk1Var2',
'perk1Var3',
'perk2Var1',
'perk2Var2',
'perk2Var3',
'perk3Var1',
'perk3Var2',
'perk3Var3',
'perk4Var1',
'perk4Var2',
'perk4Var3',
'perk5Var1',
'perk5Var2',
'perk5Var3',
'participantId',
'currentPlatformId',
'currentAccountId',
'profileIcon', 'seasonId', 'mapId'])
    return match_final



# Note that one match ID can give us up to 1000 different matches
data = pd.DataFrame()
i = 1
for game in games:
    
    gameURL = 'https://na1.api.riotgames.com/lol/match/v4/matches/' + str(game)
    new_request = requests.get(url = gameURL, params = params)
    print("This is the output for match number "+str(game))
    match_data = populate(new_request)
    data = pd.concat([match_data, data], axis=0, sort=False) (#retains the column orders upon the concat)
    if i%100 == 0:
        time.sleep(125)
    i+= 1

print("You collected: " + str(len(games)) + " games and " + str(data.shape[0]) + " data points!")
#You collected: 758 games and 7580 data points!

#Fetching the list of account IDs for the games obtained in the previous step
player_Ids2 = data.accountId.unique()
print("The number of associated account Ids is",len(player_Ids2))
# The number of associated account Ids is 5979

# Calling get_1000_matches function to get the list of gameIds for the list of accounts obtained from the above step
games_r2 = get_1000_matches(player_Ids2)

print("The number of associated Game Ids corresponding to the " + str(len(player_Ids2)) + " account Ids is: " + str(len(games_r2)))
# The number of associated Game Ids corresponding to the 5979 account Ids is: 458988








