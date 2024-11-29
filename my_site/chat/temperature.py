from asgiref.sync import sync_to_async
from my_app.models import CustomUser

@sync_to_async
def get_user_by_usernumber(usernumber):
    try:
        return CustomUser.objects.get(student_number=usernumber)
    except CustomUser.DoesNotExist:
        return None

def change_user_temperature(user, action):
    if action == "up":
        user.temperature += 3
        
        if user.temperature > 99.9:
            user.temperature = 99.9
    elif action == "down":
        user.temperature -= 3
        
        if user.temperature < 0:
            user.temperature = 0
    else:
        print(f"{user.username}의 온도를 변경할 수 없습니다.")
    
    user.save()

@sync_to_async
def add_temperature_change(chat_room, evaluator, evaluatee, action):
    #evaluator : 온도를 평가한 사용자 학번
    #evaluatee : 온도를 평가 받는 사용자 학번
    if str(evaluator) == str(evaluatee):
        print("자신에게 온도를 평가할 수 없습니다.")
        return
    
    change_data = {
        "evaluator": evaluator,
        "evaluatee": evaluatee,
        "action": action
    }
    
    for data in chat_room.temperature_change_list:
        if data['evaluator'] == evaluator and data['evaluatee'] == evaluatee:
            if data['action'] == action:
                print(f"{evaluator}가 이미 {evaluatee}에게 온도를 평가했습니다.")
            else:
                data['action'] = action
                chat_room.save()
                
            return
    else:
        chat_room.temperature_change_list.append(change_data)
        chat_room.save()

#채팅방 삭제시 작동
def apply_temperature_changes(chat_room):
    for change in chat_room.temperature_change_list:
        evaluatee = change["evaluatee"]
        action = change["action"]
        
        try:
            targetUser = CustomUser.objects.get(student_number=evaluatee)
        except CustomUser.DoesNotExist:
            print(f"사용자 {evaluatee}를 찾을 수 없습니다.")
            continue    
        
        change_user_temperature(targetUser, action)