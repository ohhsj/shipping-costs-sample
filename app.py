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
    url = 'https://api.heroku.com/apps/serene-plains-17463/config-vars'
    req2 = urllib2.Request(url)
    req2.add_header('Accept', 'application/vnd.heroku+json; version=3')
    req2.add_header('Authorization', 'Bearer eb027009-93dd-41cf-8f6b-006956b4790d')
    herokuConfig = urllib2.urlopen(req2).read()

    req = request.get_json(silent=True, force=True)

    api_key = request.headers["api-key"]
    if api_key != herokuConfig['API_KEY']:
        return make_response({"displayText": "Here it is"});

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
    dealsize = parameters.get("DealSize")
    batchsize = parameters.get("BatchSize")
    calculationtype = parameters.get("CalculationType")

    stddealsize = int(dealsize) / 100000.0
    
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
    
    dealPV = stddealsize * stdPVLookup[calculationtype]
    
    #Naked cores is 60 million PVs for 2x8 core and 10 adhoc runs i.e each run to complete in 2 hours
    #Looking at around 500 valuations per core per second
    numofCores = math.ceil(dealPV / 60) * 8
    
    #RAM size
    RAM = math.ceil(dealPV / 60) * 32
    
    speech = "Estimated PV Calculations (in million): %s, Num of Cores: 2 x %s, RAM: %s, Calculation Type: %s." % (str(dealPV),str(numofCores),str(RAM),calculationtype)

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        #"data": {},
        # "contextOut": [],
        "source": "apiai-onlinestore-shipping"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=True, port=port, host='0.0.0.0')
