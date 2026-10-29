import sqlite3
import random
import math
import json


def main(): 
    T = random.int(0, 100) #Determines how many times it'll be reduced
                            #Will need to edit range most likely.
                            #depending on how many factoids per.
    outputForOz = dict()
    numCategories = 6
    numAnswersPerCategory = 5
    category = []

    for n in range(numCategories):
        category[n] = random.int(0, )


    try:

        connection = #Wonder what he'll want me to connect to
        cursor = connection.cursor()
        mainQuery = ("Select Factoidid from categories_Factoids natural join Factiods where category = ? and difficulty = ?")#update once you have the actual info
        getFactoidInfoQuery = ("select * from Factoid where factoid_id = ?")
        for i in range(numCategories): #This should run times equivalent to how many categories, 
                                        #running through the simulated annealing process on each group
                                        #of factoids.
            for m in range(numAnswersPerCategory):    
                cursor.execute(mainQuery, category[i], m + 1)
                allRows = cursor.fetchall()

                factoidID = simulatedAnnealing(T, allRows, cursor, mainQuery)
                cursor.execute(getFactoidInfoQuery, factoidID)
                answer = cursor.fetchone()
                outputForOz.update({"factoidID": answer[0], 
                                    "Answer": answer[1],
                                    "" #Finish
                                    })

    except sqlite3 as error:
        print(f"Your sql stuff crashed H")
        print(f"here's the error {error}")

    finally:
        if connection == True:
            connection.close()
            print("Stopped")





def simulatedAnnealing(T, allRows, cursor, mainQuery): #This isn't going to be a normal simulated annealing. That would't work, 
                            #I'm not searching for a specific node, just a random answer
    maxQuery = "select max(factoid.id) from ?"
    minQuery = "select min(factoid.id) from ?"
    totalQuery = "select count(factoid.id) from ?"
    cursor.execute(minQuery, mainQuery)
    minValue = cursor.fetchone()
    cursor.execute(maxQuery, mainQuery)
    selectedID = cursor.fetchone()
    cursor.execute(totalQuery, mainQuery)
    totalEntries = cursor.fetchone()
                                        #Currently /4 should hopefully good for the range
    while T > 0:
        reductionFactor = random.randint(0, math.floor(totalEntries / 4)) #Need to check math. 

        if selectedID <= minValue[0]:
            return minValue[0]

        selectedID -= reductionFactor

        T -= 1

    return selectedID

main()