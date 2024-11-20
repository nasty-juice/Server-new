from matching.models import MatchingQueue

class MatchingMixin:
    def get_waiting_status_data(self):
        queues = MatchingQueue.objects.all()
        response_data = []
        
        if queues.count() == 0:
            response_data.append({
                "name": "No queue",
                "current_user_count": 0,
            })
            return response_data
        else:
            for queue in queues:
                current_user_count = queue.users.count()
                response_data.append({
                    "name": queue.name,
                    "current_user_count": current_user_count,

                })

        return response_data
    
    def get_meal_waiting_status(self, data):
        response_data = [item for item in data if item['name'] in ['명진당','학관','교직원식당']]

        return response_data
    
    def get_taxi_waiting_status(self, data):
        response_data = [item for item in data if item['name'] in ['station_to_mju', 'mju_to_station']]

        return response_data
    