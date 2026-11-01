import sqlite3
import random
import math
from pathlib import Path
import json


def main(): 
    T = random.randint(0, 100) #Determines how many times it'll be reduced
                            #Will need to edit range most likely.
                            #depending on how many factoids per.
    #outputForOz = dict()
    outputForOz = [] #List instead? Dictionary overwrites.
    numCategories = 6
    numAnswersPerCategory = 5
    category = [-1, -1, -1, -1, -1, -1]
    categoryOptions = [] #This is a different way to store categories. They aren't normalized so I had to normalize them essentially




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
        for i in range(numCategories): #This should run times equivalent to how many categories, 
                                        #running through the simulated annealing process on each group
                                        #of factoids.
            for m in range(numAnswersPerCategory):    
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
                print("Is it taking longer after or before this?")
                cursor.execute(getFactoidInfoQuery, (factoidID,))
                answer = cursor.fetchone()
                if answer is not None:
                    outputForOz.append({"factoidID": answer[0], #This naming scheme is exceptionally confusing. Gl OZ
                                    "Answer": answer[3],  #Jeopardy will say this one
                                    "Question": answer[2] #The user will say this one
                                    })
                print(f"What is happening? n {i} and m {m}")
        categoryQuery = ("Select title from categories where id = ?")
        print("Categories")
        for i in range(len(category)):
            cursor.execute(categoryQuery, (category[i],))
            print(cursor.fetchone())
        print("Here's the final output homeslice")
        print(outputForOz)

    except sqlite3.Error as error:
        print(f"Your sql stuff crashed H")
        print(f"here's the error {error}")

    finally:
        if connection is not None:
            connection.close()
            print("Stopped")





def HillClimbingFunction(T, allRows): #This is mostly a placeholder. It just returns a random selection of stuff
    return random.choice(allRows)[0]

main()