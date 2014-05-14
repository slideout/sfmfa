#!/usr/bin/python

# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
import csv
import os, time, math, string, random
import pdb
import pygame
import shutil
import tty, sys, termios
import warnings

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.swarming import permutations_runner

import ch_model_params
import ms_model_params



SWARM_DEF = "search_def.json"
CH_SWARM_CONFIG = {
  "includedFields": [
    {
      "fieldName": "character",
      "fieldType": "string",
    }
  ],
  "streamDef": {
    "info": "mfaCh",
    "version": 1,
    "streams": [
      {
        "info": "mfaCh.csv",
        "source": "file://mfaCh.csv",
        "columns": [
          "*"
        ]
      }
    ]
  },
  "inferenceType": "TemporalAnomaly",
  "inferenceArgs": {
    "predictionSteps": [
      1
    ],
    "predictedField": "character"
  },
  "swarmSize": "medium"
}
MS_SWARM_CONFIG = {
  "includedFields": [
    {
      "fieldName": "gapMs",
      "fieldType": "int",
      "minValue": -250,
      "maxValue": 5000
    }
  ],
  "streamDef": {
    "info": "mfa",
    "version": 1,
    "streams": [
      {
        "info": "mfaTimings.csv",
        "source": "file://mfaTimings.csv",
        "columns": [
          "*"
        ]
      }
    ]
  },

  "inferenceType": "TemporalAnomaly",
  "inferenceArgs": {
    "predictionSteps": [
      1
    ],
    "predictedField": "gapMs"
  },
  "swarmSize": "medium"
}

modelCh = None
modelMs = None

screen = None
font = None
textLines = []



def gPrint( str, append=False ):
    global screen, font, textLines

    while len( textLines ) > (screen.get_height()-30)/20:
        # remove the top line from the list
        del textLines[0]

    if append:
        textLines[ len(textLines)-1 ] += str
    else:
        padding = ""
        while len(str) > 90:
            tmp = str[:90]
            textLines.append( padding + tmp )
            str = str[90:]
            padding = "        "
        textLines.append( padding + str)
    
    # erase the screen
    screen.fill((0,0,255))
    x = y = 0
    for line in textLines:
        label = font.render( line, True, (255,255,0))
        
        screen.blit(label, (x,y))
        
        y += 20
    
    pygame.display.update()
    
    
    

def swarmData():
    # prep and per-run cleanup    
    #    warnings.filterwarnings('error')
    if os.path.isfile("mfaCh.csv"):
        os.unlink("mfaCh.csv")
    if os.path.isfile("mfaTimings.csv"):
        os.unlink("mfaTimings.csv")

    
    # simple character data, random
    f = open("mfaCh.csv", "a")
    writer = csv.writer(f)
    writer.writerow(['character'])
    writer.writerow(['string'])
    writer.writerow('')
    for count in range(0,120):
        ch = random.randint( ord('1'), ord('z'))
        writer.writerow([ch])
    f.close()

    # timing data
    f = open("mfaTimings.csv", "a")
    writer = csv.writer(f)
    writer.writerow(["gapMs","reset"])
    writer.writerow(["int","int"])
    writer.writerow(['','R'])
    # load in some context data, so the swarm doesn't over-generalize the
    # the data that is generated for a single password
    for count in range(0,50):
        #writer.writerow( [ 0, 0 ])    # priming seems to distract the swarm, works better with learning 
        writer.writerow( [ random.randint( ord('1'), ord('z')) * 30, 0 ] )
        writer.writerow( [ random.randint( ord('1'), ord('z')) * 30, 0 ] )
        writer.writerow( [ random.randint( -50, 1500 ), 0 ])
        writer.writerow( [ random.randint( 20, 120 ), 1] )
    f.close()
    """
    # prior version used the password for swarming, but it's too specific a dataset to get a decent swarm 
    for index in range(len(data)):
        character = data[index]["character"]
        if index+1 < len(data):
            nextCharacter = data[index+1]["character"]
        else:
            nextCharacter = 0
        elapsedMs = data[index]["elapsedMs"]
        downMs = data[index]["downMs"]

        # simple sequence
        chWriter.writerow([character])
        
        # primer, elapsed+char, down+char, next, de-primer
        #msWriter.writerow(['R'])
        msWriter.writerow([0,0])
        msWriter.writerow([character*30,0])
        msWriter.writerow([nextCharacter*30,0])
        msWriter.writerow([elapsedMs,0])
        msWriter.writerow([downMs,1])

        index += 1
    """

    permutations_runner.runWithConfig(CH_SWARM_CONFIG, {'maxWorkers': 4, 'overwrite': True})
    # copy the model info to the current folder
    shutil.copy("./model_0/model_params.py", "./ch_model_params.py")

    permutations_runner.runWithConfig(MS_SWARM_CONFIG, {'maxWorkers': 4, 'overwrite': True})
    # copy the model info to the current folder
    shutil.copy("./model_0/model_params.py", "./ms_model_params.py")



def recordEntry():
    #
    # setup the list of data
    results = []

    # loop until ctrl-c or an enter is pressed    
    done = False
    while done == False:
        elapsedMs = 0
        
        # multiple keystrokes can come back here, if they're hit fast enough
        keystrokes = getChars()
        
        for key in keystrokes:
            if key["key"] == 306:
                sys.exit()      # ctrl-c
            if key["key"] == pygame.K_RETURN:
                done = True
                break
            #ch = chr( key["key"] )
            
            # store down/up and the char, final timing happens after all chars are inputted
            results.append( { "character": key["key"], "down": key["down"], "up": key["up"]})
                
    # go through the results and set the   down and elapsed times
    for index in range(len(results)):
        # down time is easy, when it went up minus when it went down
        downMs = results[index]["up"] - results[index]["down"]

        # elapsed is how long from "up" until the next key went down
        # as in, the transition time from this character to the next one
        elapsedMs =  0
        if index+1 < len(results):
            elapsedMs = results[index+1]["down"] - results[index]["up"]
        
        # window the elapsedMs
        if elapsedMs > 2000:
            elapsedMs = 2000
        if elapsedMs < -250:
            elapsedMs = -250
    
        results[index]["downMs"] = downMs
        results[index]["elapsedMs"] = elapsedMs

    return results

def getChars():
    """ old way, which can't get key down/up events 
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    """
    keystrokes = []
    while True:
        # if there are keystrokes, and all of them have an up time, finish
        if len(keystrokes) > 0:
            complete = True
            for key in keystrokes:
                if key["up"] == 0:
                    complete = False
                    break
            if complete:
                #for key in keystrokes:
                #    print chr(key["key"]), key
                return keystrokes
                
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                # add the key and start time into the list
                keystrokes.append( {"key": event.key, "down":currentTime(), "up":0})
                if event.key < 256   and  event.key != pygame.K_RETURN  and  string.printable.index( chr( event.key ) ) >= 0:
                    gPrint( chr( event.key ), True )
            elif event.type == pygame.KEYUP:
                # find the key and record the up time
                for key in keystrokes:
                    if key[ "key" ] != event.key:
                        continue
                    key[ "up" ] = currentTime()
            else:
                continue
    
    return None

def currentTime():
    # milliseconds
    return int(round(time.time() * 1000))

def readData( data, index ):
    # scale the character data up into the high range of the predictor
    # so that they can be learned as a sequence, vs parallel data
    character = data[index]["character"] * 30
    if index+1 < len(data):
        nextCharacter = data[index+1]["character"] * 30
    else:
        nextCharacter = 0
    elapsedMs = data[index]["elapsedMs"]
    downMs = data[index]["downMs"]
    
    return character, nextCharacter, elapsedMs, downMs

def readResult( result, cur, total, count ):
    
    tmp = result.inferences["anomalyScore"]
    
    if math.isnan(tmp):
        tmp = 1.0
    cur += tmp
    total += tmp
    count += 1
    
    return cur, total, count

def toCh( ch ):
    return chr( ch / 30 )




def learnUser():
    global modelCh, modelMs

    # get a simple password
    for count in range(3):
        gPrint( 'Enter your password (pass #' + str( count ) + "): ", False )
        
        # the keystroke recording method, returns a list of char and timing data back
        data = recordEntry()

        totalAnomaly = 0.0
        sampleCount = 0
        curAnomaly = 0

        chAS = "Ch anomalies: "
        msAS = "Ms anomalies: "
        for index in range(len(data)):
            character, nextCharacter, elapsedMs, downMs = readData( data, index )

            # train the character model
            result = modelCh.run({"character": character})
            curAnomaly = readResult( result, 0, 0, 0 )[0]
            chAS += " [" + toCh(character) + "]:" + str(curAnomaly)

            # train the timing/subSequence model
            
            #result = modelMs.run({"gapMs": 0})
            #curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
            for count in range(5):
                # subsequencing and priming
                modelMs.resetSequenceStates()
                result = modelMs.run({"gapMs": 0})
                curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
                
                curAnomaly = 0
                result = modelMs.run({"gapMs": character})
                curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
                result = modelMs.run({"gapMs": nextCharacter})
                curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
                result = modelMs.run({"gapMs": elapsedMs})
                curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
                result = modelMs.run({"gapMs": downMs})
                curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
            
            msAS += " [" + toCh(character) + "/" + toCh(nextCharacter) +"][" + str(elapsedMs) + "e/" + str(downMs)+ "d]:" + str(curAnomaly/4)

                   
        gPrint( "   Learning pass: " + str(count) + ", avg anomaly score: " + str(float(totalAnomaly)/float(sampleCount)) )
        gPrint( "      " + chAS )
        gPrint( "      " + msAS )
        



if __name__ == "__main__":
    # if swarming is on, swarm and exit
    if len(sys.argv) > 1  and sys.argv[1] == "swarm":
        swarmData()
        sys.exit()

    pygame.init()
    pygame.display.set_caption("SingleEntry MFA")
    screen = pygame.display.set_mode( [800,300] )
    screen.fill((0,0,255))    
    font = pygame.font.Font(None, 25)
    x = y = 0

    # setup the models
    modelCh = ModelFactory.create(ch_model_params.MODEL_PARAMS)
    modelCh.enableInference({"predictedField": "character"})
    modelMs = ModelFactory.create(ms_model_params.MODEL_PARAMS)
    modelMs.enableInference({"predictedField": "gapMs"})

    # train the cla on the data
    learnUser()
    gPrint( "Model trained, beginning test mode" )
  
    # disable learning, and loop until a blank passphrase was entered
    # checking each one for cumulative anomaly score
    modelCh.disableLearning()
    modelMs.disableLearning()
    while True:
        gPrint( "Test your password: " )
        data = recordEntry()
        if len(data) == 0:
            break;


        # pdb.set_trace()

        totalAnomaly = 0
        sampleCount = 0
        curAnomaly = 0
        chAS = "Ch anomalies: "
        msAS = "Ms anomalies: "
        for index in range(len(data)):
            character, nextCharacter, elapsedMs, downMs = readData( data, index )

            # test character sequence anomaly
            curAnomaly = 0  # ignore anomaly on the primer input
            result = modelCh.run({"character": character})
            curAnomaly,totalAnomaly,sampleCount = readResult( result, 0, totalAnomaly, sampleCount )
            chAS += " [" + toCh(character) + "]:" + str(curAnomaly)
             
            
            # now the timing anomaly

            # subsequence and priming
            modelMs.resetSequenceStates()
            # primer, ignored
            modelMs.run({"gapMs": 0})

            # start char, end char, elapsed, down            
            curAnomaly = 0
            result = modelMs.run({"gapMs": character})
            curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
            result = modelMs.run({"gapMs": nextCharacter})
            curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
            result = modelMs.run({"gapMs": elapsedMs})
            curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
            result = modelMs.run({"gapMs": downMs})
            curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
                    
            msAS += " [" + toCh(character) + "->" + toCh(nextCharacter) +"][" + str(elapsedMs) + "e/" + str(downMs)+ "d]:" + str(curAnomaly/4)


        gPrint( "   Testing pass: avg anomaly score: " + str(float(totalAnomaly)/float(sampleCount)) )
        gPrint( "      " + chAS )
        gPrint( "      " + msAS )

        # show whether the trained user typed the right password
        passFail = "Probable pass"
        avgAnomaly = float(totalAnomaly)/float(sampleCount)
        
        # this is a silly way to predict failure, look at Subutai's anomaly histogram code and integrate someday        
        if avgAnomaly > .1:
            passFail = "Probable fail"
        gPrint( "Overall anomaly: " + str(avgAnomaly) + ": " + passFail )
  




