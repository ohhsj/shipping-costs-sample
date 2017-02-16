#!/usr/bin/env python
import math
import urllib2
import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    url = 'https://api.heroku.com/apps/aa-hw-estimator-engine/config-vars'
    req2 = urllib2.Request(url)
    req2.add_header('Accept', 'application/vnd.heroku+json; version=3')
    req2.add_header('Authorization', 'Bearer eb027009-93dd-41cf-8f6b-006956b4790d')
    herokuConfig = json.load(urllib2.urlopen(req2))
    
    print("Config-Var:")
    print(herokuConfig['API_KEY'])
    
    req = request.get_json(silent=True, force=True)

    api_key = request.headers["api-key"]
    
    print("api-key:")
    print(api_key)
    
    if api_key != herokuConfig['API_KEY']:
        return make_response({"displayText": "Authorization error"})

    print("Request:")
    print(json.dumps(req, indent=4))
    
    res = makeWebhookResult(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def makeWebhookResult(req):
    result = req.get("result")
    parameters = result.get("parameters")
    dealsize = int(parameters.get("DealSize"))
    batchsize = int(parameters.get("BatchSize"))
    calculationtype = parameters.get("CalculationType")

    stddealsize = dealsize / 100000.0
    
    #Assumes the following for PV estimations
    #                           Trades	Scenarios	Horizons	Calcs   Total
    #Market Risk Sensitivities	100000	20	        1	        1       2000000
    #HSVaR	                    100000	500	        1	        1       50000000
    #Monte Carlo VaR	        100000	5000	    1	        1       500000000
    #MC VaR Factor Groups	    100000	5000	    1	        10      5000000000
    #Additional VaR Horizons	100000	5000	    5	        10      25000000000
    #Potential Future Exposure	100000	5000	    100	        1       50000000000
    #PFE Stress Tests	        100000	5000	    100	        10      500000000000
    #CVA Sensitivities	        100000	5000	    100	        50      2500000000000
        
    #in millions
    stdPVLookup = {
        'Market Risk Sensitivities': 2,
        'FRTB-SA': 10, 
        'HS VaR': 50, 
        'Monte Carlo VaR': 500, 
        'FRTB HS-IMA': 1000, 
        'PFE': 5000, 
        'PFE Stress Tests': 500000, 
        'FRTB-CVA': 2500000
    }
    #Vectorization per deal with the number of scenarios and horizons
    vectorizationLookup = {
        'Market Risk Sensitivities': 1,
        'FRTB-SA': 1, 
        'HS VaR': 1, 
        'Monte Carlo VaR': 10, 
        'FRTB HS-IMA': 10, 
        'PFE': 250, 
        'PFE Stress Tests': 500, 
        'FRTB-CVA': 1000
    }
    
    dealPV = stddealsize * stdPVLookup[calculationtype]
    dealVector = vectorizationLookup[calculationtype]
    
    #Naked cores is 60 million PVs for 16 core and 10 adhoc runs i.e each run to complete in under 30mins
    #Looking at around 500 valuations per core per second
    #if the numnber of runs is just 1, then we can make use of 4 hours
    #if the number of runs is more than 1 but less than 5, then we can make use of 2 hours
    #if the number of runs is 5 or more but less than 10, then we can make use of 1 hour
    #if the number of runs is 10 or more then we need to complete in 30mins
    
    if batchsize == 1:
        batchScale = 1
    elif batchsize > 1:
        batchScale = 2
    elif batchsize >= 5:
        batchScale = 4
    elif batchsize >= 10:
        batchScale = 8    
    else:
        batchScale = 0
        
    numofCores = math.ceil(dealPV / (30 * dealVector * 0.8)) * 16
    
    #RAM size
    rawRAM = math.ceil(dealPV / (30 * dealVector * 0.8)) 
    if rawRAM % 2 != 0:
        rawRAM += 1
    RAM = rawRAM * 16
    
    speech = "Estimated PV Calculations (in million): %s, Num of Cores: 2 x %s, RAM: %s, Calculation Type: %s." % (str(dealPV),str(numofCores),str(RAM),calculationtype)

    print("Response:")
    print(speech)
    respParam = {}
    respParam['corenum'] = str(numofCores)
    respParam['dealPV'] = str(dealPV)
    respParam['dealVector'] = str(dealVector)
    respParam['ram'] = str(RAM)

    return {
        "speech": speech,
        "displayText": speech,
        #"data": {},
        "contextOut": [{"name":"estimator", "lifespan":5, "parameters": respParam }] ,
        "source": "aa-hw-estimator-engine",
        "followupEvent": {"name":"ENDCONVERSATION","data": respParam}
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=True, port=port, host='0.0.0.0')
