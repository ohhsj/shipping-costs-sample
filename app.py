#!/usr/bin/env python

import urllib
import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = makeWebhookResult(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def makeWebhookResult(req):
#    if req.get("result").get("action") != "hardware-estimator":
#        return {}
    result = req.get("result")
    parameters = result.get("parameters")
    dealsize = parameters.get("DealSize")
    batchsize = parameters.get("BatchSize")
    calculationtype = parameters.get("CalculationType")

    stddealsize = int(dealsize) / 100000.0
    
    #Assumes the following for PV estimations
    #                           Trades	Scenarios	Horizons	Calcs
    #Market Risk Sensitivities	100000	20	        1	        1
    #HSVaR	                    100000	500	        1	        1
    #Monte Carlo VaR	        100000	5000	    1	        1
    #MC VaR Factor Groups	    100000	5000	    1	        10
    #Additional VaR Horizons	100000	5000	    5	        10
    #Potential Future Exposure	100000	5000	    100	        1
    #PFE Stress Tests	        100000	5000	    100	        10
    #CVA Sensitivities	        100000	5000	    100	        50

    stdPVLookup = {'FRTB-SA': 10, 'HS VaR': 50, 'Monte Carlo VaR': 500, 'FRTB HS-IMA': 1000, 'PFE': 5000, 'PFE Stress Tests': 500000, 'FRTB-CVA': 2500000}
    
    dealPV = stddealsize * stdPVLookup[calculationtype]
    
    #Naked cores is 30 million PVs for 2x8 core and 10 adhoc runs i.e each run to complete in 2.4 hours
    #how to scale?
    numofCores = dealPV / 30
    
    speech = "Estimated PV Calculations (in million): %s, Num of Cores: %s, Calculation Type: %s." % (str(dealPV),str(numofCores),calculationtype)

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
