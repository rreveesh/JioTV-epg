import requests
import json
import datetime
import os
prevEpgDayCount = 1
nextEpgDayCount = 2


channelList = []


def getChannels():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    reqUrl = "https://jiotv.data.cdn.jio.com/apis/v1.4/getMobileChannelList/get/?os=android&devicetype=phone"
    response = requests.get(reqUrl,headers=headers)
    apiData = json.loads(response.text)
    return apiData["result"]


def getEpg(channelId, offset, langId):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    try:
        reqUrl = "https://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get?channel_id=" + \
            str(channelId)+"&offset="+str(offset)+"&langId="+str(langId)
        response = requests.get(reqUrl,headers=headers)
        print("OK: " + str(response.ok) + " status: " + str(response.status_code))
        if (response.status_code == 200):
            apiData = json.loads(response.text or "{}")
            return apiData["epg"]
        return []
    except requests.exceptions.Timeout:
        return []
    except requests.exceptions.ConnectionError:
        return []


def writeEpgChannel(id, name, iconId, fp):
    if id is None or name is None:
        return

    name = name.replace("&", "and;")
    name = name.replace("<", "&lt;")
    name = name.replace(">", "&gt;")
    name = name.replace("'", "&apos;")
    name = name.replace('"', "&quot;")
    fp.write("\t<channel id=\""+str(name)+"\">\n")
    fp.write("\t\t<display-name lang=\"eng\">"+str(name)+"</display-name>\n")
    fp.write("\t\t<icon src=\"https://jiotv.catchup.cdn.jio.com/dare_images/images/" +
             str(iconId)+"\"></icon>\n")
    fp.write("\t</channel>\n")


def writeEpgProgram(id,name, epg, fp):
    if name is None or epg is None:
        return
    startTime = datetime.datetime.fromtimestamp(int(epg["startEpoch"]/1000))
    progStart = startTime.strftime("%Y%m%d%H%M%S +0000")

    endTime = datetime.datetime.fromtimestamp(int(epg["endEpoch"]/1000))
    progEnd = endTime.strftime("%Y%m%d%H%M%S +0000")

    name = name.replace("&", "and")        
    title = epg["showname"]
    title = title.replace("&", "and;")
    title = title.replace("<", "&lt;")
    title = title.replace(">", "&gt;")
    title = title.replace("'", "&apos;")
    title = title.replace('"', "&quot;")
    
  

    description = epg["episode_desc"] or epg["description"]
    description = description.replace("&", "and;")
    description = description.replace("<", "&lt;")
    description = description.replace(">", "&gt;")
    description = description.replace("'", "&apos;")
    description = description.replace('"', "&quot;")

    director = epg["director"]
    actors = str(epg["starCast"]).split(", ")
    category = epg["showCategory"]
    episodeNum = epg["episode_num"]

    try:
        fp.write("\t<programme start=\""+str(progStart)+"\" stop=\"" +
                 str(progEnd)+"\" channel=\""+str(name) + "\">\n")
        fp.write("\t\t<title lang=\"eng\">" + title + "</title>\n")
        fp.write("\t\t<desc lang=\"eng\">" + description + "</desc>\n")
        fp.write("\t</programme>\n")
    except UnicodeEncodeError:
        print("it was not a ascii-encoded unicode string")
        fp.close()


def grabEpgAllChannel(day):
    print("\n\nGetting EPG for all channels for day "+str(day)+"\n")
    programFile = open("program"+str(day)+".xml", "a", encoding='utf-8')
    progress = 0
    for channel in channelList:
        print("Getting EPG for Service ID-"+str(channel["channel_id"]) +
              " "+channel["channel_name"]+" day "+str(day))
        epgData = getEpg(channel["channel_id"], day, 6)
        for epg in epgData:
            writeEpgProgram(channel["channel_id"],channel["channel_name"], epg, programFile)
        progress += 1
        #if progress == 5:
        #    break
        print("progress "+str(progress)+"/"+str(len(channelList)))
    programFile.close()


def rotateEpg():
    for day in range((prevEpgDayCount * -1), nextEpgDayCount):
        if (os.path.isfile('./program' + str(day) + '.xml')
            and os.path.isfile('./program' + str(day+1) + '.xml')
                and ((day) != (nextEpgDayCount - 1))):
            preProgFile = open('./program' + str(day) +
                               '.xml', "w", encoding='utf-8')
            nextProgFile = open('./program' + str(day+1) +
                                '.xml', "r", encoding='utf-8')
            preProgFile.write(nextProgFile.read())
            preProgFile.close()
            nextProgFile.close()
    if (os.path.isfile('./program' + str(nextEpgDayCount-1) + '.xml')):
        os.remove('./program' + str(nextEpgDayCount-1) + '.xml')


def mergeEpgData():
    channelsFile = open("channels.xml", "r", encoding='utf-8')
    epgFile = open("epg.xml", "a", encoding='utf-8')
    
    epgFile.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
    epgFile.write("<tv>\n")
    #towrite channel list once
    epgFile.write(channelsFile.read())
        
    for day in range((prevEpgDayCount * -1), nextEpgDayCount):
        if (os.path.isfile('./program' + str(day) + '.xml')):
            programsFile = open('./program' + str(day) +
                                '.xml', "r", encoding='utf-8')
            epgFile.write(programsFile.read())
            programsFile.close()

    epgFile.write("</tv>\n")
    epgFile.close()

    # create single day epg
    epgFile1d = open("epg1d.xml", "a", encoding='utf-8')
    epgFile1d.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
    epgFile1d.write("<tv>\n")
    epgFile1d.write(channelsFile.read())
    channelsFile.close()
    if (os.path.isfile('./program0.xml')):
            programsFile = open('./program0.xml', "r", encoding='utf-8')
            epgFile1d.write(programsFile.read())
            programsFile.close()
    epgFile1d.write("</tv>\n")
    epgFile1d.close()

# Process starts here

channelWrFlag = 0
channelList = getChannels()
progress = 0
if (os.path.isfile('./channels.xml')):
    os.remove("./channels.xml")
if (os.path.isfile('./epg.xml')):
    os.remove("epg.xml")
if (os.path.isfile('./epg1d.xml')):
    os.remove("epg1d.xml")
channelFile = open("channels.xml", "a", encoding='utf-8')
for channel in channelList:
    writeEpgChannel(channel["channel_id"],
                    channel["channel_name"], channel["logoUrl"], channelFile)
channelFile.close()
rotateEpg()
for day in range((prevEpgDayCount*-1), nextEpgDayCount):
    if (not os.path.isfile('./epg' + str(day) + '.xml')):
        grabEpgAllChannel(day)
mergeEpgData()
print("Action complete")
