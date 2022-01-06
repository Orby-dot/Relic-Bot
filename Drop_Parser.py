##WARFRAME DROP PARSER##
# Purpose: Take the info from https://n8k6e2y6.ssl.hwcdn.net/repos/hnfvc0o3jnfvc873njb03enrf56.html and extract 2 files. 
# One with where relics drop and another with what relics have
# Currently does not have bounties

import requests 
import json
from bs4 import BeautifulSoup
import yaml


#Constants (can add/remove without breaking the code too much)
RARITY_CONST = ["Very Common","Common","Uncommon","Ultra Rare","Rare","Legendary"]
ROTATION_CONST = ["Rotation A","Rotation B","Rotation C"]
BLACKLIST_CONST= ["Hot Mess", "Event","Sunkiller","Table For Two","Another Betrayer","Time's Up","The Aftermath","Family Reunion","Recover The Orokin Archive"]

#Finds number in a string (also includes the '.')
def findInt(strInit):
    strNum = ""
    for i in strInit:
        if (ord(i) > 47 and ord(i) < 58) or ord(i) == 46:
            strNum += i

    return strNum

#Removes the weird indent from the html
def removeIndent(strInit):
    strNoIndent = ""
    for i in range (len(strInit)):
        if ord(strInit[i]) != 10:
            strNoIndent= strNoIndent + strInit[i]

    return strNoIndent

#Removes the beginning fluff and all the html code. Leaving only the list of items
def initParse(rawHtml):
    
    soup = BeautifulSoup(rawHtml,'html.parser')

    #If the first paragraph goes thru a drastic change this will break and i will have to fix it
    rawText = soup.get_text().split(")")
    rawText.pop(0)
    rawText.pop(0)
    rawText.pop(0)

    while("Missions" not in rawText[0]):
        rawText.pop(0)

    #This is really messy and i am sorry but a quick TL;DR is just i want the data after "Missions:" in the raw text for the next stages
    temp = rawText[0].split("Missions:")
    rawText.pop(0)
    temp.pop(0)
    temp = temp + rawText
    rawText = temp

    return rawText

#Turns a string like: "RotationAAxi B6" into 2 seperate entries of "Rotation A" and "Axi B6"
def splitRotation(strInit):
    strSplit =[]

    for i in range(len(ROTATION_CONST)):
        if ROTATION_CONST[i] in strInit: #If any of the key phrases from ROTATION_CONST is found it splits the str
            strSplit= strInit.split(ROTATION_CONST[i])
            if len(strSplit[0]) < 1:
                strSplit[0] = ROTATION_CONST[i]
            else: #Sometimes we will have a str like "SendaRotationAAxi B6" so we need to split it into 3 elements (Yeah the html is that gross)
                holder = strSplit[1]
                strSplit[1] = ROTATION_CONST[i] 
                strSplit.append(holder)
            break
    
    return strSplit

#Turns a string like: "Axi B6Rare 12%" into 2 seperate entries of "Axi B6" and "12"
def splitRarity(strInit):
    strSplit =[]
    for i in range(len(RARITY_CONST)):
        if RARITY_CONST[i] in strInit:
            strSplit= strInit.split(RARITY_CONST[i])
            strSplit[1] = findInt(strSplit[1])
            break
    
    return strSplit

#Splits the text file into 2 files: Relics and what they drop and everything else
def splitRelic(arrTxt, arrRelic, arrOther):
    i = 0
    while "Relics:" not in arrTxt[i]:
        arrOther.append(arrTxt[i])
        i += 1
    while "Keys:" not in arrTxt[i]:
        arrRelic.append(arrTxt[i])
        i += 1
    while "Relic Drops by Source:" not in arrTxt[i]: #I am not looking at the stuff past "Relic Drop by Source" cuz that is pain
        arrOther.append(arrTxt[i])
        i += 1

#Turns the txt file of relic data into a dictionary structure 
def relicToDic(arrRelic):
    dictRelic = {}
    step = -1 #used this to keep track what part of the pattern i am on
    currentRelic = ""
    currentItem = ""
    for i in arrRelic:

        if  i is not None:
            if step != -1 and "Relic" in i:
                step = 1
            
                    
            if step == -1:
                tempStr = i.replace("Relics:", "")
                tempStr += ")"
                dictRelic[tempStr] = {}
                currentRelic = tempStr
                step = 2

            elif step ==1:
                tempStr = i
                tempStr += ")"
                dictRelic[tempStr] = {}
                currentRelic = tempStr
                step = 2

            elif step ==2:
                dictRelic[currentRelic][i] = 0
                currentItem = i
                step = 3

            elif step ==3:
                dictRelic[currentRelic][currentItem] = float(i)
                step = 2


    dictRelic = relicFlip(dictRelic) #Flips the order of the dictionary from [Relic] -> [Part] -> [Chance] to [Part] -> [Relic] -> [Chance]
    return dictRelic


#Turns the txt file of the drop data into a dictionary structure 
def dropToDic(arrDropTable):

    missionName = ""
    rotation = ""
    dictDropTable = {}
    blacklistMission = 0

    for i in range(len(arrDropTable)):
        if ROTATION_CONST[0] is arrDropTable[i]:
                
                missionName = arrDropTable[i-1] + ")"
                missionName = removeIndent(missionName)

                blacklistMission = 0
                for i in BLACKLIST_CONST:
                    if i in missionName:
                        blacklistMission = 1

                rotation = ROTATION_CONST[0]

        elif ROTATION_CONST[1] is arrDropTable[i]:
            rotation = ROTATION_CONST[1]


        elif ROTATION_CONST[2] is arrDropTable[i]:
            rotation = ROTATION_CONST[2]


        elif "Relic" in arrDropTable[i] and "Clem" not in arrDropTable[i] and blacklistMission ==0: #I have to add a clem check here cuz of a mission...I have once again been beaten by Clem
            if dictDropTable.get(missionName) == None:
                dictDropTable[missionName]= {}

            if dictDropTable[missionName].get(rotation) == None:
                dictDropTable[missionName][rotation]= {}
            try:
                dictDropTable[missionName][rotation][arrDropTable[i]] = (float(arrDropTable[i+1]))
                i += 1

            except (ValueError):
                dictDropTable[missionName][rotation][arrDropTable[i]] = (float(arrDropTable[i+2]))
                i += 2


    dictDropTable = otherFlip(dictDropTable)#Flips the order of the dictionary from [Location] -> [Rotation] -> [Relic] -> [Chance] to [Relic] -> [Location] -> [Rotation] -> [Chance]
    return dictDropTable


#Flips the order of the dictionary from [Relic] -> [Part] -> [Chance] to [Part] -> [Relic] -> [Chance]
def relicFlip(dictInit):
    dictFlipped = {}
    for i in dictInit:
        for j in dictInit[i]:
            if dictFlipped.get(j) == None:
                dictFlipped[j] = {}
            dictFlipped[j][i]= dictInit[i][j]

    return dictFlipped

#Flips the order of the dictionary from [Location] -> [Rotation] -> [Relic] -> [Chance] to [Relic] -> [Location] -> [Rotation] -> [Chance]
def otherFlip(dictInit):
    dictFlipped = {}
    for i in dictInit:
        for j in dictInit[i]:
            for k in dictInit[i][j]:
                if dictFlipped.get(k) == None:
                    dictFlipped[k] = {}
                if dictFlipped[k].get(i) == None:
                    dictFlipped[k][i] = {}
                dictFlipped[k][i][j]= dictInit[i][j][k]


    return dictFlipped





def main():
    req = requests.get("https://n8k6e2y6.ssl.hwcdn.net/repos/hnfvc0o3jnfvc873njb03enrf56.html")
    data = req.text

    rawTxt = initParse(data)

    arrParsed = []
    for i in range(len(rawTxt)):
        arrParsed.append(removeIndent(rawTxt[i]))

        temp = splitRotation(rawTxt[i])
        if temp:
            arrParsed.pop()
            arrParsed += temp



    tempParsed = arrParsed
    arrParsed = []

    for i in range(len(tempParsed)):
        arrParsed.append(tempParsed[i])
        temp = splitRarity(tempParsed[i])
        if temp:
                arrParsed.pop()
                arrParsed += temp



    fileRelic = []
    fileDropTable = []

    splitRelic(arrParsed,fileRelic,fileDropTable)

    fileRelic = relicToDic(fileRelic)
    fileDropTable = dropToDic(fileDropTable)

    with open('raw_txt.txt','w') as outfile:
        for i in arrParsed:
            outfile.write(i + "\n")

    with open('relic_human_readable.yaml','w') as outfile:

        yaml.dump(fileRelic, stream=outfile, default_flow_style=False ,indent = 4)

    with open('relic.json','w') as outfile:

        json.dump(fileRelic,outfile)


    with open('drop_table_human_readable.yaml','w') as outfile:

        yaml.dump(fileDropTable, stream=outfile, default_flow_style=False ,indent = 4) 

    with open('drop_table.json','w') as outfile:
        json.dump(fileDropTable,outfile)


    with open('raw_html.txt','w') as outfile:
        outfile.write(data)


main()