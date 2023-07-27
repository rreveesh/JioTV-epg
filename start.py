import requests
import json
import datetime

prevEpgDayCount = 7
nextEpgDayCount = 2

channelList = []


def getChannels():
    reqUrl = "https://jiotv.data.cdn.jio.com/apis/v1.4/getMobileChannelList/get/?os=android&devicetype=phone"
    response = requests.get(reqUrl)
    apiData = json.loads(response.text)
    return apiData["result"]


def getEpg(channelId, offset, langId):
    reqUrl = "https://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get?channel_id=" + \
        str(channelId)+"&offset="+str(offset)+"&langId="+str(langId)
    response = requests.get(reqUrl)
    print("OK: " + str(response.ok) + " status: " + str(response.status_code))
    if (response.status_code == 200):
        apiData = json.loads(response.text or "{}")
        return apiData["epg"]
    return []


def initEpgFiles():
    f = open("channels.xml", "w")
    f.write("")
    f.close()

    f = open("program.xml", "w")
    f.write("")
    f.close()

    f = open("epg.xml", "w")
    f.write("")
    f.close()


def writeEpgChannel(id, name, iconId, fp):
    if id is None or name is None:
        return

    name = name.replace("&", "&amp;")
    # f = open("channels.xml", "a", encoding='utf-8')
    fp.write("\t<channel id=\""+str(id)+"\">\n")
    fp.write("\t\t<display-name>"+str(name)+"</display-name>\n")
    fp.write("\t\t<icon src=\"https://jiotv.catchup.cdn.jio.com/dare_images/images/" +
             str(iconId)+"\"></icon>\n")
    fp.write("\t</channel>\n")
    # f.close()


def writeEpgProgram(channelId, start, end, title, description, icon, fp):
    if channelId is None or start is None or end is None or title is None:
        return
    startTime = datetime.datetime.fromtimestamp(int(start/1000))
    progStart = startTime.strftime("%Y%m%d%H%M%S +0000")

    endTime = datetime.datetime.fromtimestamp(int(end/1000))
    progEnd = endTime.strftime("%Y%m%d%H%M%S +0000")

    title = title.replace("&", "&amp;")
    description = description.replace("&", "&amp;")

    try:
        # f = open("program.xml", "a", encoding='utf-8')
        fp.write("\t<programme start=\""+str(progStart)+"\" stop=\"" +
                 str(progEnd)+"\" channel=\""+str(channelId) + "\">\n")
        fp.write("\t\t<title lang=\"en\">" + title + "</title>\n")
        fp.write("\t\t<desc lang=\"en\">" + description + "</desc>\n")
        fp.write("\t\t<icon src=\"https://jiotv.catchup.cdn.jio.com/dare_images/shows/" +
                 str(icon)+"\"></icon>\n")
        fp.write("\t</programme>\n")
        # f.close()
    except UnicodeEncodeError:
        print("it was not a ascii-encoded unicode string")
        fp.close()


def mergeEpgData():
    channelsFile = open("channels.xml", "r", encoding='utf-8')
    programsFile = open("program.xml", "r", encoding='utf-8')
    epgFile = open("epg.xml", "a", encoding='utf-8')

    epgFile.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
    epgFile.write("<!DOCTYPE tv SYSTEM \"xmltv.dtd\">\n")
    epgFile.write(
        "<tv generator-info-name=\"Arnab Ghosh\" generator-info-url=\"https://github.com/arnab8820\">\n")
    epgFile.write(channelsFile.read())
    epgFile.write(programsFile.read())
    epgFile.write("</tv>\n")


# Process starts here
initEpgFiles()
channelList = getChannels()
progress = 0
channelFile = open("channels.xml", "a", encoding='utf-8')
programFile = open("program.xml", "a", encoding='utf-8')
for channel in channelList:
    writeEpgChannel(channel["channel_id"],
                    channel["channel_name"], channel["logoUrl"], channelFile)
    lowerRange = 0
    if prevEpgDayCount > 0:
        if channel["isCatchupAvailable"]:
            lowerRange = (prevEpgDayCount*-1)
        else:
            lowerRange = -1
    for offset in range(lowerRange, nextEpgDayCount+1):
        print("Getting EPG for "+str(channel["channel_id"]) +
              " "+channel["channel_name"]+" day "+str(offset))
        epgData = getEpg(channel["channel_id"], offset, 6)
        for epg in epgData:
            writeEpgProgram(channel["channel_id"],
                            epg["startEpoch"], epg["endEpoch"], epg["showname"],
                            epg["description"], epg["episodePoster"], programFile)
    progress += 1
    print("\n\nChannel Progress: " + str(progress) +
          "/"+str(len(channelList))+"\n\n")

channelFile.close()
programFile.close()

mergeEpgData()
print("Action complete")
