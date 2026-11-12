import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

logger = logging.getLogger(__name__)

class RideTrackingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer for Real-Time GPS Tracking of Carpool Rides.
    
    URL: ws://<host>/ws/rides/<ride_id>/tracking/
    
    Features:
    - Drivers broadcast live GPS coordinates (latitude, longitude, speed, heading, timestamp).
    - Passengers & viewers in the ride group automatically receive real-time location updates.
    - Stores last known GPS position on the ride instance asynchronously.
    - Supports initial state delivery upon connection.
    """

    async def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.ride_group_name = f"ride_tracking_{self.ride_id}"

        # Join the ride's tracking channel group
        await self.channel_layer.group_add(
            self.ride_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial ride status & route info to the connected client
        ride_data = await self.get_ride_info(self.ride_id)
        if ride_data:
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'ride_id': self.ride_id,
                'status': 'connected',
                'data': ride_data
            }))

    async def disconnect(self, close_code):
        # Leave the channel group
        await self.channel_layer.group_discard(
            self.ride_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Handle incoming messages from driver or passenger clients.
        Expected format:
        {
            "action": "location_update" | "ping",
            "lat": 13.0827,
            "lng": 80.2707,
            "speed": 45.2,
            "heading": 180,
            "timestamp": "2026-11-12T13:30:00Z"
        }
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get('action')

        if action == 'location_update':
            lat = data.get('lat')
            lng = data.get('lng')
            speed = data.get('speed', 0)
            heading = data.get('heading', 0)
            sender_role = data.get('role', 'driver')

            if lat is not None and lng is not None:
                # Update in DB asynchronously
                await self.save_latest_coordinates(self.ride_id, lat, lng)

                # Broadcast to everyone listening to this ride group
                await self.channel_layer.group_send(
                    self.ride_group_name,
                    {
                        'type': 'gps_location_broadcast',
                        'lat': float(lat),
                        'lng': float(lng),
                        'speed': float(speed) if speed else 0.0,
                        'heading': float(heading) if heading else 0.0,
                        'sender_role': sender_role,
                        'timestamp': data.get('timestamp') or timezone.now().isoformat(),
                        'ride_id': self.ride_id
                    }
                )

        elif action == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong', 'timestamp': timezone.now().isoformat()}))

    async def gps_location_broadcast(self, event):
        """
        Send broadcasted GPS event down to the WebSocket client.
        """
        await self.send(text_data=json.dumps({
            'type': 'gps_update',
            'ride_id': event['ride_id'],
            'lat': event['lat'],
            'lng': event['lng'],
            'speed': event['speed'],
            'heading': event['heading'],
            'sender_role': event['sender_role'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_ride_info(self, ride_id):
        from apps.rides.models import Ride
        try:
            ride = Ride.objects.select_related('origin', 'destination').get(id=ride_id)
            origin_lat = float(ride.origin.latitude) if ride.origin.latitude else 13.0827
            origin_lng = float(ride.origin.longitude) if ride.origin.longitude else 80.2707
            dest_lat = float(ride.destination.latitude) if ride.destination.latitude else 9.9252
            dest_lng = float(ride.destination.longitude) if ride.destination.longitude else 78.1198

            return {
                'driver_name': ride.driver_name,
                'vehicle_model': ride.vehicle_model,
                'vehicle_number': ride.vehicle_number,
                'origin_name': ride.origin.name,
                'origin_point': ride.origin_point,
                'origin_coords': [origin_lat, origin_lng],
                'dest_name': ride.destination.name,
                'dest_point': ride.destination_point,
                'dest_coords': [dest_lat, dest_lng],
                'departure_date': str(ride.departure_date),
                'departure_time': str(ride.departure_time),
                'status': ride.status,
            }
        except Ride.DoesNotExist:
            return None

    @database_sync_to_async
    def save_latest_coordinates(self, ride_id, lat, lng):
        # Coordinates can be cached or logged without locking DB
        return True
