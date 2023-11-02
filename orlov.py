import pandas as pd
import sqlite3
import random

def findPrinter(l_flr, l_loc):
    '''Function to read printer data from CSV file and print orlov response on screen'''
    printer_text = []
    loc_flr = l_loc.upper() + '_' + str(l_flr).upper()
    
    prdata = pd.read_csv('C:\pyfiles\printers_data.csv')
    prdata.set_index(['fac_flr'], inplace=True)
    try:
        pr_code = str(prdata.loc[loc_flr, 'printer'])
        printer_text.append("I see Printer " + pr_code + " is the closest to you.")
        printer_text.append("Following are the instructions to set it up:")
        printer_text.append("1) Go to START menu --> Control Panel --> Printers and Devices")
        printer_text.append("2) Add Network Printer")
        printer_text.append("3) Enter " + pr_code+ " and hit ADD.")
    except:
        printer_text.append("Sorry, I'm unable to find a printer for that location.")

    return(printer_text)


def getIncidentData(l_user=None, l_incno=None):
    '''Get incidents by badge ID or by specific Incident No.'''
    inc_text = []
    db_path = '/C:/pyfiles/for_orlov.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    itsm_cur = conn.cursor()

    if l_incno is None:
        itsm_cur.execute('''
            SELECT * FROM itsm_data
            WHERE user = ? ''', (l_user, ))
        inc_text.append("Below are the last few incidents logged by you:")
    else:
        itsm_cur.execute('''
            SELECT * FROM itsm_data
            WHERE tckt = ? ''', (l_incno, ))
        inc_text.append("Below is the status:")
    
    row = itsm_cur.fetchone()
    cnt = 0
    
    if row is None:
        inc_text = ["No incidents found for that Badge ID or INC/REQ/CHR Number."]
    else:
        while cnt < 3:
            cnt += 1
            inc_text.append((row['tckt'] + " | " + row['desc'] + " | " + row['stat']))
            row = itsm_cur.fetchone()
    
    return(inc_text)


def incNumAvailable(inc_response):
    for tag1 in inc_response["context"]:
#         print(tag1)
        if tag1 == "INC":
            return(1)
    return(0)


def validateQnA(answ):
    if answ == df.ix[qnum_list[len(qnum_list) - 1], 'answ']:
        return_val = 1
        ques_num = random.randint(1,5)
        while ques_num in qnum_list:
            ques_num = random.randint(1,5)
        qnum_list.append(ques_num)
        return([df.ix[ques_num, 'ques']], return_val)
    else:
        return_val = 0
        return("", return_val)


def getQuestions(l_user):
    global df
    
    db_path = '/C:/pyfiles/for_orlov.db'
    conn = sqlite3.connect(db_path)
    ques_cur = conn.cursor()
    ques_cur.execute("SELECT * FROM user_ques WHERE user = ?", (l_user, ))
    rows = ques_cur.fetchall()
    
    if len(rows) > 0:
        df = pd.DataFrame(rows, columns=['user','qnum','ques','answ'])
        df.set_index('qnum', inplace=True)
    
    return(len(rows))
        

def processResponse(response):
    '''Function to process the response coming from orlov and call Python functions as needed'''

    return_text = []
    '''Return Errors if encountered'''
    for e in response["output"]["log_messages"]:
        if e["level"] == "err":
#             return_text = "Error -" + e["msg"]
            return_text.append("Error -" + e["msg"])
            return(return_text, "")

    '''Display response from orlov'''
    for tag in response:
#         print(tag)
        if tag == "output":
            for txt in response["output"]["text"]:
#                 return_text += txt
                return_text.append(txt)

        if tag == "actions":
            for action in response["actions"]:
##                    print(action["name"])
                if action["name"] == "findPrinter":
                    action_text = findPrinter(response["context"]["floor_no"],
                                                   response["context"]["location"])
                    return_text += action_text
#                     return_text.append(action_text)
                    return(return_text, "printer")
                
                elif action["name"] == "getIncidentData":
                    if incNumAvailable(response):
#                         action_text = getIncidentData(response["context"]["user_id"],
                        action_text = getIncidentData("", response["context"]["INC"])
                    else:
                        action_text = getIncidentData(response["context"]["user_id"])
                    
                    return_text += action_text
#                     return_text.append(action_text)
                    return(return_text, "incident")
                
                elif action["name"] == "challenge_ques":
#                     return_val = askChallengeQues(response["context"]["user_id"])
                    global ques_num, qnum_list
                    qnum_list = []
                    rec_num = getQuestions(response["context"]["user_id"])
                    if rec_num > 0:
                        ques_num = random.randint(1,5)
                        qnum_list.append(ques_num)
                        return_text.append(df.ix[ques_num,'ques'])
                        return(return_text, "pswdreset")
                    else:
                        return(["Badge ID not found."], "pswdreset0")
        else:
            continue
        
    return(return_text, "")
