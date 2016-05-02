#!/usr/bin/python2.7

score = 301
while(score > 0):
    print "Your score is now %s" % score
    user_input = int(raw_input("What did you score? "))
    if user_input == 180:
        print "YOU GOT A 180"
    if score - user_input < 0:
        print "You BUSTED"
        continue
    score = score - user_input
    if score == 0:
        print "YOU WIN"
        exit()
    if score == 200:
        print "YOU WIN A PRIZE"
    elif score == 300:
        print "HOW DID YOU ONLY SCORE 1 POINT"
    else:
        print "NO PRIZE FOR YOU"
print "ALL DONE"
