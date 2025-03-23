import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Game, Move

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'game_{self.game_id}'
        self.user = self.scope['user']

        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )

        await self.accept()
        print("Connected to game group")
        
        game_state = await self.get_game_state()
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'state': game_state
        }))
        print("Sent game state")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )
        print("Disconnected from game group")

    async def receive(self, text_data):
        print(f"Received from client: {text_data}")
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')
            
            if message_type == 'make_move':
                row = data.get('row')
                col = data.get('col')
                
                if row is None or col is None:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Invalid move: missing row or column'
                    }))
                    return
                
                valid, updated_state = await self.make_move(row, col)
                
                if valid:
                    await self.channel_layer.group_send(
                        self.game_group_name,
                        {
                            'type': 'game_update',
                            'state': updated_state
                        }
                    )
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Invalid move'
                    }))
                    print("Sent error")
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
            print("Sent error")
        except Exception as e:
            print(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Server error: {str(e)}'
            }))
            print("Sent error")

    async def game_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_update',
            'state': event['state']
        }))
        print("Sent game update")

    @database_sync_to_async
    def get_game_state(self):
        try:
            game = Game.objects.get(id=self.game_id)
            print(f"Got game state for game {game.id}")
            return {
                'board': game.board,
                'current_player': game.current_player,
                'status': game.status,
                'winner': game.winner,
                'player_x': game.player_x.username if game.player_x else None,
                'player_o': game.player_o.username if game.player_o else None,
            }
        except Game.DoesNotExist:
            return None

    # Add this to your existing GameConsumer class

    @database_sync_to_async
    def make_move(self, row, col):
        try:
            print(f"Making move for game {self.game_id}")
            game = Game.objects.get(id=self.game_id)
            
            if (game.current_player == 'X' and game.player_x != self.user) or \
            (game.current_player == 'O' and game.player_o != self.user):
                return False, None
            
            if game.status != 'active':
                return False, None
            
            board = json.loads(game.board)
            if board[row][col] != '':
                return False, None
            
            board[row][col] = game.current_player
            
            winner = self.check_winner(board)
            is_draw = self.is_board_full(board)
            
            # Store old status to check if it's changed
            old_status = game.status
            symbol = game.current_player
            if winner:
                game.status = 'completed'
                game.winner = winner
            elif is_draw:
                game.status = 'draw'
            else:
                game.current_player = 'O' if game.current_player == 'X' else 'X'
            
            game.board = json.dumps(board)
            game.save()
            
            Move.objects.create(
                game=game,
                player=self.user,
                row=row,
                col=col,
                symbol=symbol
            )
            print("Saved move")
            
            if old_status != game.status:
                self.notify_game_list(game)
            
            return True, self.get_game_state_sync(game)
            
        except Game.DoesNotExist:
            return False, None
        except Exception as e:
            print(f"Error in make_move: {str(e)}")
            return False, None

    def notify_game_list(self, game):
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        
        game_data = {
            'id': game.id,
            'status': game.status,
            'current_player': game.current_player,
            'player_x': game.player_x.username if game.player_x else None,
            'player_o': game.player_o.username if game.player_o else None,
        }
        
        async_to_sync(channel_layer.group_send)(
            'game_list',
            {
                'type': 'game_list_update',
                'action': 'update',
                'game': game_data
            }
        )
        print(f"Notified game list about game {game.id} update")
        
    def get_game_state_sync(self, game):
        return {
            'board': game.board,
            'current_player': game.current_player,
            'status': game.status,
            'winner': game.winner,
            'player_x': game.player_x.username if game.player_x else None,
            'player_o': game.player_o.username if game.player_o else None,
        }

    def check_winner(self, board):
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] != '':
                return board[i][0]
            
            if board[0][i] == board[1][i] == board[2][i] != '':
                return board[0][i]
        
        if board[0][0] == board[1][1] == board[2][2] != '':
            return board[0][0]
        
        if board[0][2] == board[1][1] == board[2][0] != '':
            return board[0][2]
        
        return None

    def is_board_full(self, board):
        for row in board:
            if '' in row:
                return False
        return True
    

class GameListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'game_list'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        print("Connected to game list group")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print("Disconnected from game list group")

    async def game_list_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_list_update',
            'action': event['action'],
            'game': event['game']
        }))
        print("Sent game list update")