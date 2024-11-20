from matching.models import MatchingQueue

class MatchingMixin:
    def get_meal_waiting_status(self, data):
        meal_queues = MatchingQueue.objects.all().filter(name__in=['student_center', 'myeongjin', 'staff_cafeteria', 'welfare'])
        restaurant_list = ['student_center', 'myeongjin', 'staff_cafeteria', 'welfare']
        response_data = []

        if meal_queues.exists():
            added_restaurant = set()
            
            for meal_queue in meal_queues:
                current_user_count = meal_queue.users.count()
                response_data.append({
                    "name": meal_queue.name,
                    "current_user_count": current_user_count,
                })
                
                added_restaurant.add(meal_queue.name)
            
            for restaurant in restaurant_list:
                if restaurant not in added_restaurant:
                    response_data.append({
                        "name": restaurant,
                        "current_user_count": 0,
                    })
        else:
            for restaurant in restaurant_list:
                response_data.append({
                    "name": restaurant,
                    "current_user_count": 0,
                })
        
        return response_data
    
    def get_taxi_waiting_status(self, data):
        taxi_queues = MatchingQueue.objects.all().filter(name__in=['mju_to_station', 'station_to_mju'])
        route_list = ['mju_to_station', 'station_to_mju']
        response_data = []
        
        if taxi_queues.exists():
            added_route = set()
            
            for taxi_queue in taxi_queues:
                current_user_count = taxi_queue.users.count()
                response_data.append({
                    "name": taxi_queue.name,
                    "current_user_count": current_user_count,
                })
                
                added_route.add(taxi_queue.name)
            
            for route in route_list:
                if route not in added_route:
                    response_data.append({
                        "name": route,
                        "current_user_count": 0,
                    })
                    
        else:
            for route in route_list:
                response_data.append({
                    "name": route,
                    "current_user_count": 0,
                })
        
        return response_data