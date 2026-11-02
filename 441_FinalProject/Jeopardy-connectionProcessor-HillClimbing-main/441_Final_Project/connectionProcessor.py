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
        cursor.execute("select count(id) from categories") #how many entries exist in the table
        totNumberCategories = cursor.fetchone()[0] #realistically 0 should just be the count
        cursor.execute("select id from categories")
        for m in range(totNumberCategories):
            categoryOptions.append(cursor.fetchone()[0]) #List of all id's but with the list's organizaton
        print(f' Yo this is the number of possibilities of categories {totNumberCategories}')

        for n in range(numCategories):
            category[n] = categoryOptions[random.randint(0, len(categoryOptions)-1)] #can select the same category twice. MAKE A FIX AFTER IT WORKS HUNTER
        print(f"category is {category}")
        

        #below here is selecting the actual factoids.
        mainQuery = ("Select factoids.id from factoid_categories left join factoids on factoid_categories.factoid_id = factoids.id where factoid_categories.category_id = ? and difficulty = ?")#update once you have the actual info
        getFactoidInfoQuery = ("select * from factoids where id = ?")

        factoidContainingArray = FactoidPicker(mainQuery, getFactoidInfoQuery, numCategories, numAnswersPerCategory, cursor, category, oneCatFactoids) #Get the factoids I'm starting with

        for categoryNumber in range(numCategories):
            print("We're moving")
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
    for i in range(numCategories): #This should run times equivalent to how many categories. Outputs factoidContainingArray which houses every group of factoids
            if i != 0:
                factoidContainingArray.append(oneCatFactoids)
                oneCatFactoids = []
            for m in range(numAnswersPerCategory):    
                
                
                
                factoidID = randomFactoidState(cursor, mainQuery, category, i, m)
                print(f"Is it taking longer after or before this? {factoidID}")
                cursor.execute(getFactoidInfoQuery, (factoidID,))
                answer = cursor.fetchone()
                if answer is not None:
                                            #"factoidID": This is what I'm storing. I just need the id here though
                    oneCatFactoids.append(answer[0]
                                        #This is where answer stuff was originally stored. Prob delete later, but for now I'm just commenting it for reference.
                                        #, #This naming scheme is exceptionally confusing. Gl OZ
                                    #"Answer": answer[3],  #Jeopardy will say this one
                                    #"Question": answer[2] #The user will say this one
                                    )
                print(f"What is happening? i {i} and m {m} and oneCatFactoids{oneCatFactoids}")
            categoryQuery = ("Select title from categories where id = ?")
            print("Categories")
            for i in range(len(category)):
                cursor.execute(categoryQuery, (category[i],))
                print(cursor.fetchone())
            print("Here's one of the category's factoids homeslice")
            print(oneCatFactoids)

    factoidContainingArray.append(oneCatFactoids)
    print(f"final output hopefully {factoidContainingArray}")

    return factoidContainingArray

def randomFactoidState(cursor, mainQuery, category, i, m):
    cursor.execute(mainQuery, (category[i], m + 1))
    factoidID = None
    seen = 0

    for (candidateID,) in cursor: #Apparently this is called reservoir sampling (thanks stack overflow) Before this I was getting all the rows and uh
                                              #My very strong desktop ran out of memory. So this was my solution
        seen += 1
        if random.randrange(seen) == 0:
            factoidID = candidateID

            if factoidID is None:
                continue
    return factoidID


def HillClimbingFunction(cursor, factoidArray, mainQuery, category, categoryNumber): #This is mostly a placeholder. It just returns a random selection of stuff   
    answer = []
    restarts = 2
    generations = 2
    currentState = -1
    bestState = -1
    bestScore = float("-inf")

    for _ in range(restarts):
        #Is this supposed to be the entire array of factoids, or one specific point?
        currentScore = evaluate(factoidArray, cursor)

        # Climb the local hill by accepting uphill moves immediately
        for _ in range(generations):
            mutatedArray = mutate(cursor, factoidArray, mainQuery, category, categoryNumber)
            mutatedScore = evaluate(mutatedArray, cursor)

            if mutatedScore > currentScore:
                factoidArray = mutatedArray
                currentScore = mutatedScore

        # Track the global optimum across all restarts
        if currentScore > bestScore:
            bestArray = factoidArray
            bestScore = currentScore

    return bestArray, bestScore

def evaluate(factoidArray, cursor):
    factoidsAmount = 5
    score = 0
    tagArray = []
    #So here is where we incorporate tags. 
    #If there is no matching factoid tags compared to the rest of the factoids in the current state, then you subtract points.
    #If there is 1 matching factoid tags, then you add a point.
    #If there is 2 matching factoid tags, then you add two points.
    #If there is 3 or more matching factoid tags, then you add three+ points depending on how much continued overlap.
    tagQuery = ("Select tag_id from factoid_tags left join factoids where factoids.id = ?")
    for n in range(factoidsAmount): #There's 5 factoids per. That's not changing.
        wasMatchingTag = False
        cursor.execute(tagQuery, (factoidArray[n],))
        tagID = cursor.fetchall()

        if tagID in tagArray:
            score = 0
            for m in range(len(tagArray)):
                if tagID == tagArray[m]:
                    score += 1
            wasMatchingTag = True
        else:
            tagArray.append(tagID)

        if wasMatchingTag == False:
            score -= 1

    return score

def mutate(cursor, factoidArray, mainQuery, category, categoryNumber):
    candidate = factoidArray.copy()
    selectedIndexToMutate = random.randint(0,4)
    #selectedIndex should work for the difficulty considering the numbers in the index should match the difficulty?
    candidate[selectedIndexToMutate] = randomFactoidState(cursor, mainQuery, category, categoryNumber, selectedIndexToMutate)    

    return candidate

main()