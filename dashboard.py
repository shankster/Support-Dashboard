import time
import datetime
import json
import os
import requests
import pytz
import json
import operator
from jsontraverse.parser import JsonTraverseParser

counter=0

def fetchURLfromJSON(param):
    with open('geckoURList.json') as fp:
        data=json.load(fp)
    value=data[param]
    return value

def fetchAgentsfromJSON():
    with open('agentsList.json') as fp:
        data=json.load(fp)
    return data

agentsList=fetchAgentsfromJSON()
masterList=[{},{},{},{},{},{},{},{},{},{},{},{}]
ticketStatusCodes={"open": 2,"pending": 3,"resolved":4,"closed":5,"underInvestigation":7,"inProgress":8,"callbackScheduled":9,"devfollowup":10,"migration":11}
countTotals={2:0,3:0,4:0,5:0,6:0,7:0,8:0,9:0,10:0,11:0}
apiK=os.environ["GECKOBOARD_API_KEY"]
agentsCount={}
geckoURLs={}
breakdownUrl="gecko_widget_url"

baseURL="https://push.geckoboard.com/v1/send/"
baseStore={
   "api_key":apiK,
   "data":{}
}

def convertListToString(lst):
    for each in range(len(lst)):
        lst[each]=str(lst[each])
    return lst

def merge(dict1, dict2):
    result=dict1
    for k in dict2.items():
        if(k in result):
            result[k]=result[k]+dict2[k]
        else:
            result[k]=dict2[k]
    return result

#Forms URLs for each of the Geckoboard requests
def urlAttacher(url):
    global baseURL
    return (baseURL+url)

#Sorts the agent's counts by their number of tickets
def sortDict(nSDict):
    sortedDict = sorted(nSDict.items(), key=operator.itemgetter(1),reverse=True)
    return dict(sortedDict)

#Forms URLs for each of the FD requests
def urlMaker(domain,idAG,status,pageNumber,agentOrGroup):
    domain=domain
    basicUrl="https://{}.freshdesk.com/api/v2".format(domain)
    operation="search"
    item="tickets"
    parameter="query"
    idAG=idAG
    status=status
    queryString=""
    statusString=''
    statusLength=len(status)
    if statusLength==1:
        statusString='status:{}'.format(status[0])
    elif statusLength>1:
        for eachStatus in status:
            statusString=statusString+('status:{}').format(eachStatus)+' OR '
        statusString=statusString[:(len(statusString)-4)]

    if agentOrGroup=="group":
        queryString="group_id:{} AND ({})".format(idAG,statusString)
    else:
        queryString="agent_id:{} AND group_id:9 AND ({})".format(idAG,statusString)

    page="page={}".format(pageNumber)
    requestUrl=basicUrl+'/'+operation+'/'+item+'?'+page+'&'+parameter+"="+"\""+queryString+"\""
    #print (requestUrl+'\n')
    return requestUrl

def makeRequest(url):
    url=url
    apiKey=os.environ["FRESHDESK_AGENT_API_KEY"]
    password=""
    apiRequest=requests.get(url,auth=(apiKey,password))
    apiResponse=json.dumps(apiRequest.json(),indent=4,sort_keys=True)
    #print("MakeReq Type: {}".format(type(apiResponse)))
    return apiResponse

def totalFinder(statusCode,code,agentOrGroup):
    uri=urlMaker('replace_with_fd_site_name',code,[statusCode],1,agentOrGroup)
    print("\nURL= {}".format(uri))
    apiResponse=makeRequest(uri)
    #print("Blah Type: {}".format(type(apiResponse)))
    if agentOrGroup=="group":
        findCount(statusCode,apiResponse)
    responseParser=JsonTraverseParser(apiResponse)
    total=responseParser.traverse("total")
    return total

def totalFinderAgents(agentID,agentOrGroup):
    uri=urlMaker('replace_with_fd_site_name',agentID,[2,10],1,"agent")
    print("\nURL= {}".format(uri))
    apiResponse=makeRequest(uri)
    responseParser=JsonTraverseParser(apiResponse)
    total=responseParser.traverse("total")
    return total

#Processes the response to find the ticket count for each of the agent_IDs
def findCount(status,response):
    global openDict,masterList
    openDict={}
    dataR=json.loads(response)
    resultSet=dataR["results"]
    for each in resultSet:
        agent_id=each["responder_id"]
        if(agent_id != None):
            if(agent_id in openDict):
                openDict[agent_id]+=1
            else:
                openDict[agent_id]=1
    openDict=sortDict(openDict)
    
    masterList[status]=openDict

    return sortDict


#Geckoboard Dashboard Functions
def numericGauge(value,min,max):
    global baseStore
    numericStore={}
    numericStore["item"]=value
    numericStore["min"]={}
    numericStore["min"]["value"]=min
    numericStore["max"]={}
    numericStore["max"]["value"]=max
    baseStore["data"]=numericStore
    return json.dumps(baseStore)

def pieChart(value,label,color):
    global baseStore
    barStore={}
    barStore["item"]=[]
    holdList=[]
    count=len(value)
    store={}
    for each in range(count):
        store["value"]=value[each]
        store["label"]=label[each]
        store["color"]=color[each]
        holdList.append(store)
        store={}
    barStore["item"]=holdList
    baseStore["data"]=barStore
    return json.dumps(baseStore)

def barChart(labels,series):
    global baseStore
    xAxis={}
    root={}
    xAxis['labels']=labels
    root["x_axis"]=xAxis
    root["series"]=[]

    containerData={}
    containerData["data"]=series
    root["series"].append(containerData)

    baseStore["data"]=root
    return json.dumps(baseStore)


def pushNumeric(statusCode,min,max,widgetName):
    global countTotals
    group="group"
    value=totalFinder(statusCode,6,group)
    countTotals[statusCode]=value
    pushJSON=numericGauge(value,min,max)
    url=urlAttacher(fetchURLfromJSON(widgetName))
    req=requests.post(url,pushJSON)
    reqStatus=req.status_code
    print("Ticket Status Code: {}   Request Status Code: {}\n".format(statusCode,reqStatus))
    return reqStatus


def pushNumericGauge():
    openPush=pushNumeric(ticketStatusCodes["open"],10,130,"open")
    devFollowupPush=pushNumeric(ticketStatusCodes["devfollowup"],10,75,"devFollowup")
    migrationPush=pushNumeric(ticketStatusCodes["migration"],0,20,"migration")
    callbackScheduledPush=pushNumeric(ticketStatusCodes["callbackScheduled"],0,20,"callbackScheduled")
    inProgressPush=pushNumeric(ticketStatusCodes["inProgress"],25,150,"inProgress")
    pendingPush=pushNumeric(ticketStatusCodes["pending"],100,500,"pending")
    underInvestigationPush=pushNumeric(ticketStatusCodes["underInvestigation"],10,100,"underInvestigation")

def pushPieChart():
    global countTotals

    labels=["Open","Dev Followup","Migration","In Progress","Under Investigation","Callback Scheduled"]
    value=[
        countTotals[ticketStatusCodes["open"]],
        countTotals[ticketStatusCodes["devfollowup"]],
        countTotals[ticketStatusCodes["migration"]],
        countTotals[ticketStatusCodes["inProgress"]],
        countTotals[ticketStatusCodes["underInvestigation"]],
        countTotals[ticketStatusCodes["callbackScheduled"]]]
    colour=["#d50000","#e53935","#ff5252","#ef5350","#e57373","#ffcdd2"]

    pushUrl=pieChart(value,labels,colour)
    req=requests.post(urlAttacher(breakdownUrl),pushUrl)
    print("Push Pie Chart: {}\n".format(req.status_code))

def pushBarChart():
    agentsBreakUp()
    global agentsCount
    #mergedDict=sortDict(merge(masterList[2],masterList[10]))
    labelList=[]
    valueList=[]
    for key,value in agentsCount.items():
        if key in agentsList:
            name=agentsList[key]
            labelList.append(name)
            valueList.append(value)
    print("AgentId:{}\nCount:{}".format(labelList,valueList))
    pushUrl=barChart(labelList,valueList)
    req=requests.post(urlAttacher(fetchURLfromJSON("openCount")),pushUrl)
    print("Push Bar Chart: {}\n".format(req.status_code))

def agentsBreakUp():
    global agentsList,agentsCount
    group="agent"
    for agentID,agentName in agentsList.items():
        count=totalFinderAgents(agentID,"agent")
        agentsCount[agentID]=count
    agentsCount=sortDict(agentsCount)
    print("Counter: {}".format(agentsCount))

if __name__=="__main__":
    pushNumericGauge()
    pushBarChart()