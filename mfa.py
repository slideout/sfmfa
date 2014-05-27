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
import os, time, string
import math, random, numpy
import pdb
import pygame
import shutil
import tty, sys, termios
import warnings

from nupic.frameworks.opf.modelfactory import ModelFactory

import ch_model_params
import ms_model_params




screen = None
font = None
textLines = []
def gPrint( str, append=False ):
    """ print to the graphics terminal
    
    """
    global screen, font, textLines

    if screen is None:
        pygame.init()
        pygame.display.set_caption("SingleEntry MFA")
        screen = pygame.display.set_mode( [800,300] )
        screen.fill((0,0,255))    
        font = pygame.font.Font(None, 25)
        x = y = 0
    

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
    character = chr(data[index]["character"])
    if index+1 < len(data):
        nextCharacter = chr(data[index+1]["character"])
    else:
        nextCharacter = ' '
    elapsedMs = data[index]["elapsedMs"]
    downMs = data[index]["downMs"]
    
    return character, nextCharacter, elapsedMs, downMs



def getFilename( mode ):
    filename = 'mfa'
    if mode == 'learn':
        filename += 'Learn'
    elif mode == 'test':
        filename += 'Test'
    filename += ".csv"
    return filename
        
        


def learnData( mode ):
    """ read and save passphrase keystroke data
    
        mode='learn'  record three sequences of the passphrase and save the data for later
    
        mode='test'   record a single passphrase and save for testing
    
    
    """

    # setup the output files and prep them
    filename = getFilename( mode )    
    if os.path.isfile( filename ):
        os.unlink( filename )
    f = open(filename, "a")
    writer = csv.writer(f)
    writer.writerow(["character","nextCharacter", "elapsedMs", "downMs", "reset"])
    writer.writerow(["string","string", "int","int","int"])
    writer.writerow(['','','','','R'])
    

    for count in range(3 if mode  == 'learn' else 1):
        if mode == 'learn':
            gPrint( 'Enter your password/passphrase (pass #' + str( count ) + "): ", False )
        elif mode == 'test':
            gPrint( 'Enter the testing password/passphrase: ', False )
        
        # the keystroke recording method, returns a list of char and timing data back
        data = recordEntry()

        for index in range(len(data)):
            character, nextCharacter, elapsedMs, downMs = readData( data, index )
            writer.writerow( [character,nextCharacter,elapsedMs,downMs,0 if index<len(data)-1 else 1])
    
    f.close()



def loadData( mode ):
    filename = getFilename( mode )    
    f = open(filename, "r")
    reader = csv.reader(f)

    # skip headers
    reader.next()
    reader.next()
    reader.next()
    
    data = []
    phrase = []
    for row in reader:
        phrase.append( { 'character': row[0], 'nextCharacter': row[1], 'elapsedMs': int(row[2]), 'downMs': int(row[3]) } )
        if int(row[4]) == 1:
            data.append( phrase )
            phrase = []
        
    return data


def readResult( result, cur, total, count ):
    
    tmp = result.inferences["anomalyScore"]
    
    if math.isnan(tmp):
        tmp = 1.0
    cur += tmp
    total += tmp
    count += 1
    
    return cur, total, count



def run():
        
    # setup the models
    modelCh = ModelFactory.create(ch_model_params.MODEL_PARAMS)
    modelCh.enableInference({"predictedField": "character"})

    modelMs = ModelFactory.create(ms_model_params.MODEL_PARAMS)
    modelMs.enableInference({"predictedField": "timing"})


    # train both models on the learned data, then run the test data through both models
    for mode in ['learn','test']:
        # returns a list of lists, each index is a passphrase sequence
        data = loadData( mode )
        
        chAS = "Character sequence anomalies (" + mode + "):  [Character]:AnomalyScore"
        msAS = "Transition timing anomalies (" + mode + "):  [Character/NextCharacter/ElapsedMs/DownMs]:sum(AnomalyScore)"
        totalAnomaly = 0.0
        sampleCount = 0
        curAnomaly = 0

        if mode == 'test':
            modelCh.disableLearning()
            modelMs.disableLearning()
        
        for count in range(25 if mode == 'learn' else 1):
            if mode == 'learn':
                sys.stdout.write( 'Learning pass: ' + str(count) + '\r' )
            sys.stdout.flush()

            phrase = data[random.randrange( len(data) )]
            
            modelCh.resetSequenceStates()
            modelCh.run( {'character':' '})     # character priming
            chAS += '\n                    '
            
            msAS += '\n                    '
            
            for index in range(len(phrase)):
                row = phrase[index]
                
                # train the character model
                result = modelCh.run({'character': row[ 'character'] })
                curAnomaly = readResult( result, 0, 0, 0 )[0]
                chAS += " [" + row['character'] + "]:" + str(curAnomaly)
            
                # train the timing/subsequence model
                modelMs.resetSequenceStates()
    
                # subsequencing / priming
                result = modelMs.run( {'character':' ', 'timing':None })
                
                curAnomaly = 0
                result = modelMs.run( {'character':row['character'], 'timing':None }) 
                curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
    
                result = modelMs.run( {'character':row['nextCharacter'], 'timing':None }) 
                curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
                
                result = modelMs.run( {'character':None, 'timing':row['elapsedMs'] }) 
                curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
    
                result = modelMs.run( {'character':None, 'timing':row['downMs'] }) 
                curAnomaly,totalAnomaly,sampleCount = readResult( result, curAnomaly, totalAnomaly, sampleCount )
    
                msAS += " [" + row['character'] + "/" + row['nextCharacter'] +"/" + str(row['elapsedMs']) + "/" + str(row['downMs'])+ "]:" + str(curAnomaly)
                
        
        print( "                     \n" )
        print( "      " + chAS )
        print( "      " + msAS )
        
        if mode == 'test':
            # show whether the tested data matched the trained data
            passFail = "Probable pass"
            
            # this may be an overly simple way to predict failure, look at Subutai's anomaly histogram code and integrate someday        
            if totalAnomaly > .5:
                passFail = "Probable fail"
            print( "Total anomaly: " + str(totalAnomaly) + ": " + passFail )
        



if __name__ == "__main__":
    
    if len(sys.argv) == 0:
        print 'mfa [runType]'
        print '   runTypes:'
        print '       learn - record keystroke data for learning'
        print '       test  - record keystroke data for testing'
        print '       run   - train the model with learned data, then run the test data and output anomaly info'
        sys.exit()

    if sys.argv[1] == 'learn':
        learnData( 'learn')
        sys.exit()

    if sys.argv[1] == 'test':
        learnData( 'test' )
        sys.exit()
        
    if sys.argv[1] == 'run':
        run()
        sys.exit()




