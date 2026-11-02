import sqlite3
import random
import math
from pathlib import Path
import json


def main(): 
    #oneCatFactoids = dict()
    oneCatFactoids = [] #List instead? Dictionary overwrites.
    numCategories = 6
    numAnswersPerCategory = 5
    category = [-1, -1, -1, -1, -1, -1]
    categoryOptions = [] #This is a different way to store categories. They aren't normalized so I had to normalize them essentially
    outputForOz = []

    


    try:

        dbPath = Path(__file__).resolve().parent / "enwiki-20220501-pages-articles-multistream.classified.db"
        connection = sqlite3.connect(dbPath)
        print(f"Using database: {dbPath}")

        cursor = connection.cursor()
        #everything in this section is choosing the categories.
        cursor.execute("select count(id) from categories") 
        totNumberCategories = cursor.fetchone()[0] 
        cursor.execute("select id from categories")
        for m in range(totNumberCategories):
            categoryOptions.append(cursor.fetchone()[0]) #List of all id's but with the list's organizaton

        category = random.sample(categoryOptions, numCategories) #Today I learned the random module had this. Tried a while loop to fix the duplicate category problem, but that didn't work /:
        print(f"category is {category}")
        

        #below here is selecting the actual factoids.
        mainQuery = ("Select factoids.id from factoid_categories left join factoids on factoid_categories.factoid_id = factoids.id where factoid_categories.category_id = ? and difficulty = ?")#update once you have the actual info
        getFactoidInfoQuery = ("select * from factoids where id = ?")

        factoidContainingArray = FactoidPicker(mainQuery, getFactoidInfoQuery, numCategories, numAnswersPerCategory, cursor, category, oneCatFactoids) #Get the factoids I'm starting with

        for categoryNumber in range(numCategories):
            bestArray, bestScore = HillClimbingFunction(cursor, factoidContainingArray[categoryNumber], mainQuery, category, categoryNumber)
            for factoidAmount in range(numAnswersPerCategory):
                cursor.execute(getFactoidInfoQuery, (bestArray[factoidAmount],))
                answer = cursor.fetchone()
                outputForOz.append({"factoidID": answer[0], 
                                   "Answer": answer[3],  #Jeopardy will say this one
                                    "Question": answer[2] #The user will say this one
                            })

        print(outputForOz)


        
    except sqlite3.Error as error:
        print(f"Your sql stuff crashed H")
        print(f"here's the error {error}")

    finally:
        if connection is not None:
            connection.close()
            print("Stopped")





#Picks all the initial factoids before hill climbing
def FactoidPicker(mainQuery, getFactoidInfoQuery, numCategories, numAnswersPerCategory, cursor, category, oneCatFactoids):
    factoidContainingArray = []
    for i in range(numCategories): #run times equivalent to how many categories. Outputs factoidContainingArray which houses every group of factoids
            if i != 0:
                factoidContainingArray.append(oneCatFactoids)
                oneCatFactoids = []
            for m in range(numAnswersPerCategory):    
                
                
                
                factoidID = randomFactoidState(cursor, mainQuery, category, i, m)
                cursor.execute(getFactoidInfoQuery, (factoidID,))
                answer = cursor.fetchone()
                if answer is not None:
                    oneCatFactoids.append(answer[0]
                                    )
            categoryQuery = ("Select title from categories where id = ?")

    print("Categories")
    for i in range(len(category)):
        cursor.execute(categoryQuery, (category[i],))
        print(cursor.fetchone())
    factoidContainingArray.append(oneCatFactoids)
    print(f"final output hopefully {factoidContainingArray}")

    return factoidContainingArray

def randomFactoidState(cursor, mainQuery, category, i, m):
    cursor.execute(mainQuery, (category[i], m + 1))
    factoidID = None
    seen = 0

    for (candidateID,) in cursor: #Apparently this is called reservoir sampling (thanks stack overflow) Before this I was getting all the rows and uh
                                              #My very strong desktop ran out of memory. So this was my solution. Was I probably doing it wrong, yes. But I don't have to deal with that
                                              #anymore now. so ha
        seen += 1
        if random.randrange(seen) == 0:
            factoidID = candidateID

    if factoidID is None: #there's some categories that don't have high difficulty questions. This catches those. There had better not be categories that don't have 5 questions period, 
                            #Cause I'm not accounting for that unless it actually becomes a problem. Lucky this problem came up because of whoever "darren korb" is
        noMoreDifficultQuestions = "select factoids.id from factoid_categories left join factoids on factoid_categories.factoid_id = factiods.id where factoid_cateogries.category_id = ?"
        cursor.execute(noMoreDifficultQuestions, (category[i],))
        seen = 0
        for (candidateID,) in cursor:
            seen += 1
            if random.randrange(seen) == 0:
                factoidID = candidateID
    return factoidID


def HillClimbingFunction(cursor, factoidArray, mainQuery, category, categoryNumber): 
    restarts = 50
    generations = 50
    bestScore = float("-inf")

    for _ in range(restarts):
        #Changed dimitri's idea a bit based on what I had. Using the full array instead of just individual states.
        currentScore = evaluate(factoidArray, cursor)

        for _ in range(generations):#climb uphill moves automatically
            mutatedArray = mutate(cursor, factoidArray, mainQuery, category, categoryNumber)
            mutatedScore = evaluate(mutatedArray, cursor)

            if mutatedScore > currentScore:
                factoidArray = mutatedArray
                currentScore = mutatedScore

        #track optimum
        if currentScore > bestScore:
            bestArray = factoidArray
            bestScore = currentScore

    return bestArray, bestScore

def evaluate(factoidArray, cursor):
    score = 0
    tagArray = []
    #Dimitri's response on discord minus the two parts I have to ask
    #So here is where we incorporate tags. 
    #If there is no matching factoid tags compared to the rest of the factoids in the current state, then you subtract points.
    #If there is 1 matching factoid tags, then you add a point.
    #If there is 2 matching factoid tags, then you add two points.
    #If there is 3 or more matching factoid tags, then you add three+ points depending on how much continued overlap.
    tagQuery = ("Select tag_id from factoid_tags where factoid_id = ?")
  
    for factoid_id in factoidArray:
        cursor.execute(tagQuery, (factoid_id,))
        #Apparently this wasn't working properly because in was checking based off of it being a list with all the tags. None had that. 
        #But making this into a set should work
        tags = {row[0] for row in cursor.fetchall()}
        tagArray.append(tags)
        
    #need to compare every factoid to every other factoid to figure out if there's equivalences
    #That then is reflected in the shared tags amount. according to dimitri's stuff, I think adding that is the equivalence?
    for i in range(len(tagArray)):
        for j in range(i + 1, len(tagArray)):
            sharedTagsAmount = len(tagArray[i] & tagArray[j])
            
            if sharedTagsAmount > 0:
                score += sharedTagsAmount
            else:
                score -= 1

    return score

def mutate(cursor, factoidArray, mainQuery, category, categoryNumber):
    candidate = factoidArray.copy()
    selectedIndexToMutate = random.randrange(len(candidate))
    #selectedIndex should work for the difficulty considering the numbers in the index should match the difficulty - 1. I think?
    candidate[selectedIndexToMutate] = randomFactoidState(cursor, mainQuery, category, categoryNumber, selectedIndexToMutate)    

    return candidate

main()