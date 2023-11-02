from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from orlov_developer_cloud import AssistantV1
import orlov
import json, random

app = Flask(__name__)
sio = SocketIO(app, asyc_mode='eventlet')
thread=None

assistant = AssistantV1(username = 'username',
                           password = 'password',
                           version = '2018-02-16')
workspace_id = '49dee8c1-cd3d-43f7-9914-33cbdaace889'
context = {}
local_process = 0
q_count = 0

response = assistant.message(workspace_id=workspace_id)
context = response["context"]


@app.route('/', methods = ['GET'])
def index():
    return render_template('index.html', async_mode=sio.async_mode)


@sio.on('connect')
def socket_connect():
    print("User connected...")
    emit('my_response', {'data': 'Connected', 'count': 0})

  
@sio.on('message')
def handleMessage(msg):
    print("Received Message:", msg)
    sio.emit('message', "USER: "+msg)
#     sio.emit('message', "orlov: "+msg+msg)
#     from_human_message = str(msg["data"])
    from_human_message = msg
    global context, local_process, action_flag, q_count
  
    bot_response = []
#     try:
#         response = assistant.message(workspace_id=workspace_id, input={'text': urllib.parse.unquote(from_human_message)}, context=context)
    if not local_process:
#         print(json.dumps(response, indent=2))
        try:
            response = assistant.message(workspace_id=workspace_id, input={'text': from_human_message}, context=context)
            context = response["context"]
            try:
                processed_response, action_flag = orlov.processResponse(response)
                bot_response += processed_response
                
                if action_flag == 'pswdreset0':
                    try:
                        response = assistant.message(workspace_id=workspace_id, input={'text': ""}, context=context)
                        context = response["context"]
                        try:
                            processed_response, temp = orlov.processResponse(response)
                            print("BOT ", bot_response)
                            print("PROC ", processed_response)
                            bot_response += processed_response
                        except Exception as ex:
                            bot_response.append("Sorry 5. I'm unable to process that response. Please try again later.")
                            print("Exception Error: ", ex)
                    except Exception as ex:
                        bot_response.append("We're having trouble talking to orlov at the moment. Please try again later")
                        print("Exception Error: ", ex)
            except Exception as ex:
                bot_response.append("Sorry 1. I'm unable to process that response. Please try again later.")
                print("Exception Error: ", ex)
        except Exception as ex:
            bot_response.append("We're having trouble talking to orlov at the moment. Please try again later")
            print("Exception Error: ", ex)
    else:
        if action_flag == 'pswdreset':
            q_count += 1
            next_ques, valid = orlov.validateQnA(from_human_message)
            
            if valid and q_count <= 1:
                bot_response += next_ques
            else:
                if valid:
                    bot_response.append("Your password has been reset. Please check your registered personal email for next steps.")
                else:
                    bot_response.append("Your answer did not match. Please try again later.")

                local_process = 0
                q_count = 0

                try:
                    response = assistant.message(workspace_id=workspace_id, input={'text': ""}, context=context)
                    context = response["context"]
                    try:
                        processed_response, action_flag = orlov.processResponse(response)
                        bot_response += processed_response
                    except Exception as ex:
                        bot_response.append("Sorry 2. I'm unable to process that response. Please try again later.")
                        print("Exception Error: ", ex)
                except Exception as ex:
                    bot_response.append("We're having trouble talking to orlov at the moment. Please try again later")
                    print("Exception Error: ", ex)
                    
    print(bot_response)
    bot_response[0] = "orlov: " + bot_response[0]
    cnt = 0
    for text in bot_response:
        if cnt != 0:
            text = ". . . . . . . . ." + text
            
        sio.emit('message', text)
        cnt += 1
    
    if action_flag == "incident" or action_flag == "printer":
        try:
            response = assistant.message(workspace_id=workspace_id, input={'text': ""}, context=context)
            context = response["context"]
            try:
                processed_response, action_flag = orlov.processResponse(response)
                bot_response = processed_response
            except Exception as ex:
                bot_response.append("Sorry 4. I'm unable to process that response. Please try again later.")
                print("Exception Error: ", ex)
        except Exception as ex:
            bot_response.append("We're having trouble talking to orlov at the moment. Please try again later")
            print("Exception Error: ", ex)
  
#         sio.emit('message', "orlov: " + bot_response)
        print(bot_response)
        bot_response[0] = "orlov: " + bot_response[0]
        cnt = 0
        for text in bot_response:
            if cnt != 0:
                text = ". . . . . . . . ." + text
                
            sio.emit('message', text)
            cnt += 1
    elif action_flag == "pswdreset":
        local_process = 1


@sio.on('disconnect')
def socket_disconnect():
    global context
    context = {}
    print('User disconnected...')
#     print('Client disconnected', sid)


if __name__ == '__main__':
    sio.run(app, debug=True)
