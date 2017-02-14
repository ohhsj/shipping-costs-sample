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

    stddealsize = int(dealsize) / 100000
    stdPVLookup = {'FRTB-SA': 10, 'HS VaR': 50, 'Monte Carlo VaR': 500, 'FRTB HS-IMA': 1000, 'PFE': 5000, 'PFE Stress Tests': 500000, 'FRTB-CVA': 2500000}

    print(str(stdPVLookup[calculationtype]))
    
    dealPV = stddealsize * stdPVLookup[calculationtype]

    print(str(dealPV))
    
    speech = "This is a response back from the webhook with the parameters. Estimated Deal PV: %s, Batch size: %s, Calculation Type: %s." % (str(stddealsize),batchsize,calculationtype)

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
